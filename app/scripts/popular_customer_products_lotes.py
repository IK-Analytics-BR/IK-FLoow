"""
Script para popular customer_products em LOTES PEQUENOS
Processa 1000 registros por vez para evitar timeout
"""

import os
import sys
import mysql.connector
from dotenv import load_dotenv
from datetime import datetime
import time

# Configurar encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Adicionar o diretório pai ao caminho de importação
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'supply_chain_system')

BATCH_SIZE = 1000  # Processar 1000 por vez


def limpar_dados(conn):
    """Limpa dados existentes de NF-e"""
    print("\n[1/4] Limpando dados de NF-e existentes...")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customer_products WHERE nfe_chave IS NOT NULL")
    deletados = cursor.rowcount
    conn.commit()
    cursor.close()
    print(f"   ✓ {deletados} registros removidos")


def contar_total(conn):
    """Conta quantos registros serão processados"""
    print("\n[2/4] Contando registros a processar...")
    cursor = conn.cursor()
    
    query = """
        SELECT COUNT(*) as total
        FROM nfe_staging_notas n
        INNER JOIN nfe_staging_itens i ON i.nfe_staging_nota_id = n.id
        INNER JOIN customers c ON (
            REPLACE(REPLACE(REPLACE(c.cnpj, '.', ''), '/', ''), '-', '') COLLATE utf8mb4_unicode_ci = n.dest_cnpj_cpf
            AND c.active = TRUE
        )
        INNER JOIN products p ON (
            (p.supplier_code COLLATE utf8mb4_unicode_ci = i.codigo_produto 
             OR p.barcode COLLATE utf8mb4_unicode_ci = i.codigo_ean)
            AND p.active = TRUE
        )
        WHERE n.dest_cnpj_cpf IS NOT NULL
          AND i.codigo_produto IS NOT NULL
          AND i.descricao IS NOT NULL
    """
    
    cursor.execute(query)
    total = cursor.fetchone()[0]
    cursor.close()
    
    print(f"   ✓ Total a processar: {total:,} registros")
    return total


