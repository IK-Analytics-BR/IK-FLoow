"""
Script Completo: Importa XMLs + Processa NFe de ENTRADA
Executa em 2 etapas:
1. Importa XMLs para staging
2. Processa staging → Tabelas finais (fornecedores, produtos, pedidos, estoque)
"""

import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.scripts.importar_xml_nfe_entrada_background import ImportadorEntradaBackground
from database import get_db
import time
from datetime import datetime


def limpar_dados_anteriores():
    """
    Limpa TODOS os dados anteriores de NFe de Entrada:
    - Staging (notas e itens) → TUDO
    - Pedidos de compra → APENAS os vinculados a NFe
    - Movimentos de estoque → APENAS os de pedidos NFe
    - Fornecedores → APENAS os criados HOJE
    - Produtos → APENAS matéria prima (categoria 3) criados HOJE
    
    IMPORTANTE: Fornecedores e Produtos são filtrados por data de criação
    porque as tabelas não têm coluna nfe_entrada_staging_id.
    Se rodar em dias diferentes, dados antigos não serão limpos.
    """
    db = get_db()
    
    print("\n" + "="*60)
    print("LIMPANDO DADOS ANTERIORES")
    print("="*60)
    
    try:
        # Desabilitar verificação de foreign keys
        db.execute("SET FOREIGN_KEY_CHECKS = 0")
        print("\n🔓 Verificações de chave estrangeira desabilitadas")
        
        # Contar registros antes de limpar
        print("\n📊 Contando registros antes da limpeza...")
        stats_antes = {
            'staging_notas': db.fetch_one("SELECT COUNT(*) as total FROM nfe_entrada_staging_notas")['total'],
            'staging_itens': db.fetch_one("SELECT COUNT(*) as total FROM nfe_entrada_staging_itens")['total'],
            'import_log': db.fetch_one("SELECT COUNT(*) as total FROM nfe_entrada_import_log")['total'],
            'stock_movements': db.fetch_one("""
                SELECT COUNT(*) as total 
                FROM stock_movements sm
                INNER JOIN purchase_orders po ON sm.reference_id = po.id
                WHERE sm.reference_type = 'purchase_order' 
                AND po.nfe_entrada_staging_id IS NOT NULL
            """)['total'],
            'pedidos': db.fetch_one("SELECT COUNT(*) as total FROM purchase_orders WHERE nfe_entrada_staging_id IS NOT NULL")['total'],
            'fornecedores': db.fetch_one("SELECT COUNT(*) as total FROM suppliers WHERE DATE(created_at) = CURDATE()")['total'],
            'produtos': db.fetch_one("SELECT COUNT(*) as total FROM products WHERE category_id = 3 AND DATE(created_at) = CURDATE()")['total']
        }
        
        print(f"   📦 Staging Notas: {stats_antes['staging_notas']}")
        print(f"   📦 Staging Itens: {stats_antes['staging_itens']}")
        print(f"   📝 Log de Importação: {stats_antes['import_log']}")
        print(f"   📊 Movimentos de Estoque: {stats_antes['stock_movements']}")
        print(f"   🛒 Pedidos de Compra: {stats_antes['pedidos']}")
        print(f"   👥 Fornecedores: {stats_antes['fornecedores']}")
        print(f"   📦 Produtos: {stats_antes['produtos']}")
        
        # Limpar na ordem correta (respeitar dependências)
        print("\n🗑️ Limpando dados...")
        
        # 1. Movimentos de estoque (dependem de pedidos)
        if stats_antes['stock_movements'] > 0:
            db.execute("""
                DELETE sm FROM stock_movements sm
                INNER JOIN purchase_orders po ON sm.reference_id = po.id
                WHERE sm.reference_type = 'purchase_order' 
                AND po.nfe_entrada_staging_id IS NOT NULL
            """)
            print("   ✅ Movimentos de estoque apagados")
        
        # 2. Pedidos de compra (dependem de fornecedores e produtos)
        if stats_antes['pedidos'] > 0:
            db.execute("DELETE FROM purchase_orders WHERE nfe_entrada_staging_id IS NOT NULL")
            print("   ✅ Pedidos de compra apagados")
        
        # 3. Produtos (matéria prima criados hoje)
        if stats_antes['produtos'] > 0:
            db.execute("DELETE FROM products WHERE category_id = 3 AND DATE(created_at) = CURDATE()")
            print("   ✅ Produtos apagados")
        
        # 4. Fornecedores (criados hoje)
        if stats_antes['fornecedores'] > 0:
            db.execute("DELETE FROM suppliers WHERE DATE(created_at) = CURDATE()")
            print("   ✅ Fornecedores apagados")
        
        # 5. Staging (tabelas temporárias)
        db.execute("TRUNCATE TABLE nfe_entrada_staging_itens")
        print("   ✅ Staging Itens limpo")
        
        db.execute("TRUNCATE TABLE nfe_entrada_staging_notas")
        print("   ✅ Staging Notas limpo")
        
        db.execute("TRUNCATE TABLE nfe_entrada_import_log")
        print("   ✅ Log de Importação limpo")
        
        # Reabilitar verificação de foreign keys
        db.execute("SET FOREIGN_KEY_CHECKS = 1")
        print("\n🔒 Verificações de chave estrangeira reabilitadas")
        
        print("\n✅ Limpeza concluída com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro ao limpar dados: {e}")
        # Garantir que foreign key checks seja reabilitado mesmo em caso de erro
        try:
            db.execute("SET FOREIGN_KEY_CHECKS = 1")
        except:
            pass
        raise e


