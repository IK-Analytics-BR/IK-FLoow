"""
Importador COMPLETO de XMLs de NF-e
Importa NF-e, cancelamentos, inutilizações e cartas de correção
"""
import sys
import os
import time
from pathlib import Path

# Adicionar path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'app'))

from database import get_db
from utils.nfe_xml_parser import parse_nfe_xml
from utils.nfe_evento_parser import parse_nfe_evento


class ImportadorXMLCompleto:
    """
    Importador completo de XMLs (NF-e + Eventos)
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
        
        # NF-e
        self.total_nfe_sucesso = 0
        self.total_nfe_duplicado = 0
        self.total_nfe_erro = 0
        
        # Eventos
        self.total_cancelamento = 0
        self.total_inutilizacao = 0
        self.total_carta_correcao = 0
        self.total_evento_erro = 0
        
        # Outros
        self.total_desconhecido = 0
    
    def importar_todos(self):
        """
        Importa todos os XMLs da pasta
        """
        print("=" * 80)
        print("📥 IMPORTAÇÃO COMPLETA DE XMLs DE NF-e")
        print("=" * 80)
        print(f"\n📁 Pasta: {self.pasta_xml}")
        print("\n🔍 Este importador processa:")
        print("   ✅ NF-e (notas fiscais)")
        print("   ✅ Cancelamentos")
        print("   ✅ Inutilizações")
        print("   ✅ Cartas de correção")
        
        # Verificar pasta
        if not os.path.exists(self.pasta_xml):
            print(f"\n❌ ERRO: Pasta não encontrada: {self.pasta_xml}")
            return
        
        # Buscar XMLs
        print(f"\n🔍 Buscando arquivos XML...")
        xml_files = self._buscar_xmls()
        
        if not xml_files:
            print(f"\n⚠️  Nenhum arquivo XML encontrado")
            return
        
        self.total_arquivos = len(xml_files)
        print(f"✅ Encontrados {self.total_arquivos} arquivo(s) XML")
        
        # Confirmar
        resposta = input(f"\n❓ Deseja importar {self.total_arquivos} arquivo(s)? (s/n): ")
        if resposta.lower() != 's':
            print("\n❌ Importação cancelada.")
            return
        
        # Importar
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
        Busca todos os XMLs recursivamente
        
        Returns:
            list: Lista de caminhos
        """
        xml_files = []
        pastas_encontradas = set()
        
        for root, dirs, files in os.walk(self.pasta_xml):
            pastas_encontradas.add(root)
            for file in files:
                if file.lower().endswith('.xml'):
                    xml_path = os.path.join(root, file)
                    xml_files.append(xml_path)
        
        # Mostrar subpastas
        if len(pastas_encontradas) > 1:
            print(f"   📂 Encontradas {len(pastas_encontradas)} pasta(s) (incluindo subpastas)")
            for pasta in sorted(pastas_encontradas):
                qtd_xml = len([f for f in xml_files if f.startswith(pasta)])
                if qtd_xml > 0:
                    print(f"      • {os.path.relpath(pasta, self.pasta_xml)}: {qtd_xml} XML(s)")
        
        return sorted(xml_files)
    
    def _importar_xml(self, xml_file):
        """
        Importa um XML (detecta tipo automaticamente)
        
        Args:
            xml_file (str): Caminho do arquivo
        """
        inicio = time.time()
        
        try:
            # 1. Tentar como NF-e
            try:
                print(f"   📄 Tentando como NF-e...")
                dados_nfe = parse_nfe_xml(xml_file)
                self._importar_nfe(xml_file, dados_nfe, inicio)
                return
            except Exception as e_nfe:
                erro_nfe = str(e_nfe)
                
                # Se não for NF-e, tentar como evento
                if 'NFe não encontrado' in erro_nfe or 'infNFe não encontrado' in erro_nfe or 'NoneType' in erro_nfe:
                    print(f"   🔄 Não é NF-e, tentando como evento...")
                    
                    try:
                        dados_evento = parse_nfe_evento(xml_file)
                        
                        if dados_evento:
                            self._importar_evento(xml_file, dados_evento, inicio)
                            return
                        else:
                            # Não é NF-e nem evento
                            print(f"   ⚠️  Tipo de documento desconhecido")
                            self._registrar_log(xml_file, 'erro', 'desconhecido', 
                                               'Tipo de documento desconhecido', None, None, None,
                                               int((time.time() - inicio) * 1000))
                            self.total_desconhecido += 1
                            return
                            
                    except Exception as e_evento:
                        # Erro ao tentar parse como evento
                        print(f"   ❌ ERRO: {str(e_evento)}")
                        self._registrar_log(xml_file, 'erro', 'desconhecido',
                                           f"NF-e: {erro_nfe} | Evento: {str(e_evento)}", 
                                           None, None, None,
                                           int((time.time() - inicio) * 1000))
                        self.total_desconhecido += 1
                        return
                else:
                    # Erro diferente em NF-e
                    raise e_nfe
        
        except Exception as e:
            # Erro geral
            print(f"   ❌ ERRO: {str(e)}")
            self._registrar_log(xml_file, 'erro', 'desconhecido', str(e), None, None, None,
                               int((time.time() - inicio) * 1000))
            self.total_nfe_erro += 1
    
    def _importar_nfe(self, xml_file, dados, inicio):
        """
        Importa NF-e
        
        Args:
            xml_file (str): Caminho do arquivo
            dados (dict): Dados extraídos
            inicio (float): Tempo de início
        """
        nota = dados['nota']
        itens = dados['itens']
        chave_acesso = nota['chave_acesso']
        numero_nota = nota['numero_nota']
        
        # Verificar duplicação
        print(f"   🔍 Verificando duplicação...")
        nota_existente = self.db.fetch_one("""
            SELECT id FROM nfe_staging_notas WHERE chave_acesso = %s
        """, [chave_acesso])
        
        if nota_existente:
            print(f"   ⚠️  NF-e já importada")
            self._registrar_log(xml_file, 'duplicado', 'nfe',
                               f"Nota {numero_nota} já importada",
                               chave_acesso, numero_nota, None,
                               int((time.time() - inicio) * 1000))
            self.total_nfe_duplicado += 1
            return
        
        # Inserir
        print(f"   💾 Inserindo NF-e...")
        nota_id = self._inserir_nota(nota, itens, xml_file, dados['xml_original'])
        
        tempo_ms = int((time.time() - inicio) * 1000)
        self._registrar_log(xml_file, 'sucesso', 'nfe',
                           f"NF-e {numero_nota} importada com {len(itens)} item(ns)",
                           chave_acesso, numero_nota, nota_id, tempo_ms)
        
        print(f"   ✅ NF-e importada! ({tempo_ms}ms)")
        self.total_nfe_sucesso += 1
    
    def _importar_evento(self, xml_file, dados, inicio):
        """
        Importa evento (cancelamento, inutilização, carta de correção)
        
        Args:
            xml_file (str): Caminho do arquivo
            dados (dict): Dados do evento
            inicio (float): Tempo de início
        """
        tipo = dados['tipo_evento']
        chave_nfe = dados.get('chave_nfe')
        
        # Verificar duplicação (por chave ou arquivo)
        print(f"   🔍 Verificando duplicação de {tipo}...")
        
        check_duplicado = """
            SELECT id FROM nfe_eventos 
            WHERE arquivo_xml = %s
        """
        
        evento_existente = self.db.fetch_one(check_duplicado, [os.path.basename(xml_file)])
        
        if evento_existente:
            print(f"   ⚠️  {tipo.title()} já importado")
            self._registrar_log(xml_file, 'duplicado', tipo,
                               f"{tipo.title()} já importado",
                               chave_nfe, None, None,
                               int((time.time() - inicio) * 1000))
            
            if tipo == 'cancelamento':
                self.total_cancelamento += 1
            elif tipo == 'inutilizacao':
                self.total_inutilizacao += 1
            elif tipo == 'carta_correcao':
                self.total_carta_correcao += 1
            
            return
        
        # Inserir evento
        print(f"   💾 Inserindo {tipo}...")
        evento_id = self._inserir_evento(dados, xml_file)
        
        tempo_ms = int((time.time() - inicio) * 1000)
        self._registrar_log(xml_file, 'sucesso', tipo,
                           f"{tipo.title()} importado",
                           chave_nfe, None, evento_id, tempo_ms)
        
        print(f"   ✅ {tipo.title()} importado! ({tempo_ms}ms)")
        
        if tipo == 'cancelamento':
            self.total_cancelamento += 1
        elif tipo == 'inutilizacao':
            self.total_inutilizacao += 1
        elif tipo == 'carta_correcao':
            self.total_carta_correcao += 1
    
    def _inserir_nota(self, nota, itens, xml_file, xml_original):
        """Insere NF-e (mesmo código do importador anterior)"""
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
        
        # Inserir itens
        for item in itens:
            self._inserir_item(nota_id, item)
        
        return nota_id
    
    def _inserir_item(self, nota_id, item):
        """Insere item da NF-e (mesmo código do importador anterior)"""
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
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s
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
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        params = [
            os.path.basename(xml_file),
            xml_file,
            status,
            tipo_doc,
            mensagem,
            chave,
            numero,
            ref_id,
            tempo_ms
        ]
        
        self.db.insert(query, params)
    
    def _exibir_resumo(self, tempo_total):
        """Exibe resumo"""
        print("\n" + "=" * 80)
        print("📊 RESUMO DA IMPORTAÇÃO COMPLETA")
        print("=" * 80)
        print(f"\n📁 Pasta: {self.pasta_xml}")
        print(f"⏱️  Tempo total: {tempo_total:.2f} segundos")
        print(f"\n📦 Arquivos processados: {self.total_arquivos}")
        print(f"\n📄 NF-e (NOTAS FISCAIS):")
        print(f"   ✅ Sucesso: {self.total_nfe_sucesso}")
        print(f"   ⚠️  Duplicados: {self.total_nfe_duplicado}")
        print(f"   ❌ Erros: {self.total_nfe_erro}")
        print(f"\n📋 EVENTOS:")
        print(f"   🚫 Cancelamentos: {self.total_cancelamento}")
        print(f"   ⛔ Inutilizações: {self.total_inutilizacao}")
        print(f"   📝 Cartas de Correção: {self.total_carta_correcao}")
        print(f"   ❌ Erros em eventos: {self.total_evento_erro}")
        
        if self.total_desconhecido > 0:
            print(f"\n⚠️  Documentos desconhecidos: {self.total_desconhecido}")
        
        # Totais
        if self.total_nfe_sucesso > 0:
            print(f"\n💰 TOTAIS IMPORTADOS:")
            
            # NF-e
            totais_nfe = self.db.fetch_one("""
                SELECT 
                    COUNT(*) as qtd,
                    SUM(total_nota) as valor
                FROM nfe_staging_notas
                WHERE status_importacao = 'pendente'
            """)
            
            if totais_nfe:
                print(f"   📄 NF-e: {totais_nfe['qtd']} nota(s) - R$ {totais_nfe['valor']:,.2f}")
            
            # Eventos
            totais_eventos = self.db.fetch_one("""
                SELECT 
                    tipo_evento,
                    COUNT(*) as qtd
                FROM nfe_eventos
                GROUP BY tipo_evento
            """)
            
            if totais_eventos:
                print(f"   📋 Eventos: {self.total_cancelamento + self.total_inutilizacao + self.total_carta_correcao}")
        
        print("\n" + "=" * 80)


def main():
    """Função principal"""
    pasta_default = r"C:\Users\arita\CascadeProjects\SupplyChainSystem\XML"
    
    print("=" * 80)
    print("📥 IMPORTADOR COMPLETO DE XMLs DE NF-e")
    print("=" * 80)
    
    print(f"\nPasta padrão: {pasta_default}")
    resposta = input("Deseja usar a pasta padrão? (s/n): ")
    
    if resposta.lower() == 's':
        pasta_xml = pasta_default
    else:
        pasta_xml = input("Digite o caminho da pasta: ").strip().strip('"').strip("'")
    
    importador = ImportadorXMLCompleto(pasta_xml)
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
