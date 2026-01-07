# -*- coding: utf-8 -*-
"""
Verificar consistência de estoque entre tabelas
"""
import sys
sys.path.insert(0, 'c:/Users/arita/CascadeProjects/SupplyChainSystem')

from app.database import Database

def main():
    db = Database()
    
    print("=" * 80)
    print("VERIFICACAO DE CONSISTENCIA DE ESTOQUE")
    print("=" * 80)
    
    # 1. Verificar se current_stock existe e tem dados
    print("\n1. Tabela current_stock:")
    try:
        cnt = db.fetch_one("SELECT COUNT(*) as cnt FROM current_stock")
        print(f"   Registros: {cnt['cnt']}")
        
        # Comparar com products
        diff = db.fetch_all("""
            SELECT 
                p.id, p.name, p.stock_quantity AS estoque_products,
                cs.quantity AS estoque_current_stock
            FROM products p
            LEFT JOIN current_stock cs ON cs.product_id = p.id
            WHERE COALESCE(p.stock_quantity, 0) != COALESCE(cs.quantity, 0)
            AND p.stock_quantity > 0
            LIMIT 10
        """)
        
        if diff:
            print(f"\n   DIVERGENCIAS ENCONTRADAS ({len(diff)} exemplos):")
            for d in diff:
                print(f"      Produto {d['id']}: products={d['estoque_products']} vs current_stock={d['estoque_current_stock']}")
        else:
            print("   [OK] Sem divergencias")
            
    except Exception as e:
        print(f"   [ERRO] {e}")
    
    # 2. Verificar produtos com estoque em products
    print("\n2. Tabela products (stock_quantity):")
    prods_estoque = db.fetch_one("SELECT COUNT(*) as cnt FROM products WHERE stock_quantity > 0")
    print(f"   Produtos com estoque > 0: {prods_estoque['cnt']}")
    
    # 3. Mostrar alguns exemplos
    print("\n3. Ultimos 5 produtos com estoque:")
    exemplos = db.fetch_all("""
        SELECT id, name, stock_quantity 
        FROM products 
        WHERE stock_quantity > 0 
        ORDER BY id DESC 
        LIMIT 5
    """)
    for e in exemplos:
        print(f"   ID={e['id']}: {e['stock_quantity']} - {e['name'][:50]}")
    
    # 4. Verificar estoque_reservas
    print("\n4. Tabela estoque_reservas:")
    res = db.fetch_one("SELECT COUNT(*) as cnt, COALESCE(SUM(quantidade), 0) as total FROM estoque_reservas WHERE status IN ('ativo', 'confirmado')")
    print(f"   Reservas ativas: {res['cnt']}")
    print(f"   Total reservado: {res['total']}")
    
    # 5. Verificar estoque_movimentacoes
    print("\n5. Tabela estoque_movimentacoes:")
    try:
        mov = db.fetch_one("SELECT COUNT(*) as cnt FROM estoque_movimentacoes")
        print(f"   Movimentacoes: {mov['cnt']}")
    except:
        print("   [NAO EXISTE ou VAZIA]")

if __name__ == "__main__":
    main()