def processar_lote(conn, offset, limit):
    """Processa um lote de registros"""
    cursor = conn.cursor(dictionary=True)
    
    # Buscar lote
    query = """
        SELECT 
            c.id as customer_id,
            p.id as product_id,
            i.quantidade_comercial as quantity,
            i.valor_unitario_comercial as unit_price,
            i.valor_total_produto as total_value,
            n.data_emissao as purchase_date,
            n.numero_nota as nfe_number,
            n.chave_acesso as nfe_chave,
            CONCAT('NF-e ', n.numero_nota, ' - ', LEFT(i.descricao, 100)) as notes
        FROM nfe_staging_notas n
        INNER JOIN nfe_staging_itens i ON i.nfe_staging_nota_id = n.id
        INNER JOIN customers c ON (
            REPLACE(REPLACE(REPLACE(c.cnpj, '.', ''), '/', ''), '-', '') COLLATE utf8mb4_unicode_ci = n.dest_cnpj_cpf
            AND c.active = TRUE
        )
        INNER JOIN products p ON (
            (p.supplier_code COLLATE utf8mb4_unicode_ci = i.codigo_produto 
             OR p.barcode COLLATE utf8mb4_unicode_ci = i.codigo_ean)
            AND p.active = TRUE
        )
        WHERE n.dest_cnpj_cpf IS NOT NULL
          AND i.codigo_produto IS NOT NULL
          AND i.descricao IS NOT NULL
        LIMIT %s OFFSET %s
    """
    
    cursor.execute(query, (limit, offset))
    registros = cursor.fetchall()
    
    if not registros:
        cursor.close()
        return 0
    
    # Inserir lote
    insert_query = """
        INSERT INTO customer_products (
            customer_id, product_id, quantity, unit_price, total_value,
            purchase_date, nfe_number, nfe_chave, notes, active, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    
    inseridos = 0
    for reg in registros:
        try:
            cursor.execute(insert_query, (
                reg['customer_id'],
                reg['product_id'],
                float(reg['quantity'] or 0),
                float(reg['unit_price'] or 0),
                float(reg['total_value'] or 0),
                reg['purchase_date'],
                reg['nfe_number'],
                reg['nfe_chave'],
                reg['notes'],
                True,
                datetime.now()
            ))
            inseridos += 1
        except Exception as e:
            print(f"   ✗ Erro: {e}")
    
    conn.commit()
    cursor.close()
    return inseridos


def popular_em_lotes(conn, total):
    """Popula em lotes pequenos"""
    print(f"\n[3/4] Processando em lotes de {BATCH_SIZE}...")
    print(f"   Total de lotes: {(total // BATCH_SIZE) + 1}")
    
    offset = 0
    total_inserido = 0
    inicio = time.time()
    
    while offset < total:
        lote_num = (offset // BATCH_SIZE) + 1
        total_lotes = (total // BATCH_SIZE) + 1
        
        print(f"\n   Lote {lote_num}/{total_lotes} (offset {offset:,})...")
        
        inseridos = processar_lote(conn, offset, BATCH_SIZE)
        total_inserido += inseridos
        
        # Progresso
        percentual = (total_inserido / total) * 100
        tempo_decorrido = time.time() - inicio
        velocidade = total_inserido / tempo_decorrido if tempo_decorrido > 0 else 0
        tempo_restante = (total - total_inserido) / velocidade if velocidade > 0 else 0
        
        print(f"   ✓ {inseridos} inseridos")
        print(f"   Progresso: {total_inserido:,}/{total:,} ({percentual:.1f}%)")
        print(f"   Velocidade: {velocidade:.0f} reg/s")
        print(f"   Tempo estimado restante: {tempo_restante/60:.1f} min")
        
        offset += BATCH_SIZE
        
        # Pequena pausa para não sobrecarregar
        time.sleep(0.1)
    
    tempo_total = time.time() - inicio
    print(f"\n   ✓ Concluído em {tempo_total/60:.1f} minutos")
    return total_inserido


def exibir_estatisticas(conn):
    """Exibe estatísticas finais"""
    print("\n[4/4] Estatísticas finais...")
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT customer_id) as clientes,
            COUNT(DISTINCT product_id) as produtos,
            ROUND(SUM(total_value), 2) as valor_total
        FROM customer_products
        WHERE nfe_chave IS NOT NULL
    """)
    stats = cursor.fetchone()
    
    print(f"\n📊 Total: {stats['total']:,} relacionamentos")
    print(f"   • Clientes: {stats['clientes']:,}")
    print(f"   • Produtos: {stats['produtos']:,}")
    if stats['valor_total']:
        print(f"   • Valor: R$ {stats['valor_total']:,.2f}")
    
    cursor.close()


def main():
    """Função principal"""
    print("\n" + "="*80)
    print("POPULAR CUSTOMER_PRODUCTS EM LOTES")
    print("="*80)
    print(f"\nBanco: {DB_NAME}@{DB_HOST}")
    print(f"Tamanho do lote: {BATCH_SIZE:,} registros")
    
    try:
        # Conectar
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            autocommit=False
        )
        print("✓ Conectado\n")
        
        # Processar
        limpar_dados(conn)
        total = contar_total(conn)
        
        if total == 0:
            print("\n⚠️ Nenhum registro a processar!")
            conn.close()
            return
        
        total_inserido = popular_em_lotes(conn, total)
        exibir_estatisticas(conn)
        
        conn.close()
        
        print("\n" + "="*80)
        print("✓ CONCLUÍDO COM SUCESSO!")
        print("="*80)
        print(f"\nTotal inserido: {total_inserido:,}")
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
    except mysql.connector.Error as err:
        print(f"\n✗ ERRO: {err}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
