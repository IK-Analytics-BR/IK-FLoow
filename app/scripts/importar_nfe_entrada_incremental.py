"""
IMPORTAÇÃO INCREMENTAL DE NFe DE ENTRADA (Compras)
- Upload de XML
- Verifica duplicidade por chave de acesso
- Não limpa dados existentes
- Descarta XML após processar
- Ideal para produção na AWS
"""

import sys
import os
import tempfile
import shutil

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.utils.nfe_xml_parser import NFeXMLParser
from database import get_db
import time
from datetime import datetime
from decimal import Decimal


class ImportadorNFeEntradaIncremental:
    """Importador incremental de NFe de Entrada"""
    
    def __init__(self):
        self.db = get_db()
        self.parser = NFeXMLParser()
        self.temp_dir = None
        
        # Estatísticas
        self.total_arquivos = 0
        self.processados = 0
        self.sucesso = 0
        self.duplicados = 0
        self.erros = 0
        self.erros_detalhes = []
    
    def criar_diretorio_temporario(self):
        """Cria diretório temporário para upload"""
        self.temp_dir = tempfile.mkdtemp(prefix='nfe_entrada_')
        print(f"📁 Diretório temporário criado: {self.temp_dir}")
        return self.temp_dir
    
    def limpar_diretorio_temporario(self):
        """Remove diretório temporário após processamento"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"🗑️ Diretório temporário removido")
    
    def verificar_duplicidade(self, chave_acesso):
        """Verifica se a NFe já foi importada pela chave de acesso"""
        resultado = self.db.fetch_one(
            "SELECT id FROM nfe_entrada_staging_notas WHERE chave_acesso = %s",
            (chave_acesso,)
        )
        return resultado is not None
    
    def importar_arquivo(self, caminho_xml):
        """Importa um arquivo XML individualmente"""
        
        self.total_arquivos += 1
        nome_arquivo = os.path.basename(caminho_xml)
        
        try:
            # Parse do XML
            parse_result = self.parser.parse(caminho_xml)
            
            if not parse_result or 'nota' not in parse_result:
                self.erros += 1
                erro = f"❌ {nome_arquivo}: XML inválido ou sem chave de acesso"
                self.erros_detalhes.append(erro)
                print(erro)
                return False
            
            # Extrair dados da estrutura aninhada
            nfe_data = parse_result['nota']
            nfe_data['itens'] = parse_result.get('itens', [])
            
            if 'chave_acesso' not in nfe_data:
                self.erros += 1
                erro = f"❌ {nome_arquivo}: XML sem chave de acesso"
                self.erros_detalhes.append(erro)
                print(erro)
                return False
            
            chave_acesso = nfe_data['chave_acesso']
            
            # Verificar duplicidade
            if self.verificar_duplicidade(chave_acesso):
                self.duplicados += 1
                print(f"⚠️ {nome_arquivo}: Já importado (chave: {chave_acesso})")
                
                # Registrar no log como duplicado
                self._registrar_log(
                    nome_arquivo, caminho_xml, 'duplicado',
                    'NFe já importada anteriormente', chave_acesso,
                    nfe_data.get('numero_nota'), nfe_data.get('emit_cnpj'),
                    nfe_data.get('emit_razao_social')
                )
                return True
            
            # Inserir nota na staging
            nota_id = self._inserir_nota_staging(nfe_data, caminho_xml)
            
            if not nota_id:
                self.erros += 1
                erro = f"❌ {nome_arquivo}: Erro ao inserir nota"
                self.erros_detalhes.append(erro)
                print(erro)
                return False
            
            # Inserir itens na staging
            if 'itens' in nfe_data and nfe_data['itens']:
                for item in nfe_data['itens']:
                    self._inserir_item_staging(nota_id, item)
            
            # Registrar sucesso no log
            self._registrar_log(
                nome_arquivo, caminho_xml, 'sucesso',
                'NFe importada com sucesso', chave_acesso,
                nfe_data.get('numero_nota'), nfe_data.get('emit_cnpj'),
                nfe_data.get('emit_razao_social'), nota_id
            )
            
            self.sucesso += 1
            self.processados += 1
            print(f"✅ {nome_arquivo}: Importado (Nota: {nfe_data.get('numero_nota')})")
            return True
            
        except Exception as e:
            self.erros += 1
            erro = f"❌ {nome_arquivo}: {str(e)}"
            self.erros_detalhes.append(erro)
            print(erro)
            return False
    
    def _inserir_nota_staging(self, nfe_data, caminho_xml):
        """Insere nota na tabela de staging"""
        
        query = """
            INSERT INTO nfe_entrada_staging_notas (
                chave_acesso, numero_nota, serie, data_emissao, data_entrada,
                emit_cnpj, emit_razao_social, emit_fantasia, emit_ie, emit_uf,
                emit_municipio, dest_cnpj, dest_razao_social,
                total_nota, total_produtos, total_frete, total_seguro,
                total_desconto, total_ipi, total_icms, total_pis, total_cofins,
                status_importacao
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                'pendente'
            )
        """
        
        params = (
            nfe_data.get('chave_acesso'),
            nfe_data.get('numero_nota'),
            nfe_data.get('serie'),
            nfe_data.get('data_emissao'),
            nfe_data.get('data_entrada'),
            nfe_data.get('emit_cnpj'),
            nfe_data.get('emit_razao_social'),
            nfe_data.get('emit_fantasia'),
            nfe_data.get('emit_ie'),
            nfe_data.get('emit_uf'),
            nfe_data.get('emit_municipio'),
            nfe_data.get('dest_cnpj'),
            nfe_data.get('dest_razao_social'),
            nfe_data.get('total_nota'),
            nfe_data.get('total_produtos'),
            nfe_data.get('total_frete', 0),
            nfe_data.get('total_seguro', 0),
            nfe_data.get('total_desconto', 0),
            nfe_data.get('total_ipi', 0),
            nfe_data.get('total_icms', 0),
            nfe_data.get('total_pis', 0),
            nfe_data.get('total_cofins', 0),
        )
        
        return self.db.execute(query, params)
    
    def _inserir_item_staging(self, nota_id, item):
        """Insere item na tabela de staging"""
        
        query = """
            INSERT INTO nfe_entrada_staging_itens (
                nfe_entrada_staging_nota_id, numero_item, codigo_produto,
                gtin, gtin_tributavel, descricao, ncm, cest, cfop,
                unidade_comercial, unidade_tributavel,
                quantidade_comercial, valor_unitario_comercial,
                quantidade_tributavel, valor_unitario_tributavel,
                valor_total, valor_frete, valor_seguro, valor_desconto,
                valor_outras_despesas, valor_total_tributos
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        params = (
            nota_id,
            item.get('numero_item'),
            item.get('codigo_produto'),
            item.get('gtin', 'SEM GTIN'),
            item.get('gtin_tributavel', 'SEM GTIN'),
            item.get('descricao'),
            item.get('ncm'),
            item.get('cest'),
            item.get('cfop'),
            item.get('unidade_comercial'),
            item.get('unidade_tributavel'),
            item.get('quantidade_comercial'),
            item.get('valor_unitario_comercial'),
            item.get('quantidade_tributavel'),
            item.get('valor_unitario_tributavel'),
            item.get('valor_total'),
            item.get('valor_frete', 0),
            item.get('valor_seguro', 0),
            item.get('valor_desconto', 0),
            item.get('valor_outras_despesas', 0),
            item.get('valor_total_tributos', 0),
        )
        
        return self.db.execute(query, params)
    
    def _registrar_log(self, arquivo_xml, caminho_completo, status, mensagem,
                       chave_acesso=None, numero_nota=None, emit_cnpj=None,
                       emit_razao_social=None, nota_staging_id=None):
        """Registra log de importação"""
        
        query = """
            INSERT INTO nfe_entrada_import_log (
                arquivo_xml, caminho_completo, status_importacao, mensagem,
                chave_acesso, numero_nota, emit_cnpj, emit_razao_social,
                nfe_entrada_staging_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        self.db.execute(query, (
            arquivo_xml, caminho_completo, status, mensagem,
            chave_acesso, numero_nota, emit_cnpj, emit_razao_social,
            nota_staging_id
        ))
    
    def processar_staging(self):
        """Processa notas pendentes na staging"""
        
        print("\n" + "="*60)
        print("PROCESSANDO NFe DE ENTRADA")
        print("="*60)
        
        # Verificar notas pendentes
        stats = self.db.fetch_one("""
            SELECT 
                COUNT(*) as total_pendentes,
                SUM(total_nota) as valor_total
            FROM nfe_entrada_staging_notas
            WHERE status_importacao = 'pendente'
        """)
        
        print(f"\n📊 Notas pendentes: {stats['total_pendentes']}")
        print(f"💰 Valor total: R$ {stats['valor_total']:,.2f}")
        
        if stats['total_pendentes'] == 0:
            print("\n⚠️ Nenhuma nota pendente para processar!")
            return True
        
        # Processar via stored procedure
        print("\n🔄 Iniciando processamento em lote...")
        inicio = time.time()
        
        try:
            cursor = self.db.connection.cursor(dictionary=True)
            cursor.callproc('processar_todas_nfe_entrada')
            
            # Obter result sets
            resumo = None
            logs = []
            
            for result in cursor.stored_results():
                rows = result.fetchall()
                if rows:
                    if len(rows) == 1 and 'notas_processadas' in rows[0]:
                        resumo = rows[0]
                    else:
                        logs = rows
            
            # Mostrar resumo
            if resumo:
                print(f"\n✅ Processamento concluído!")
                print(f"   Processadas: {resumo.get('notas_processadas', 0)}")
                print(f"   Com erro: {resumo.get('notas_com_erro', 0)}")
                print(f"   Total: {resumo.get('total_tentativas', 0)}")
            
            # Mostrar logs de erro
            if logs:
                erros = [log for log in logs if log.get('status') == 'erro']
                if erros:
                    print(f"\n❌ Notas com erro: {len(erros)}")
                    for log in erros[:5]:  # Mostrar apenas 5 primeiros
                        print(f"   Nota {log.get('numero_nota')}: {log.get('mensagem')}")
            
            cursor.close()
            self.db.connection.commit()
            
            tempo = time.time() - inicio
            print(f"\n⏱️ Tempo de processamento: {tempo:.2f} segundos")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro ao processar: {e}")
            return False
    
    def mostrar_estatisticas(self):
        """Mostra estatísticas da importação"""
        
        print("\n" + "="*60)
        print("ESTATÍSTICAS DA IMPORTAÇÃO")
        print("="*60)
        
        print(f"\n📂 Total de arquivos: {self.total_arquivos}")
        print(f"✅ Sucesso: {self.sucesso}")
        print(f"⚠️ Duplicados: {self.duplicados}")
        print(f"❌ Erros: {self.erros}")
        
        if self.erros_detalhes:
            print(f"\n❌ DETALHES DOS ERROS (primeiros 10):")
            for erro in self.erros_detalhes[:10]:
                print(f"   {erro}")


def importar_xml_files(lista_arquivos_xml):
    """
    Importa lista de arquivos XML (usado quando há upload)
    
    Args:
        lista_arquivos_xml: Lista de caminhos para arquivos XML
    
    Returns:
        dict: Estatísticas da importação
    """
    
    print("\n" + "="*60)
    print("IMPORTAÇÃO INCREMENTAL DE NFe DE ENTRADA")
    print("="*60)
    print(f"📁 Total de arquivos: {len(lista_arquivos_xml)}")
    
    importador = ImportadorNFeEntradaIncremental()
    
    # Importar cada arquivo
    for i, caminho_xml in enumerate(lista_arquivos_xml):
        importador.importar_arquivo(caminho_xml)
        # Pequeno delay a cada 1000 arquivos para aliviar carga no banco
        if (i + 1) % 1000 == 0:
            print(f"\n[INFO] Pausa de 2 segundos após {i + 1} arquivos...")
            time.sleep(2)
    
    # Mostrar estatísticas
    importador.mostrar_estatisticas()
    
    # Processar staging
    if importador.sucesso > 0:
        importador.processar_staging()
    
    return {
        'total': importador.total_arquivos,
        'sucesso': importador.sucesso,
        'duplicados': importador.duplicados,
        'erros': importador.erros,
        'erros_detalhes': importador.erros_detalhes
    }


if __name__ == '__main__':
    # Exemplo de uso com pasta local
    if len(sys.argv) > 1:
        pasta_xml = sys.argv[1]
        
        if not os.path.exists(pasta_xml):
            print(f"❌ Pasta não encontrada: {pasta_xml}")
            sys.exit(1)
        
        # Listar XMLs
        arquivos_xml = [
            os.path.join(pasta_xml, f)
            for f in os.listdir(pasta_xml)
            if f.endswith('.xml')
        ]
        
        if not arquivos_xml:
            print(f"❌ Nenhum arquivo XML encontrado em: {pasta_xml}")
            sys.exit(1)
        
        # Importar
        stats = importar_xml_files(arquivos_xml)
        
        print("\n" + "="*60)
        print("🎉 IMPORTAÇÃO CONCLUÍDA!")
        print("="*60)
    else:
        print("Uso: python importar_nfe_entrada_incremental.py PASTA_XML")
