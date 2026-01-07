# -*- coding: utf-8 -*-
"""
Diagnostico: Por que OP nao foi criada para ORC-2025-0026?
"""
import sys
sys.path.insert(0, 'c:/Users/arita/CascadeProjects/SupplyChainSystem')

from app.database import Database

def main():
    db = Database()
    
    print("=== DIAGNOSTICO ORC-2025-0026 ===\n")
    
    # 1. Buscar orcamento
    orc = db.fetch_one("""
        SELECT * FROM orcamentos WHERE numero = 'ORC-2025-0026'
    """)
    print(f"1. Orcamento: ID={orc['id']}, Status={orc['status']}")
    
    # 2. Buscar itens do orcamento
    itens = db.fetch_all("""
        SELECT 
            oi.*,
            p.name AS produto_nome,
            p.category_id,
            pc.name AS categoria_nome,
            pc.categoria_fiscal
        FROM orcamento_itens oi
        JOIN products p ON p.id = oi.produto_id
        LEFT JOIN product_categories pc ON pc.id = p.category_id
        WHERE oi.orcamento_id = %s
    """, (orc['id'],))
    
    print(f"\n2. Itens do orcamento ({len(itens)}):")
    for item in itens:
        print(f"   - Produto: {item['produto_nome']}")
        print(f"     produto_id: {item['produto_id']}")
        print(f"     quantidade: {item['quantidade']}")
        print(f"     category_id: {item['category_id']}")
        print(f"     categoria_nome: {item['categoria_nome']}")
        print(f"     categoria_fiscal: {item['categoria_fiscal']}")
        print(f"     status_alocacao: {item.get('status_alocacao')}")
        print()
    
    # 3. Verificar se ja existe vinculo com OP
    vinculos = db.fetch_all("""
        SELECT * FROM orcamento_op_itens WHERE orcamento_id = %s
    """, (orc['id'],))
    print(f"3. Vinculos orcamento_op_itens: {len(vinculos)}")
    for v in vinculos:
        print(f"   {v}")
    
    # 4. Verificar OPs do orcamento
    ops = db.fetch_all("""
        SELECT * FROM ordens_producao WHERE orcamento_id = %s
    """, (orc['id'],))
    print(f"\n4. OPs vinculadas ao orcamento: {len(ops)}")
    for op in ops:
        print(f"   OP #{op['id']}: {op.get('numero_op')} - Status: {op['status']} - Tipo: {op.get('tipo_op')}")
    
    # 5. Verificar grupo de OPs
    grupo = db.fetch_one("""
        SELECT * FROM orcamento_op_grupos WHERE orcamento_id = %s
    """, (orc['id'],))
    print(f"\n5. Grupo OP: {grupo}")
    
    # 6. Verificar estoque do produto
    if itens:
        prod_id = itens[0]['produto_id']
        estoque = db.fetch_one("""
            SELECT 
                p.id,
                p.name,
                p.stock_quantity,
                pet.codigo_dna,
                pet.tipo_correia_id,
                pet.material_base_id
            FROM products p
            LEFT JOIN produto_especificacoes_tecnicas pet ON pet.produto_id = p.id
            WHERE p.id = %s
        """, (prod_id,))
        print(f"\n6. Estoque do produto {prod_id}:")
        print(f"   stock_quantity: {estoque.get('stock_quantity')}")
        print(f"   codigo_dna: {estoque.get('codigo_dna')}")
        print(f"   tipo_correia_id: {estoque.get('tipo_correia_id')}")
        print(f"   material_base_id: {estoque.get('material_base_id')}")
    
    print("\n=== FIM DIAGNOSTICO ===")

if __name__ == "__main__":
    main()