def processar_staging_nfe():
    """
    Processa todas as NFe pendentes na staging
    Cria: Fornecedores, Produtos, Pedidos de Compra, Movimentações de Estoque
    """
    db = get_db()
    
    print("\n" + "="*60)
    print("ETAPA 2: PROCESSANDO NFe DE ENTRADA")
    print("="*60)
    
    # Contar notas pendentes
    stats_antes = db.fetch_one("""
        SELECT 
            COUNT(*) as total_pendentes,
            SUM(total_nota) as valor_total
        FROM nfe_entrada_staging_notas
        WHERE status_importacao = 'pendente'
    """)
    
    print(f"\n📊 Notas pendentes: {stats_antes['total_pendentes']}")
    print(f"💰 Valor total: R$ {stats_antes['valor_total']:,.2f}")
    
    if stats_antes['total_pendentes'] == 0:
        print("\n⚠️ Nenhuma nota pendente para processar!")
        return
    
    # Chamar procedure de processamento em lote
    print("\n🔄 Iniciando processamento em lote...")
    inicio = time.time()
    
    try:
        # Usar callproc() para stored procedures (MySQL Connector 8.0+)
        cursor = db.connection.cursor(dictionary=True)
        cursor.callproc('processar_todas_nfe_entrada')
        
        # Obter result sets da procedure
        resumo = None
        logs = []
        
        for result in cursor.stored_results():
            rows = result.fetchall()
            if rows:
                # Primeiro result set (resumo) tem 1 linha
                if len(rows) == 1 and 'notas_processadas' in rows[0]:
                    resumo = rows[0]
                # Segundo result set (logs) tem múltiplas linhas
                else:
                    logs = rows
        
        # Mostrar resumo
        if resumo:
            processadas = resumo.get('notas_processadas', 0)
            erros_count = resumo.get('notas_com_erro', 0)
            total = resumo.get('total_tentativas', 0)
            
            print(f"\n✅ Processamento concluído!")
            print(f"   Processadas: {processadas}")
            print(f"   Com erro: {erros_count}")
            print(f"   Total tentativas: {total}")
        
        # Mostrar logs
        if logs:
            sucessos = sum(1 for log in logs if log.get('status') == 'sucesso')
            erros_count = sum(1 for log in logs if log.get('status') == 'erro')
            
            print(f"\n📋 Detalhes:")
            print(f"   ✅ Sucesso: {sucessos}")
            print(f"   ❌ Erros: {erros_count}")
            
            # Mostrar erros se houver
            if erros_count > 0:
                print(f"\n❌ NOTAS COM ERRO:")
                for log in logs:
                    if log.get('status') == 'erro':
                        numero = log.get('numero_nota')
                        mensagem = log.get('mensagem')
                        print(f"   Nota {numero}: {mensagem}")
        
        cursor.close()
        db.connection.commit()
        
    except Exception as e:
        print(f"\n❌ Erro ao processar: {e}")
        return
    
    tempo_total = time.time() - inicio
    
    # Estatísticas finais
    print("\n" + "="*60)
    print("ESTATÍSTICAS FINAIS")
    print("="*60)
    
    stats_final = {
        'fornecedores': db.fetch_one("""
            SELECT COUNT(*) as total 
            FROM suppliers 
            WHERE email LIKE '%@nfe.importado' 
            AND DATE(created_at) = CURDATE()
        """),
        'pedidos': db.fetch_one("""
            SELECT 
                COUNT(*) as total_pedidos,
                SUM(total_value) as valor_total
            FROM purchase_orders 
            WHERE nfe_entrada_staging_id IS NOT NULL 
            AND DATE(created_at) = CURDATE()
        """),
        'produtos': db.fetch_one("""
            SELECT COUNT(*) as total 
            FROM products 
            WHERE category_id = 3 
            AND DATE(created_at) = CURDATE()
        """),
        'estoque': db.fetch_one("""
            SELECT 
                COUNT(*) as total_movimentos,
                SUM(quantity) as quantidade_total
            FROM stock_movements sm
            INNER JOIN purchase_orders po ON sm.reference_id = po.id
            WHERE sm.reference_type = 'purchase_order' 
            AND po.nfe_entrada_staging_id IS NOT NULL
            AND DATE(sm.created_at) = CURDATE()
        """)
    }
    
    print(f"\n👥 Fornecedores criados: {stats_final['fornecedores']['total']}")
    print(f"📦 Produtos criados: {stats_final['produtos']['total']}")
    print(f"🛒 Pedidos de compra: {stats_final['pedidos']['total_pedidos']}")
    print(f"💰 Valor total pedidos: R$ {stats_final['pedidos']['valor_total']:,.2f}")
    print(f"📊 Movimentos de estoque: {stats_final['estoque']['total_movimentos']}")
    print(f"📈 Quantidade total: {stats_final['estoque']['quantidade_total']:,.2f}")
    
    print(f"\n⏱️ Tempo total de processamento: {tempo_total:.2f} segundos")


