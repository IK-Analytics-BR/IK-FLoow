"""
Script para popular customer_products - VERSÃO AUTOMÁTICA (sem input)
Executa em modo 'substituir' automaticamente
"""

import os
import sys
import mysql.connector
from dotenv import load_dotenv
from datetime import datetime

# Configurar encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Adicionar o diretório pai ao caminho de importação
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco de dados
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'supply_chain_system')


def popular_customer_products(conn):
    """Popula tabela customer_products com dados das NF-e"""
    print("\n" + "="*80)
    print("POPULANDO CUSTOMER_PRODUCTS")
    print("="*80)
    
    cursor = conn.cursor(dictionary=True)
    
    # 1. Limpar
    print("\n[1/5] Limpando dados de NF-e...")
    cursor.execute("DELETE FROM customer_products WHERE nfe_chave IS NOT NULL")
    deletados = cursor.rowcount
    conn.commit()
    print(f"   ✓ {deletados} registros removidos")
    
    # 2. Buscar dados
    print("\n[2/5] Buscando relacionamentos das NF-e...")
    
    query = """
        SELECT 
            n.id as nota_id,
            n.chave_acesso,
            n.numero_nota,
            n.data_emissao,
            i.quantidade_comercial,
            i.valor_unitario_comercial,
            i.valor_total_produto,
            i.descricao,
            c.id as customer_id,
            c.name as customer_name,
            p.id as product_id,
            p.name as product_name
            
        FROM nfe_staging_notas n
        INNER JOIN nfe_staging_itens i ON i.nfe_staging_nota_id = n.id
        LEFT JOIN customers c ON (
            REPLACE(REPLACE(REPLACE(c.cnpj, '.', ''), '/', ''), '-', '') COLLATE utf8mb4_unicode_ci = n.dest_cnpj_cpf
            AND c.active = TRUE
        )
        LEFT JOIN products p ON (
            (p.supplier_code COLLATE utf8mb4_unicode_ci = i.codigo_produto 
             OR p.barcode COLLATE utf8mb4_unicode_ci = i.codigo_ean)
            AND p.active = TRUE
        )
        
        WHERE n.dest_cnpj_cpf IS NOT NULL
          AND i.codigo_produto IS NOT NULL
          AND i.descricao IS NOT NULL
        
        ORDER BY n.data_emissao DESC, n.numero_nota, i.numero_item
    """
    
    print("   Executando query...")
    cursor.execute(query)
    print("   Buscando resultados...")
    relacionamentos = cursor.fetchall()
    print(f"   ✓ {len(relacionamentos)} relacionamentos encontrados")
    
    # 3. Estatísticas
    print("\n[3/5] Analisando dados...")
    
    total_com_cliente = sum(1 for r in relacionamentos if r['customer_id'])
    total_com_produto = sum(1 for r in relacionamentos if r['product_id'])
    total_completos = sum(1 for r in relacionamentos if r['customer_id'] and r['product_id'])
    
    print(f"   • Com cliente cadastrado: {total_com_cliente}")
    print(f"   • Com produto cadastrado: {total_com_produto}")
    print(f"   • Completos (cliente + produto): {total_completos}")
    
    if total_completos == 0:
        print("\n⚠️ ATENÇÃO: Nenhum relacionamento completo!")
        print("   Execute primeiro: python popular_dados_nfe_CORRIGIDO.py")
        cursor.close()
        return 0, 0
    
    # 4. Inserir
    print(f"\n[4/5] Inserindo {total_completos} relacionamentos...")
    
    insert_query = """
        INSERT INTO customer_products (
            customer_id, product_id, quantity, unit_price, total_value,
            purchase_date, nfe_number, nfe_chave, notes, active, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    
    importados = 0
    ignorados = 0
    erros = 0
    
    for rel in relacionamentos:
        if not rel['customer_id'] or not rel['product_id']:
            ignorados += 1
            continue
        
        try:
            quantity = float(rel['quantidade_comercial'] or 0)
            unit_price = float(rel['valor_unitario_comercial'] or 0)
            total_value = float(rel['valor_total_produto'] or 0)
            
            notes = f"NF-e {rel['numero_nota']} - {rel['descricao'][:100]}"
            
            cursor.execute(insert_query, (
                rel['customer_id'],
                rel['product_id'],
                quantity,
                unit_price,
                total_value,
                rel['data_emissao'],
                rel['numero_nota'],
                rel['chave_acesso'],
                notes,
                True,
                datetime.now()
            ))
            
            importados += 1
            
            if importados % 100 == 0:
                conn.commit()
                print(f"   Processados: {importados}/{total_completos}")
                
        except Exception as e:
            print(f"   ✗ Erro: {e}")
            erros += 1
    
    conn.commit()
    
    # 5. Resumo
    print("\n[5/5] Resumo:")
    print(f"   ✓ Importados: {importados}")
    print(f"   ⚠️ Ignorados: {ignorados}")
    if erros > 0:
        print(f"   ✗ Erros: {erros}")
    
    cursor.close()
    return importados, erros


def exibir_estatisticas(conn):
    """Exibe estatísticas"""
    print("\n" + "="*80)
    print("ESTATÍSTICAS")
    print("="*80)
    
    cursor = conn.cursor(dictionary=True)
    
    # Total
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT customer_id) as clientes,
            COUNT(DISTINCT product_id) as produtos,
            SUM(total_value) as valor_total
        FROM customer_products
        WHERE nfe_chave IS NOT NULL
    """)
    totais = cursor.fetchone()
    
    print(f"\n📊 Total: {totais['total']} relacionamentos")
    print(f"   • Clientes: {totais['clientes']}")
    print(f"   • Produtos: {totais['produtos']}")
    if totais['valor_total']:
        print(f"   • Valor total: R$ {totais['valor_total']:,.2f}")
    
    # Top 5 clientes
    print("\n🏆 TOP 5 CLIENTES:")
    cursor.execute("""
        SELECT 
            c.name,
            COUNT(DISTINCT cp.nfe_chave) as qtd_notas,
            SUM(cp.total_value) as valor_total
        FROM customer_products cp
        INNER JOIN customers c ON c.id = cp.customer_id
        WHERE cp.nfe_chave IS NOT NULL
        GROUP BY cp.customer_id, c.name
        ORDER BY valor_total DESC
        LIMIT 5
    """)
    
    for i, row in enumerate(cursor.fetchall(), 1):
        print(f"   {i}. {row['name'][:50]}")
        print(f"      {row['qtd_notas']} notas - R$ {row['valor_total']:,.2f}")
    
    cursor.close()


def main():
    """Função principal"""
    print("\n" + "="*80)
    print("POPULAR CUSTOMER_PRODUCTS - VERSÃO AUTOMÁTICA")
    print("="*80)
    print(f"\nConectando ao banco: {DB_NAME}@{DB_HOST}")
    
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        print("✓ Conectado\n")
        
        # Executar em modo substituir
        importados, erros = popular_customer_products(conn)
        
        # Estatísticas
        if importados > 0:
            exibir_estatisticas(conn)
        
        conn.close()
        
        print("\n" + "="*80)
        print("✓ CONCLUÍDO!")
        print("="*80)
        print(f"\nImportados: {importados}")
        print(f"Erros: {erros}")
        print(f"\nData/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
    except mysql.connector.Error as err:
        print(f"\n✗ ERRO DE CONEXÃO: {err}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
