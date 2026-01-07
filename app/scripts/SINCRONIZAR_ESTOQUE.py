# -*- coding: utf-8 -*-
"""
Sincronizar current_stock com products.stock_quantity
"""
import sys
sys.path.insert(0, 'c:/Users/arita/CascadeProjects/SupplyChainSystem')

from app.database import Database

def main():
    db = Database()
    
    print("=" * 80)
    print("SINCRONIZANDO ESTOQUE: products.stock_quantity -> current_stock")
    print("=" * 80)
    
    # 1. Contar produtos com estoque
    prods = db.fetch_one("SELECT COUNT(*) as cnt FROM products WHERE stock_quantity > 0")
    print(f"\nProdutos com estoque > 0: {prods['cnt']}")
    
    # 2. Atualizar current_stock para produtos que já existem
    print("\n1. Atualizando registros existentes em current_stock...")
    result = db.execute("""
        UPDATE current_stock cs
        INNER JOIN products p ON p.id = cs.product_id
        SET cs.quantity = p.stock_quantity,
            cs.updated_at = NOW()
    """)
    print(f"   Registros atualizados")
    
    # 3. Inserir produtos que não estão em current_stock
    print("\n2. Inserindo produtos faltantes em current_stock...")
    db.execute("""
        INSERT INTO current_stock (product_id, location_id, quantity, created_at, updated_at)
        SELECT p.id, 1, p.stock_quantity, NOW(), NOW()
        FROM products p
        WHERE p.stock_quantity > 0
          AND NOT EXISTS (SELECT 1 FROM current_stock cs WHERE cs.product_id = p.id)
    """)
    print(f"   Registros inseridos")
    
    # 4. Verificar sincronização
    print("\n3. Verificando sincronizacao...")
    diff = db.fetch_all("""
        SELECT 
            p.id, p.name, p.stock_quantity AS estoque_products,
            cs.quantity AS estoque_current_stock
        FROM products p
        LEFT JOIN current_stock cs ON cs.product_id = p.id
        WHERE COALESCE(p.stock_quantity, 0) != COALESCE(cs.quantity, 0)
        AND p.stock_quantity > 0
        LIMIT 5
    """)
    
    if diff:
        print(f"   [AVISO] Ainda existem {len(diff)} divergencias")
        for d in diff:
            print(f"      Produto {d['id']}: products={d['estoque_products']} vs current_stock={d['estoque_current_stock']}")
    else:
        print("   [OK] Todas as quantidades sincronizadas!")
    
    # 5. Resumo final
    print("\n" + "=" * 80)
    print("SINCRONIZACAO CONCLUIDA!")
    print("=" * 80)

if __name__ == "__main__":
    main()
