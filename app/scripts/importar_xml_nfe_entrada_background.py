"""
Script de importação de XMLs de NF-e de ENTRADA em background
"""
import sys
import os
import json
import time
import xml.etree.ElementTree as ET

# Adicionar path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'app'))

from database import get_db


class ImportadorEntradaBackground:
    """
    Importador de NFe de ENTRADA que salva progresso em arquivo JSON
    """
    
    def __init__(self, pasta_xml):
        self.pasta_xml = pasta_xml
        self.db = get_db()
        
        # Arquivo de progresso
        self.progress_file = os.path.join(project_root, 'import_entrada_progress.json')
        
        # Estatísticas
        self.total_arquivos = 0
        self.processados = 0
        self.sucesso = 0
        self.duplicado = 0
        self.erros = 0
    
    def importar(self):
        """Executa importação"""
        inicio = time.time()
        
        # Buscar XMLs
        xml_files = self._buscar_xmls()
        self.total_arquivos = len(xml_files)
        
        # Salvar progresso inicial
        self._salvar_progresso('iniciado')
        
        # Processar cada XML
        for xml_file in xml_files:
            self._processar_xml(xml_file)
            self.processados += 1
            
            # Atualizar progresso a cada 5 arquivos
            if self.processados % 5 == 0:
                self._salvar_progresso('processando')
        
        # Finalizar
        tempo_total = time.time() - inicio
        self._salvar_progresso('concluido', tempo_total)
    
    def _buscar_xmls(self):
        """Busca XMLs recursivamente"""
        xml_files = []
        for root, dirs, files in os.walk(self.pasta_xml):
            for file in files:
                if file.lower().endswith('.xml'):
                    xml_files.append(os.path.join(root, file))
        return sorted(xml_files)
    
    def _processar_xml(self, xml_file):
        """Processa um XML de NFe de ENTRADA"""
        tempo_inicio = time.time()
        
        try:
            # Parse do XML
            dados = self._parse_nfe_entrada(xml_file)
            
            if not dados:
                self._registrar_log(xml_file, 'erro', 'Não foi possível fazer parse do XML', None, tempo_inicio)
                self.erros += 1
                return
            
            # CORREÇÃO: Verificar se chave de acesso existe
            if 'chave_acesso' not in dados or not dados['chave_acesso']:
                self._registrar_log(xml_file, 'erro', 'XML sem chave de acesso válida', None, tempo_inicio)
                self.erros += 1
                return
            
            # Verificar se já existe (por chave de acesso)
            chave_acesso = dados['chave_acesso']
            existe = self.db.fetch_one(
                "SELECT id FROM nfe_entrada_staging_notas WHERE chave_acesso = %s",
                (chave_acesso,)
            )
            
            if existe:
                self._registrar_log(xml_file, 'duplicado', 'NFe já importada', chave_acesso, tempo_inicio)
                self.duplicado += 1
                return
            
            # Inserir na staging
            self._inserir_staging(xml_file, dados)
            
            self._registrar_log(xml_file, 'sucesso', 'NFe importada com sucesso', chave_acesso, tempo_inicio)
            self.sucesso += 1
            
        except Exception as e:
            self._registrar_log(xml_file, 'erro', str(e), None, tempo_inicio)
            self.erros += 1
    
    def _parse_nfe_entrada(self, xml_file):
        """
        Parse básico do XML de NFe de ENTRADA
        """
        try:
            # Ler XML
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Namespace
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            
            # Buscar nfeProc ou NFe
            nfe_proc = root.find('.//nfe:NFe', ns)
            if nfe_proc is None:
                nfe_proc = root.find('.//NFe', ns)
            
            if nfe_proc is None:
                return None
            
            # Buscar infNFe
            inf_nfe = nfe_proc.find('.//nfe:infNFe', ns)
            if inf_nfe is None:
                inf_nfe = nfe_proc.find('.//infNFe')
            
            if inf_nfe is None:
                return None
            
            # Chave de acesso
            chave_acesso = inf_nfe.get('Id', '').replace('NFe', '')
            
            # Identificação
            ide = inf_nfe.find('.//nfe:ide', ns) or inf_nfe.find('.//ide')
            numero_nota = self._get_text(ide, 'nNF', ns)
            serie = self._get_text(ide, 'serie', ns)
            modelo = self._get_text(ide, 'mod', ns)
            tipo_operacao = self._get_text(ide, 'tpNF', ns)
            data_emissao = self._get_text(ide, 'dhEmi', ns)
            data_saida = self._get_text(ide, 'dhSaiEnt', ns)
            natureza_operacao = self._get_text(ide, 'natOp', ns)
            
            # Emitente (FORNECEDOR)
            emit = inf_nfe.find('.//nfe:emit', ns) or inf_nfe.find('.//emit')
            emit_cnpj = self._get_text(emit, 'CNPJ', ns)
            emit_razao_social = self._get_text(emit, 'xNome', ns)
            emit_nome_fantasia = self._get_text(emit, 'xFant', ns)
            emit_ie = self._get_text(emit, 'IE', ns)
            
            # Endereço emitente
            emit_end = emit.find('.//nfe:enderEmit', ns) or emit.find('.//enderEmit')
            emit_logradouro = self._get_text(emit_end, 'xLgr', ns)
            emit_numero = self._get_text(emit_end, 'nro', ns)
            emit_complemento = self._get_text(emit_end, 'xCpl', ns)
            emit_bairro = self._get_text(emit_end, 'xBairro', ns)
            emit_municipio = self._get_text(emit_end, 'xMun', ns)
            emit_uf = self._get_text(emit_end, 'UF', ns)
            emit_cep = self._get_text(emit_end, 'CEP', ns)
            emit_telefone = self._get_text(emit_end, 'fone', ns)
            emit_email = self._get_text(emit, 'email', ns)
            
            # Destinatário (SUA EMPRESA)
            dest = inf_nfe.find('.//nfe:dest', ns) or inf_nfe.find('.//dest')
            dest_cnpj = self._get_text(dest, 'CNPJ', ns)
            dest_razao_social = self._get_text(dest, 'xNome', ns)
            dest_nome_fantasia = self._get_text(dest, 'xFant', ns)
            dest_ie = self._get_text(dest, 'IE', ns)
            
            # Endereço destinatário
            dest_end = dest.find('.//nfe:enderDest', ns) or dest.find('.//enderDest')
            dest_logradouro = self._get_text(dest_end, 'xLgr', ns)
            dest_numero = self._get_text(dest_end, 'nro', ns)
            dest_complemento = self._get_text(dest_end, 'xCpl', ns)
            dest_bairro = self._get_text(dest_end, 'xBairro', ns)
            dest_municipio = self._get_text(dest_end, 'xMun', ns)
            dest_uf = self._get_text(dest_end, 'UF', ns)
            dest_cep = self._get_text(dest_end, 'CEP', ns)
            dest_telefone = self._get_text(dest_end, 'fone', ns)
            
            # Totais
            total = inf_nfe.find('.//nfe:total/nfe:ICMSTot', ns) or inf_nfe.find('.//total/ICMSTot')
            total_produtos = self._get_decimal(total, 'vProd', ns)
            total_desconto = self._get_decimal(total, 'vDesc', ns)
            total_frete = self._get_decimal(total, 'vFrete', ns)
            total_seguro = self._get_decimal(total, 'vSeg', ns)
            total_outras_despesas = self._get_decimal(total, 'vOutro', ns)
            total_ipi = self._get_decimal(total, 'vIPI', ns)
            total_icms = self._get_decimal(total, 'vICMS', ns)
            total_icms_st = self._get_decimal(total, 'vST', ns)
            total_pis = self._get_decimal(total, 'vPIS', ns)
            total_cofins = self._get_decimal(total, 'vCOFINS', ns)
            total_nota = self._get_decimal(total, 'vNF', ns)
            
            # Informações complementares
            inf_adic = inf_nfe.find('.//nfe:infAdic', ns) or inf_nfe.find('.//infAdic')
            informacoes_complementares = self._get_text(inf_adic, 'infCpl', ns) if inf_adic is not None else None
            
            # Itens
            itens = []
            for det in inf_nfe.findall('.//nfe:det', ns) or inf_nfe.findall('.//det'):
                item = self._parse_item(det, ns)
                if item:
                    itens.append(item)
            
            # Ler XML original
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_original = f.read()
            
            return {
                'chave_acesso': chave_acesso,
                'numero_nota': numero_nota,
                'serie': serie,
                'modelo': modelo,
                'tipo_operacao': tipo_operacao,
                'data_emissao': data_emissao,
                'data_entrada': data_saida,
                'emit_cnpj': emit_cnpj,
                'emit_razao_social': emit_razao_social,
                'emit_nome_fantasia': emit_nome_fantasia,
                'emit_ie': emit_ie,
                'emit_logradouro': emit_logradouro,
                'emit_numero': emit_numero,
                'emit_complemento': emit_complemento,
                'emit_bairro': emit_bairro,
                'emit_municipio': emit_municipio,
                'emit_uf': emit_uf,
                'emit_cep': emit_cep,
                'emit_telefone': emit_telefone,
                'emit_email': emit_email,
                'dest_cnpj': dest_cnpj,
                'dest_razao_social': dest_razao_social,
                'dest_nome_fantasia': dest_nome_fantasia,
                'dest_ie': dest_ie,
                'dest_logradouro': dest_logradouro,
                'dest_numero': dest_numero,
                'dest_complemento': dest_complemento,
                'dest_bairro': dest_bairro,
                'dest_municipio': dest_municipio,
                'dest_uf': dest_uf,
                'dest_cep': dest_cep,
                'dest_telefone': dest_telefone,
                'total_produtos': total_produtos,
                'total_desconto': total_desconto,
                'total_frete': total_frete,
                'total_seguro': total_seguro,
                'total_outras_despesas': total_outras_despesas,
                'total_ipi': total_ipi,
                'total_icms': total_icms,
                'total_icms_st': total_icms_st,
                'total_pis': total_pis,
                'total_cofins': total_cofins,
                'total_nota': total_nota,
                'informacoes_complementares': informacoes_complementares,
                'natureza_operacao': natureza_operacao,
                'xml_original': xml_original,
                'itens': itens
            }
            
        except Exception as e:
            print(f"Erro ao fazer parse do XML {xml_file}: {e}")
            return None
    
    def _parse_item(self, det, ns):
        """Parse de um item da NFe"""
        try:
            numero_item = det.get('nItem')
            
            prod = det.find('.//nfe:prod', ns) or det.find('.//prod')
            if prod is None:
                return None
            
            codigo_produto = self._get_text(prod, 'cProd', ns)
            codigo_ean = self._get_text(prod, 'cEAN', ns)
            codigo_ean_trib = self._get_text(prod, 'cEANTrib', ns)
            descricao = self._get_text(prod, 'xProd', ns)
            ncm = self._get_text(prod, 'NCM', ns)
            cest = self._get_text(prod, 'CEST', ns)
            cfop = self._get_text(prod, 'CFOP', ns)
            unidade_comercial = self._get_text(prod, 'uCom', ns)
            unidade_tributavel = self._get_text(prod, 'uTrib', ns)
            quantidade_comercial = self._get_decimal(prod, 'qCom', ns)
            valor_unitario_comercial = self._get_decimal(prod, 'vUnCom', ns)
            quantidade_tributavel = self._get_decimal(prod, 'qTrib', ns)
            valor_unitario_tributavel = self._get_decimal(prod, 'vUnTrib', ns)
            valor_total_bruto = self._get_decimal(prod, 'vProd', ns)
            valor_desconto = self._get_decimal(prod, 'vDesc', ns)
            valor_frete = self._get_decimal(prod, 'vFrete', ns)
            valor_seguro = self._get_decimal(prod, 'vSeg', ns)
            valor_outras_despesas = self._get_decimal(prod, 'vOutro', ns)
            
            # Calcular valor total do produto
            valor_total_produto = valor_total_bruto
            if valor_desconto:
                valor_total_produto -= valor_desconto
            if valor_frete:
                valor_total_produto += valor_frete
            if valor_seguro:
                valor_total_produto += valor_seguro
            if valor_outras_despesas:
                valor_total_produto += valor_outras_despesas
            
            return {
                'numero_item': numero_item,
                'codigo_produto': codigo_produto,
                'codigo_ean': codigo_ean,
                'codigo_ean_tributavel': codigo_ean_trib,
                'descricao': descricao,
                'ncm': ncm,
                'cest': cest,
                'cfop': cfop,
                'unidade_comercial': unidade_comercial,
                'unidade_tributavel': unidade_tributavel,
                'quantidade_comercial': quantidade_comercial,
                'valor_unitario_comercial': valor_unitario_comercial,
                'quantidade_tributavel': quantidade_tributavel,
                'valor_unitario_tributavel': valor_unitario_tributavel,
                'valor_total_bruto': valor_total_bruto,
                'valor_desconto': valor_desconto,
                'valor_frete': valor_frete,
                'valor_seguro': valor_seguro,
                'valor_outras_despesas': valor_outras_despesas,
                'valor_total_produto': valor_total_produto
            }
            
        except Exception as e:
            print(f"Erro ao fazer parse do item: {e}")
            return None
    
    def _get_text(self, element, tag, ns):
        """Obtém texto de um elemento"""
        if element is None:
            return None
        
        # Tentar com namespace
        el = element.find(f'.//nfe:{tag}', ns)
        if el is None:
            # Tentar sem namespace
            el = element.find(f'.//{tag}')
        
        return el.text if el is not None else None
    
    def _get_decimal(self, element, tag, ns):
        """Obtém valor decimal de um elemento"""
        text = self._get_text(element, tag, ns)
        if text:
            try:
                return float(text)
            except:
                return None
        return None
    
    def _inserir_staging(self, xml_file, dados):
        """Insere dados na tabela staging"""
        # Inserir nota
        nota_id = self.db.execute("""
            INSERT INTO nfe_entrada_staging_notas (
                chave_acesso, numero_nota, serie, modelo, tipo_operacao,
                data_emissao, data_entrada,
                emit_cnpj, emit_razao_social, emit_nome_fantasia, emit_ie,
                emit_logradouro, emit_numero, emit_complemento, emit_bairro,
                emit_municipio, emit_uf, emit_cep, emit_telefone, emit_email,
                dest_cnpj, dest_razao_social, dest_nome_fantasia, dest_ie,
                dest_logradouro, dest_numero, dest_complemento, dest_bairro,
                dest_municipio, dest_uf, dest_cep, dest_telefone,
                total_produtos, total_desconto, total_frete, total_seguro,
                total_outras_despesas, total_ipi, total_icms, total_icms_st,
                total_pis, total_cofins, total_nota,
                informacoes_complementares, natureza_operacao,
                arquivo_xml, xml_original, status_importacao
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s
            )
        """, (
            dados['chave_acesso'], dados['numero_nota'], dados['serie'], dados['modelo'], dados['tipo_operacao'],
            dados['data_emissao'], dados['data_entrada'],
            dados['emit_cnpj'], dados['emit_razao_social'], dados['emit_nome_fantasia'], dados['emit_ie'],
            dados['emit_logradouro'], dados['emit_numero'], dados['emit_complemento'], dados['emit_bairro'],
            dados['emit_municipio'], dados['emit_uf'], dados['emit_cep'], dados['emit_telefone'], dados['emit_email'],
            dados['dest_cnpj'], dados['dest_razao_social'], dados['dest_nome_fantasia'], dados['dest_ie'],
            dados['dest_logradouro'], dados['dest_numero'], dados['dest_complemento'], dados['dest_bairro'],
            dados['dest_municipio'], dados['dest_uf'], dados['dest_cep'], dados['dest_telefone'],
            dados['total_produtos'], dados['total_desconto'], dados['total_frete'], dados['total_seguro'],
            dados['total_outras_despesas'], dados['total_ipi'], dados['total_icms'], dados['total_icms_st'],
            dados['total_pis'], dados['total_cofins'], dados['total_nota'],
            dados['informacoes_complementares'], dados['natureza_operacao'],
            os.path.basename(xml_file), dados['xml_original'], 'pendente'
        ))
        
        # Inserir itens
        for item in dados['itens']:
            self.db.execute("""
                INSERT INTO nfe_entrada_staging_itens (
                    nfe_entrada_staging_nota_id, numero_item,
                    codigo_produto, codigo_ean, codigo_ean_tributavel, descricao,
                    ncm, cest, cfop, unidade_comercial, unidade_tributavel,
                    quantidade_comercial, valor_unitario_comercial,
                    quantidade_tributavel, valor_unitario_tributavel,
                    valor_total_bruto, valor_desconto, valor_frete, valor_seguro,
                    valor_outras_despesas, valor_total_produto
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                )
            """, (
                nota_id, item['numero_item'],
                item['codigo_produto'], item['codigo_ean'], item['codigo_ean_tributavel'], item['descricao'],
                item['ncm'], item['cest'], item['cfop'], item['unidade_comercial'], item['unidade_tributavel'],
                item['quantidade_comercial'], item['valor_unitario_comercial'],
                item['quantidade_tributavel'], item['valor_unitario_tributavel'],
                item['valor_total_bruto'], item['valor_desconto'], item['valor_frete'], item['valor_seguro'],
                item['valor_outras_despesas'], item['valor_total_produto']
            ))
    
    def _registrar_log(self, xml_file, status, mensagem, chave_acesso, tempo_inicio):
        """Registra log da importação"""
        tempo_processamento = int((time.time() - tempo_inicio) * 1000)
        
        # Extrair informações do fornecedor se possível
        fornecedor_cnpj = None
        fornecedor_nome = None
        numero_nota = None
        
        if chave_acesso:
            nota = self.db.fetch_one(
                "SELECT emit_cnpj, emit_razao_social, numero_nota FROM nfe_entrada_staging_notas WHERE chave_acesso = %s",
                (chave_acesso,)
            )
            if nota:
                fornecedor_cnpj = nota['emit_cnpj']
                fornecedor_nome = nota['emit_razao_social']
                numero_nota = nota['numero_nota']
        
        self.db.execute("""
            INSERT INTO nfe_entrada_import_log (
                arquivo_xml, caminho_completo, status, mensagem,
                chave_acesso, numero_nota, fornecedor_cnpj, fornecedor_nome,
                tempo_processamento
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            os.path.basename(xml_file), xml_file, status, mensagem,
            chave_acesso, numero_nota, fornecedor_cnpj, fornecedor_nome,
            tempo_processamento
        ))
    
    def _salvar_progresso(self, status, tempo_total=None):
        """Salva progresso em arquivo JSON"""
        progresso = {
            'status': status,
            'total_arquivos': self.total_arquivos,
            'total_processados': self.processados,
            'sucesso': self.sucesso,
            'duplicados': self.duplicado,
            'erros': self.erros,
            'percentual': int((self.processados / self.total_arquivos * 100)) if self.total_arquivos > 0 else 0
        }
        
        if tempo_total:
            progresso['tempo_total'] = int(tempo_total)
        
        with open(self.progress_file, 'w') as f:
            json.dump(progresso, f)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python importar_xml_nfe_entrada_background.py <pasta_xml>")
        sys.exit(1)
    
    pasta_xml = sys.argv[1]
    
    importador = ImportadorEntradaBackground(pasta_xml)
    importador.importar()
    
    print(f"Importação concluída: {importador.sucesso} sucesso, {importador.duplicado} duplicados, {importador.erros} erros")
