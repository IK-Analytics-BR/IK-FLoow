"""
Script para importar XMLs de NF-e para tabelas staging
Percorre pasta de XMLs e insere dados nas tabelas temporárias
"""
import sys
import os
import time
from pathlib import Path

# Adicionar path para importar módulos
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'app'))

from database import get_db
from utils.nfe_xml_parser import parse_nfe_xml


class ImportadorXMLNFe:
    """
    Importador de XMLs de NF-e
    """
    
    def __init__(self, pasta_xml):
        """
        Inicializa importador
        
        Args:
            pasta_xml (str): Caminho da pasta com XMLs
        """
        self.pasta_xml = pasta_xml
        self.db = get_db()
        
        # Estatísticas
        self.total_arquivos = 0
        self.total_sucesso = 0
        self.total_erro = 0
        self.total_duplicado = 0
    
    def importar_todos(self):
        """
        Importa todos os XMLs da pasta e subpastas
        """
        print("=" * 80)
        print("📥 IMPORTAÇÃO DE XMLs DE NF-e PARA STAGING")
        print("=" * 80)
        print(f"\n📁 Pasta: {self.pasta_xml}")
        
        # Verificar se pasta existe
        if not os.path.exists(self.pasta_xml):
            print(f"\n❌ ERRO: Pasta não encontrada: {self.pasta_xml}")
            return
        
        # Buscar todos os XMLs
        print(f"\n🔍 Buscando arquivos XML...")
        xml_files = self._buscar_xmls()
        
        if not xml_files:
            print(f"\n⚠️  Nenhum arquivo XML encontrado em: {self.pasta_xml}")
            return
        
        self.total_arquivos = len(xml_files)
        print(f"✅ Encontrados {self.total_arquivos} arquivo(s) XML")
        
        # Confirmar importação
        resposta = input(f"\n❓ Deseja importar {self.total_arquivos} arquivo(s)? (s/n): ")
        if resposta.lower() != 's':
            print("\n❌ Importação cancelada pelo usuário.")
            return
        
        # Importar cada XML
        print(f"\n" + "=" * 80)
        print("📦 IMPORTANDO XMLs...")
        print("=" * 80)
        
        inicio = time.time()
        
        for i, xml_file in enumerate(xml_files, 1):
            print(f"\n[{i}/{self.total_arquivos}] {os.path.basename(xml_file)}")
            self._importar_xml(xml_file)
        
        tempo_total = time.time() - inicio
        
        # Resumo
        self._exibir_resumo(tempo_total)
    
    def _buscar_xmls(self):
        """
        Busca todos os arquivos XML na pasta e subpastas
        
        Returns:
            list: Lista de caminhos de arquivos XML
        """
        xml_files = []
        pastas_encontradas = set()
        
        # Percorrer pasta recursivamente
        for root, dirs, files in os.walk(self.pasta_xml):
            pastas_encontradas.add(root)
            for file in files:
                if file.lower().endswith('.xml'):
                    xml_path = os.path.join(root, file)
                    xml_files.append(xml_path)
        
        # Mostrar subpastas encontradas
        if len(pastas_encontradas) > 1:
            print(f"   📂 Encontradas {len(pastas_encontradas)} pasta(s) (incluindo subpastas)")
            for pasta in sorted(pastas_encontradas):
                qtd_xml = len([f for f in xml_files if f.startswith(pasta)])
                if qtd_xml > 0:
                    print(f"      • {os.path.relpath(pasta, self.pasta_xml)}: {qtd_xml} XML(s)")
        
        return sorted(xml_files)
    
    def _importar_xml(self, xml_file):
        """
        Importa um arquivo XML para staging
        
        Args:
            xml_file (str): Caminho do arquivo XML
        """
        inicio = time.time()
        
        try:
            # 1. Parse do XML
            print(f"   📄 Fazendo parse do XML...")
            dados = parse_nfe_xml(xml_file)
            
            nota = dados['nota']
            itens = dados['itens']
            xml_original = dados['xml_original']
            
            chave_acesso = nota['chave_acesso']
            numero_nota = nota['numero_nota']
            
            # Validar chave de acesso
            if not chave_acesso or len(chave_acesso) != 44:
                raise Exception(f"Chave de acesso inválida: {chave_acesso}")
            
            # 2. Verificar duplicação
            print(f"   🔍 Verificando duplicação...")
            nota_existente = self.db.fetch_one("""
                SELECT id FROM nfe_staging_notas WHERE chave_acesso = %s
            """, [chave_acesso])
            
            if nota_existente:
                print(f"   ⚠️  Nota já importada (chave: {chave_acesso[:20]}...)")
                self._registrar_log(xml_file, 'duplicado', 
                                   f"Nota {numero_nota} já importada anteriormente",
                                   chave_acesso, numero_nota, None, int((time.time() - inicio) * 1000))
                self.total_duplicado += 1
                return
            
            # 3. Inserir cabeçalho da nota
            print(f"   💾 Inserindo cabeçalho da nota...")
            nota_id = self._inserir_nota(nota, xml_file, xml_original)
            
            # 4. Inserir itens
            print(f"   📦 Inserindo {len(itens)} item(ns)...")
            self._inserir_itens(nota_id, itens)
            
            # 5. Registrar sucesso no log
            tempo_ms = int((time.time() - inicio) * 1000)
            self._registrar_log(xml_file, 'sucesso',
                               f"Nota {numero_nota} importada com {len(itens)} item(ns)",
                               chave_acesso, numero_nota, nota_id, tempo_ms)
            
            print(f"   ✅ Importado com sucesso! ({tempo_ms}ms)")
            self.total_sucesso += 1
            
        except Exception as e:
            # Erro na importação
            erro_msg = str(e)
            print(f"   ❌ ERRO: {erro_msg}")
            
            tempo_ms = int((time.time() - inicio) * 1000)
            self._registrar_log(xml_file, 'erro', erro_msg, None, None, None, tempo_ms)
            
            self.total_erro += 1
    
    def _inserir_nota(self, nota, xml_file, xml_original):
        """
        Insere cabeçalho da nota em nfe_staging_notas
        
        Args:
            nota (dict): Dados da nota
            xml_file (str): Caminho do arquivo
            xml_original (str): XML completo
            
        Returns:
            int: ID da nota inserida
        """
        query = """
            INSERT INTO nfe_staging_notas (
                chave_acesso, numero_nota, serie, modelo, tipo_operacao,
                data_emissao, data_saida, natureza_operacao,
                emit_cnpj, emit_razao_social, emit_nome_fantasia, emit_ie,
                emit_logradouro, emit_numero, emit_complemento, emit_bairro,
                emit_municipio, emit_uf, emit_cep, emit_telefone,
                dest_cnpj_cpf, dest_razao_social, dest_nome_fantasia, dest_ie,
                dest_logradouro, dest_numero, dest_complemento, dest_bairro,
                dest_municipio, dest_uf, dest_cep, dest_telefone, dest_email,
                total_produtos, total_desconto, total_frete, total_seguro,
                total_outras_despesas, total_ipi, total_icms, total_icms_st,
                total_pis, total_cofins, total_nota,
                informacoes_complementares,
                arquivo_xml, xml_original, status_importacao
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s,
                %s, %s, %s
            )
        """
        
        params = [
            nota['chave_acesso'], nota['numero_nota'], nota['serie'], nota['modelo'], nota['tipo_operacao'],
            nota['data_emissao'], nota['data_saida'], nota['natureza_operacao'],
            nota['emit_cnpj'], nota['emit_razao_social'], nota['emit_nome_fantasia'], nota['emit_ie'],
            nota['emit_logradouro'], nota['emit_numero'], nota['emit_complemento'], nota['emit_bairro'],
            nota['emit_municipio'], nota['emit_uf'], nota['emit_cep'], nota['emit_telefone'],
            nota['dest_cnpj_cpf'], nota['dest_razao_social'], nota['dest_nome_fantasia'], nota['dest_ie'],
            nota['dest_logradouro'], nota['dest_numero'], nota['dest_complemento'], nota['dest_bairro'],
            nota['dest_municipio'], nota['dest_uf'], nota['dest_cep'], nota['dest_telefone'], nota['dest_email'],
            nota['total_produtos'], nota['total_desconto'], nota['total_frete'], nota['total_seguro'],
            nota['total_outras_despesas'], nota['total_ipi'], nota['total_icms'], nota['total_icms_st'],
            nota['total_pis'], nota['total_cofins'], nota['total_nota'],
            nota['informacoes_complementares'],
            xml_file, xml_original, 'pendente'
        ]
        
        nota_id = self.db.insert(query, params)
        return nota_id
    
    def _inserir_itens(self, nota_id, itens):
        """
        Insere itens da nota em nfe_staging_itens
        
        Args:
            nota_id (int): ID da nota
            itens (list): Lista de itens
        """
        query = """
            INSERT INTO nfe_staging_itens (
                nfe_staging_nota_id, numero_item,
                codigo_produto, codigo_ean, codigo_ean_tributavel, descricao,
                ncm, cest, cfop, unidade_comercial, unidade_tributavel,
                quantidade_comercial, valor_unitario_comercial,
                quantidade_tributavel, valor_unitario_tributavel,
                valor_total_bruto, valor_desconto, valor_frete, valor_seguro,
                valor_outras_despesas, valor_total_produto,
                icms_origem, icms_cst, icms_base_calculo, icms_aliquota, icms_valor,
                icms_st_base_calculo, icms_st_aliquota, icms_st_valor,
                ipi_cst, ipi_base_calculo, ipi_aliquota, ipi_valor,
                pis_cst, pis_base_calculo, pis_aliquota, pis_valor,
                cofins_cst, cofins_base_calculo, cofins_aliquota, cofins_valor
            ) VALUES (
                %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
        """
        
        for item in itens:
            params = [
                nota_id, item['numero_item'],
                item['codigo_produto'], item['codigo_ean'], item['codigo_ean_tributavel'], item['descricao'],
                item['ncm'], item['cest'], item['cfop'], item['unidade_comercial'], item['unidade_tributavel'],
                item['quantidade_comercial'], item['valor_unitario_comercial'],
                item['quantidade_tributavel'], item['valor_unitario_tributavel'],
                item['valor_total_bruto'], item['valor_desconto'], item['valor_frete'], item['valor_seguro'],
                item['valor_outras_despesas'], item['valor_total_produto'],
                item.get('icms_origem'), item.get('icms_cst'), item.get('icms_base_calculo'), 
                item.get('icms_aliquota'), item.get('icms_valor'),
                item.get('icms_st_base_calculo'), item.get('icms_st_aliquota'), item.get('icms_st_valor'),
                item.get('ipi_cst'), item.get('ipi_base_calculo'), item.get('ipi_aliquota'), item.get('ipi_valor'),
                item.get('pis_cst'), item.get('pis_base_calculo'), item.get('pis_aliquota'), item.get('pis_valor'),
                item.get('cofins_cst'), item.get('cofins_base_calculo'), item.get('cofins_aliquota'), item.get('cofins_valor')
            ]
            
            self.db.insert(query, params)
    
    def _registrar_log(self, xml_file, status, mensagem, chave_acesso, numero_nota, nota_id, tempo_ms):
        """
        Registra log de importação
        
        Args:
            xml_file (str): Caminho do arquivo
            status (str): sucesso, erro ou duplicado
            mensagem (str): Mensagem
            chave_acesso (str): Chave de acesso
            numero_nota (str): Número da nota
            nota_id (int): ID da nota (se sucesso)
            tempo_ms (int): Tempo de processamento em ms
        """
        query = """
            INSERT INTO nfe_import_log (
                arquivo_xml, caminho_completo, status, mensagem,
                chave_acesso, numero_nota, nfe_staging_nota_id, tempo_processamento
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        params = [
            os.path.basename(xml_file),
            xml_file,
            status,
            mensagem,
            chave_acesso,
            numero_nota,
            nota_id,
            tempo_ms
        ]
        
        self.db.insert(query, params)
    
    def _exibir_resumo(self, tempo_total):
        """
        Exibe resumo da importação
        
        Args:
            tempo_total (float): Tempo total em segundos
        """
        print("\n" + "=" * 80)
        print("📊 RESUMO DA IMPORTAÇÃO")
        print("=" * 80)
        print(f"\n📁 Pasta: {self.pasta_xml}")
        print(f"⏱️  Tempo total: {tempo_total:.2f} segundos")
        print(f"\n📦 Arquivos processados: {self.total_arquivos}")
        print(f"   ✅ Sucesso: {self.total_sucesso}")
        print(f"   ⚠️  Duplicados: {self.total_duplicado}")
        print(f"   ❌ Erros: {self.total_erro}")
        
        if self.total_sucesso > 0:
            print(f"\n💰 Total importado:")
            
            # Buscar totais no banco
            totais = self.db.fetch_one("""
                SELECT 
                    COUNT(*) as qtd_notas,
                    SUM(total_nota) as valor_total,
                    COUNT(DISTINCT dest_cnpj_cpf) as qtd_clientes
                FROM nfe_staging_notas
                WHERE status_importacao = 'pendente'
            """)
            
            if totais:
                print(f"   📝 {totais['qtd_notas']} nota(s)")
                print(f"   💵 R$ {totais['valor_total']:,.2f}")
                print(f"   👥 {totais['qtd_clientes']} cliente(s) único(s)")
        
        print("\n" + "=" * 80)
        
        if self.total_erro > 0:
            print(f"\n⚠️  {self.total_erro} arquivo(s) com erro. Verifique os logs:")
            print(f"   SELECT * FROM nfe_import_log WHERE status = 'erro';")


def main():
    """
    Função principal
    """
    # Pasta padrão de XMLs
    pasta_default = r"C:\Users\arita\CascadeProjects\SupplyChainSystem\XML"
    
    print("=" * 80)
    print("📥 IMPORTADOR DE XMLs DE NF-e")
    print("=" * 80)
    
    # Solicitar pasta
    print(f"\nPasta padrão: {pasta_default}")
    resposta = input("Deseja usar a pasta padrão? (s/n): ")
    
    if resposta.lower() == 's':
        pasta_xml = pasta_default
    else:
        pasta_xml = input("Digite o caminho da pasta com os XMLs: ").strip().strip('"').strip("'")
    
    # Executar importação
    importador = ImportadorXMLNFe(pasta_xml)
    importador.importar_todos()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