def main():
    """
    Função principal: Limpa → Importa XMLs → Processa NFe
    """
    if len(sys.argv) < 2:
        print("Uso: python importar_e_processar_nfe_entrada.py <pasta_xml>")
        sys.exit(1)
    
    pasta_xml = sys.argv[1]
    
    if not os.path.exists(pasta_xml):
        print(f"❌ Pasta não encontrada: {pasta_xml}")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("IMPORTAÇÃO E PROCESSAMENTO COMPLETO DE NFe DE ENTRADA")
    print("="*60)
    print(f"📁 Pasta: {pasta_xml}")
    print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    inicio_total = time.time()
    
    # ETAPA 0: LIMPAR DADOS ANTERIORES
    limpar_dados_anteriores()
    
    # Aguardar 1 segundo
    print("\n⏳ Aguardando 1 segundo antes de importar...")
    time.sleep(1)
    
    # ETAPA 1: IMPORTAR XMLs
    print("\n" + "="*60)
    print("ETAPA 1: IMPORTANDO XMLs PARA STAGING")
    print("="*60)
    
    importador = ImportadorEntradaBackground(pasta_xml)
    importador.importar()
    
    print(f"\n✅ Importação de XMLs concluída:")
    print(f"   Sucesso: {importador.sucesso}")
    print(f"   Duplicados: {importador.duplicado}")
    print(f"   Erros: {importador.erros}")
    
    # Verificar se há notas para processar
    if importador.sucesso == 0:
        print("\n⚠️ Nenhuma nota importada. Verifique os erros!")
        return
    
    # Aguardar 2 segundos
    print("\n⏳ Aguardando 2 segundos antes de processar...")
    time.sleep(2)
    
    # ETAPA 2: PROCESSAR STAGING
    processar_staging_nfe()
    
    # Tempo total
    tempo_total = time.time() - inicio_total
    
    print("\n" + "="*60)
    print("🎉 PROCESSO COMPLETO FINALIZADO!")
    print("="*60)
    print(f"⏱️ Tempo total: {tempo_total:.2f} segundos")
    print(f"🕐 Término: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
