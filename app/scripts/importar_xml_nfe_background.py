"""
Script de importação de XMLs em background (chamado pela interface web)
"""
import sys
import os
import json
import time

# Adicionar path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'app'))

from database import get_db
from utils.nfe_xml_parser import parse_nfe_xml
from utils.nfe_evento_parser import parse_nfe_evento
from utils.xml_classifier import classificar_xml


class ImportadorBackground:
    """
    Importador que salva progresso em arquivo JSON
    """
    
    def __init__(self, pasta_xml):
        self.pasta_xml = pasta_xml
        self.db = get_db()
        
        # Arquivo de progresso
        self.progress_file = os.path.join(project_root, 'import_progress.json')
        
        # Estatísticas
        self.total_arquivos = 0
        self.processados = 0
        self.nfe_sucesso = 0
        self.nfe_duplicado = 0
        self.evento_sucesso = 0
        self.erros = 0
        self.desconhecidos = 0
    
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
        """Processa um XML com classificação prévia"""
        try:
            # PASSO 1: Classificar XML rapidamente
            info = classificar_xml(xml_file)
            tipo = info['tipo']
            
            # PASSO 2: Processar baseado no tipo
            if tipo == 'nfe':
                # É NF-e, processar como tal
                status_nfe = info.get('status', 'autorizada')
                
                try:
                    dados_nfe = parse_nfe_xml(xml_file)
                    
                    # Adicionar status ao dados
                    dados_nfe['nota']['status_nfe'] = status_nfe
                    
                    resultado = self._importar_nfe(xml_file, dados_nfe)
                    
                    if resultado == 'sucesso':
                        self.nfe_sucesso += 1
                    elif resultado == 'duplicado':
                        self.nfe_duplicado += 1
                    return
                    
                except Exception as e_nfe:
                    self.erros += 1
                    self._registrar_log(xml_file, 'erro', 'nfe', 
                                      f'Erro ao processar NF-e (status: {status_nfe}): {str(e_nfe)}', 
                                      info.get('chave'), info.get('numero'), None, 0)
                    return
            
            elif tipo in ['cancelamento', 'inutilizacao', 'carta_correcao', 'confirmacao', 'ciencia']:
                # É evento, processar como evento
                try:
                    dados_evento = parse_nfe_evento(xml_file)
                    
                    if dados_evento:
                        resultado = self._importar_evento(xml_file, dados_evento)
                        if resultado == 'sucesso':
                            self.evento_sucesso += 1
                        elif resultado == 'duplicado':
                            self.nfe_duplicado += 1
                        return
                    else:
                        self.desconhecidos += 1
                        self._registrar_log(xml_file, 'erro', tipo, 
                                          'Parser de evento retornou None', 
                                          info.get('chave'), None, None, 0)
                        return
                        
                except Exception as e_evento:
                    self.erros += 1
                    self._registrar_log(xml_file, 'erro', tipo, 
                                      f'Erro ao processar evento: {str(e_evento)}', 
                                      info.get('chave'), None, None, 0)
                    return
            
            elif tipo == 'desconhecido':
                # Tipo não identificado
                self.desconhecidos += 1
                self._registrar_log(xml_file, 'erro', 'desconhecido', 
                                  'Tipo de XML não identificado pela classificação', 
                                  None, None, None, 0)
                return
            
            elif tipo == 'erro':
                # Erro na classificação
                self.erros += 1
                self._registrar_log(xml_file, 'erro', 'classificacao', 
                                  f"Erro ao classificar XML: {info.get('erro', 'Erro desconhecido')}", 
                                  None, None, None, 0)
                return
            
            else:
                # Tipo não suportado
                self.desconhecidos += 1
                self._registrar_log(xml_file, 'erro', tipo, 
                                  f'Tipo de documento não suportado: {tipo}', 
                                  info.get('chave'), None, None, 0)
                return
        
        except Exception as e:
            self.erros += 1
            self._registrar_log(xml_file, 'erro', 'geral', 
                              f'Erro inesperado no processamento: {str(e)}', 
                              None, None, None, 0)
    
    def _importar_nfe(self, xml_file, dados):
        """Importa NF-e"""
        nota = dados['nota']
        itens = dados['itens']
        chave_acesso = nota['chave_acesso']
        
        # Verificar duplicação
        nota_existente = self.db.fetch_one("""
            SELECT id FROM nfe_staging_notas WHERE chave_acesso = %s
        """, [chave_acesso])
        
        if nota_existente:
            self._registrar_log(xml_file, 'duplicado', 'nfe',
                               f"Nota {nota['numero_nota']} já importada",
                               chave_acesso, nota['numero_nota'], None, 0)
            return 'duplicado'
        
        # Inserir
        nota_id = self._inserir_nota(nota, itens, xml_file, dados['xml_original'])
        self._registrar_log(xml_file, 'sucesso', 'nfe',
                           f"NF-e {nota['numero_nota']} importada",
                           chave_acesso, nota['numero_nota'], nota_id, 0)
        return 'sucesso'
    
    def _importar_evento(self, xml_file, dados):
        """Importa evento"""
        tipo = dados['tipo_evento']
        
        # Verificar duplicação pelo arquivo completo
        evento_existente = self.db.fetch_one("""
            SELECT id FROM nfe_eventos WHERE arquivo_xml = %s
        """, [os.path.basename(xml_file)])
        
        if evento_existente:
            self._registrar_log(xml_file, 'duplicado', tipo,
                               f"{tipo.title()} já importado",
                               dados.get('chave_nfe'), None, None, 0)
            return 'duplicado'
        
        # Inserir evento
        try:
            self._inserir_evento(dados, xml_file)
            self._registrar_log(xml_file, 'sucesso', tipo,
                               f"{tipo.title()} importado com sucesso",
                               dados.get('chave_nfe'), None, None, 0)
            return 'sucesso'
        except Exception as e:
            self._registrar_log(xml_file, 'erro', tipo,
                               f"Erro ao inserir {tipo}: {str(e)}",
                               dados.get('chave_nfe'), None, None, 0)
            raise
    
    def _inserir_nota(self, nota, itens, xml_file, xml_original):
        """Insere nota"""
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
                arquivo_xml, xml_original, status_importacao, status_nfe
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
            xml_file, xml_original, 'pendente', nota.get('status_nfe', 'autorizada')
        ]
        
        nota_id = self.db.insert(query, params)
        
        # Inserir itens
        for item in itens:
            self._inserir_item(nota_id, item)
        
        return nota_id
    
    def _inserir_item(self, nota_id, item):
        """Insere item"""
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
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
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
    
    def _inserir_evento(self, dados, xml_file):
        """Insere evento"""
        query = """
            INSERT INTO nfe_eventos (
                tipo_evento, codigo_evento, chave_nfe, numero_protocolo,
                data_evento, sequencial_evento, justificativa,
                cnpj_emitente, serie, numero_inicial, numero_final, ano, modelo,
                status_sefaz, codigo_status, motivo_status, data_autorizacao,
                arquivo_xml, xml_original, status_importacao
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        params = [
            dados['tipo_evento'], dados['codigo_evento'], dados.get('chave_nfe'), dados.get('numero_protocolo'),
            dados.get('data_evento'), dados.get('sequencial_evento'), dados.get('justificativa'),
            dados.get('cnpj_emitente'), dados.get('serie'), dados.get('numero_inicial'), 
            dados.get('numero_final'), dados.get('ano'), dados.get('modelo'),
            dados.get('status_sefaz'), dados.get('codigo_status'), dados.get('motivo_status'), 
            dados.get('data_autorizacao'),
            os.path.basename(xml_file), dados.get('xml_original'), 'pendente'
        ]
        
        return self.db.insert(query, params)
    
    def _registrar_log(self, xml_file, status, tipo_doc, mensagem, chave, numero, ref_id, tempo_ms):
        """Registra log"""
        query = """
            INSERT INTO nfe_import_log (
                arquivo_xml, caminho_completo, status, tipo_documento, mensagem,
                chave_acesso, numero_nota, nfe_staging_nota_id, tempo_processamento
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = [
            os.path.basename(xml_file), xml_file, status, tipo_doc, mensagem,
            chave, numero, ref_id, tempo_ms
        ]
        
        self.db.insert(query, params)
    
    def _salvar_progresso(self, status, tempo_total=None):
        """Salva progresso em arquivo JSON"""
        progresso = {
            'status': status,
            'total_arquivos': self.total_arquivos,
            'total_processados': self.processados,
            'sucesso': self.nfe_sucesso + self.evento_sucesso,
            'erros': self.erros + self.desconhecidos,
            'duplicados': self.nfe_duplicado,
            'nfe_sucesso': self.nfe_sucesso,
            'evento_sucesso': self.evento_sucesso,
            'tempo_total': tempo_total
        }
        
        with open(self.progress_file, 'w') as f:
            json.dump(progresso, f)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python importar_xml_nfe_background.py <pasta_xml>")
        sys.exit(1)
    
    pasta = sys.argv[1]
    
    importador = ImportadorBackground(pasta)
    importador.importar()
