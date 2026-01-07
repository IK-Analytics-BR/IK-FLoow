"""
Script para popular a tabela customer_products com dados das NF-e
Relaciona clientes com produtos comprados nas notas fiscais
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


def popular_customer_products(conn, modo='substituir'):
    """
    Popula tabela customer_products com dados das NF-e
    
    Args:
        conn: Conexão com o banco de dados
        modo: 'substituir' (limpa e repopula) ou 'adicionar' (apenas adiciona novos)
    """
    print("\n" + "="*80)
    print("POPULANDO TABELA CUSTOMER_PRODUCTS COM DADOS DAS NF-e")
    print("="*80)
    
    cursor = conn.cursor(dictionary=True)
    
    # 1. Limpar tabela (se modo = substituir)
    if modo == 'substituir':
        print("\n[1/5] Limpando tabela customer_products...")
        cursor.execute("DELETE FROM customer_products WHERE nfe_chave IS NOT NULL")
        deletados = cursor.rowcount
        conn.commit()
        print(f"✓ {deletados} registros de NF-e removidos")
    else:
        print("\n[1/5] Modo: adicionar novos registros")
    
    # 2. Buscar relacionamentos cliente-produto das NF-e
    print("\n[2/5] Buscando relacionamentos cliente-produto das NF-e...")
    
    query = """
        SELECT 
            -- Dados da nota
            n.id as nota_id,
            n.chave_acesso,
            n.numero_nota,
            n.data_emissao,
            n.dest_cnpj_cpf,
            
            -- Dados do item
            i.id as item_id,
            i.codigo_produto,
            i.codigo_ean,
            i.descricao,
            i.quantidade_comercial,
            i.valor_unitario_comercial,
            i.valor_total_produto,
            
            -- IDs das tabelas principais (se existirem)
            c.id as customer_id,
            c.name as customer_name,
            p.id as product_id,
            p.name as product_name
            
        FROM nfe_staging_notas n
        INNER JOIN nfe_staging_itens i ON i.nfe_staging_nota_id = n.id
        
        -- Tentar encontrar o cliente pelo CNPJ/CPF
        LEFT JOIN customers c ON (
            REPLACE(REPLACE(REPLACE(c.cnpj, '.', ''), '/', ''), '-', '') COLLATE utf8mb4_unicode_ci = n.dest_cnpj_cpf
            AND c.active = TRUE
        )
        
        -- Tentar encontrar o produto pelo código ou EAN
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
    
    cursor.execute(query)
    relacionamentos = cursor.fetchall()
    print(f"✓ Encontrados {len(relacionamentos)} relacionamentos cliente-produto nas NF-e")
    
    # 3. Estatísticas
    print("\n[3/5] Analisando dados...")
    
    total_com_cliente = sum(1 for r in relacionamentos if r['customer_id'])
    total_com_produto = sum(1 for r in relacionamentos if r['product_id'])
    total_completos = sum(1 for r in relacionamentos if r['customer_id'] and r['product_id'])
    
    print(f"   • Relacionamentos com cliente cadastrado: {total_com_cliente}")
    print(f"   • Relacionamentos com produto cadastrado: {total_com_produto}")
    print(f"   • Relacionamentos completos (cliente + produto): {total_completos}")
    
    if total_completos == 0:
        print("\n⚠️  ATENÇÃO: Nenhum relacionamento completo encontrado!")
        print("   Certifique-se de que:")
        print("   1. A tabela customers foi populada com os dados das NF-e")
        print("   2. A tabela products foi populada com os dados das NF-e")
        print("   3. Os códigos de produto batem entre as tabelas")
        cursor.close()
        return
    
    # 4. Inserir relacionamentos completos
    print(f"\n[4/5] Inserindo {total_completos} relacionamentos completos...")
    
    insert_query = """
        INSERT INTO customer_products (
            customer_id,
            product_id,
            quantity,
            unit_price,
            total_value,
            purchase_date,
            nfe_number,
            nfe_chave,
            notes,
            active,
            created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    
    importados = 0
    ignorados_sem_dados = 0
    ignorados_duplicados = 0
    erros = 0
    
    for rel in relacionamentos:
        # Pular se não tiver cliente ou produto
        if not rel['customer_id'] or not rel['product_id']:
            ignorados_sem_dados += 1
            continue
        
        try:
            # Verificar se já existe (evitar duplicação)
            if modo == 'adicionar':
                cursor.execute("""
                    SELECT id FROM customer_products 
                    WHERE customer_id = %s 
                      AND product_id = %s 
                      AND nfe_chave COLLATE utf8mb4_unicode_ci = %s
                """, (rel['customer_id'], rel['product_id'], rel['chave_acesso']))
                
                if cursor.fetchone():
                    ignorados_duplicados += 1
                    continue
            
            # Preparar dados
            quantity = float(rel['quantidade_comercial'] or 0)
            unit_price = float(rel['valor_unitario_comercial'] or 0)
            total_value = float(rel['valor_total_produto'] or 0)
            
            # Criar nota descritiva
            notes = f"NF-e {rel['numero_nota']} - {rel['descricao'][:100]}"
            
            # Inserir
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
                print(f"   {importados} relacionamentos processados...")
                
        except Exception as e:
            print(f"✗ Erro ao inserir relacionamento: {e}")
            print(f"   Cliente ID: {rel['customer_id']}, Produto ID: {rel['product_id']}")
            erros += 1
    
    conn.commit()
    
    # 5. Resumo
    print("\n[5/5] Resumo da importação:")
    print(f"   ✓ {importados} relacionamentos importados")
    print(f"   ⚠️  {ignorados_sem_dados} ignorados (sem cliente ou produto cadastrado)")
    
    if modo == 'adicionar':
        print(f"   ⚠️  {ignorados_duplicados} ignorados (duplicados)")
    
    if erros > 0:
        print(f"   ✗ {erros} erros")
    
    cursor.close()
    return importados, erros


def exibir_estatisticas(conn):
    """Exibe estatísticas da tabela customer_products"""
    print("\n" + "="*80)
    print("ESTATÍSTICAS - CUSTOMER_PRODUCTS")
    print("="*80)
    
    cursor = conn.cursor(dictionary=True)
    
    # Total de relacionamentos
    cursor.execute("SELECT COUNT(*) as total FROM customer_products")
    total = cursor.fetchone()['total']
    print(f"\n📊 Total de relacionamentos: {total}")
    
    # Total com dados de NF-e
    cursor.execute("""
        SELECT COUNT(*) as total 
        FROM customer_products 
        WHERE nfe_chave IS NOT NULL
    """)
    total_nfe = cursor.fetchone()['total']
    print(f"   • Relacionamentos de NF-e: {total_nfe}")
    
    # Valor total
    cursor.execute("""
        SELECT 
            SUM(total_value) as valor_total,
            SUM(quantity) as quantidade_total
        FROM customer_products
        WHERE nfe_chave IS NOT NULL
    """)
    totais = cursor.fetchone()
    if totais and totais['valor_total']:
        print(f"   • Valor total das compras: R$ {totais['valor_total']:,.2f}")
        print(f"   • Quantidade total de itens: {totais['quantidade_total']:,.2f}")
    
    # Top 5 clientes que mais compraram
    print("\n🏆 TOP 5 CLIENTES QUE MAIS COMPRARAM:")
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
        print(f"      • {row['qtd_notas']} nota(s) - R$ {row['valor_total']:,.2f}")
    
    # Top 5 produtos mais vendidos
    print("\n📦 TOP 5 PRODUTOS MAIS VENDIDOS:")
    cursor.execute("""
        SELECT 
            p.name,
            COUNT(*) as qtd_vendas,
            SUM(cp.quantity) as qtd_total,
            SUM(cp.total_value) as valor_total
        FROM customer_products cp
        INNER JOIN products p ON p.id = cp.product_id
        WHERE cp.nfe_chave IS NOT NULL
        GROUP BY cp.product_id, p.name
        ORDER BY qtd_vendas DESC
        LIMIT 5
    """)
    
    for i, row in enumerate(cursor.fetchall(), 1):
        print(f"   {i}. {row['name'][:50]}")
        print(f"      • {row['qtd_vendas']} venda(s) - {row['qtd_total']:,.2f} un - R$ {row['valor_total']:,.2f}")
    
    cursor.close()


def main():
    """Função principal"""
    print("\n" + "="*80)
    print("POPULAR CUSTOMER_PRODUCTS COM DADOS DAS NF-e")
    print("="*80)
    print(f"\nConectando ao banco: {DB_NAME}@{DB_HOST}")
    
    try:
        # Conectar ao banco
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        print("✓ Conectado com sucesso\n")
        
        # Perguntar modo de operação
        print("Modo de operação:")
        print("1. Substituir (limpa relacionamentos de NF-e e repopula)")
        print("2. Adicionar (mantém existentes e adiciona novos)")
        escolha = input("\nEscolha uma opção (1 ou 2): ").strip()
        
        modo = 'substituir' if escolha == '1' else 'adicionar'
        
        # Executar população
        importados, erros = popular_customer_products(conn, modo)
        
        # Estatísticas
        if importados > 0:
            exibir_estatisticas(conn)
        
        # Fechar conexão
        conn.close()
        
        print("\n" + "="*80)
        print("✓ PROCESSAMENTO CONCLUÍDO!")
        print("="*80)
        print(f"\nResumo:")
        print(f"   Relacionamentos importados: {importados}")
        print(f"   Erros: {erros}")
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
