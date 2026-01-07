"""
Script para verificar e corrigir especificações técnicas DNA
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.database import Database

def main():
    db = Database()
    
    print("=" * 70)
    print("VERIFICAR ESPECIFICAÇÕES TÉCNICAS E ESTOQUE")
    print("=" * 70)
    
    # 1. Ver produtos com especificações e estoque
    produtos = db.fetch_all("""
        SELECT 
            p.id, p.name, p.stock_quantity,
            pet.codigo_dna, pet.largura_mm, pet.comprimento_mm,
            pet.tipo_correia_id, pet.material_base_id
        FROM products p
        INNER JOIN produto_especificacoes_tecnicas pet ON pet.produto_id = p.id
        WHERE p.stock_quantity > 0
        ORDER BY p.id
        LIMIT 20
    """)
    
    print(f"\n1. PRODUTOS COM ESPECIFICAÇÃO E ESTOQUE ({len(produtos)}):")
    print("-" * 70)
    for p in produtos:
        print(f"  #{p['id']:4} | Est: {p['stock_quantity']:3} | DNA: {p['codigo_dna']}")
        print(f"         L={p['largura_mm']}mm C={p['comprimento_mm']}mm | Tipo:{p['tipo_correia_id']} Mat:{p['material_base_id']}")
        print(f"         {p['name'][:60]}")
        print()
    
    # 2. Verificar produto específico (T10 2080X50MM)
    print("\n2. BUSCAR PRODUTO T10 2080X50MM:")
    print("-" * 70)
    prod_teste = db.fetch_one("""
        SELECT p.id, p.name, pet.codigo_dna, pet.largura_mm, pet.comprimento_mm, 
               pet.tipo_correia_id, pet.material_base_id, p.stock_quantity
        FROM products p
        LEFT JOIN produto_especificacoes_tecnicas pet ON pet.produto_id = p.id
        WHERE p.name LIKE '%T10%2080%' OR p.name LIKE '%2080%T10%'
    """)
    
    if prod_teste:
        print(f"  Encontrado: #{prod_teste['id']} - {prod_teste['name']}")
        print(f"  DNA: {prod_teste['codigo_dna']}")
        print(f"  Dimensões: L={prod_teste['largura_mm']} C={prod_teste['comprimento_mm']}")
        print(f"  Tipo/Material: {prod_teste['tipo_correia_id']} / {prod_teste['material_base_id']}")
        print(f"  Estoque: {prod_teste['stock_quantity']}")
    else:
        print("  Produto não encontrado. Buscando produtos T10...")
        prods_t10 = db.fetch_all("""
            SELECT p.id, p.name, pet.codigo_dna, pet.largura_mm, pet.comprimento_mm
            FROM products p
            LEFT JOIN produto_especificacoes_tecnicas pet ON pet.produto_id = p.id
            WHERE p.name LIKE '%T10%'
            LIMIT 10
        """)
        for pt in prods_t10:
            has_esp = "✓" if pt['codigo_dna'] else "✗"
            print(f"  {has_esp} #{pt['id']}: {pt['name'][:50]} | DNA: {pt['codigo_dna']}")
    
    # 3. Estatísticas gerais
    print("\n3. ESTATÍSTICAS:")
    print("-" * 70)
    stats = db.fetch_one("""
        SELECT 
            (SELECT COUNT(*) FROM products WHERE stock_quantity > 0) as produtos_com_estoque,
            (SELECT COUNT(*) FROM produto_especificacoes_tecnicas) as total_especificacoes,
            (SELECT COUNT(*) FROM produto_especificacoes_tecnicas WHERE tipo_correia_id IS NOT NULL) as com_tipo,
            (SELECT COUNT(*) FROM produto_especificacoes_tecnicas WHERE material_base_id IS NOT NULL) as com_material,
            (SELECT COUNT(*) FROM produto_especificacoes_tecnicas WHERE largura_mm IS NOT NULL) as com_largura,
            (SELECT COUNT(*) FROM produto_especificacoes_tecnicas WHERE comprimento_mm IS NOT NULL) as com_comprimento
    """)
    print(f"  Produtos com estoque > 0: {stats['produtos_com_estoque']}")
    print(f"  Total especificações: {stats['total_especificacoes']}")
    print(f"  Com tipo correia: {stats['com_tipo']}")
    print(f"  Com material: {stats['com_material']}")
    print(f"  Com largura: {stats['com_largura']}")
    print(f"  Com comprimento: {stats['com_comprimento']}")
    
    # 4. Exemplo de busca similar (simular API)
    print("\n4. SIMULAR BUSCA DNA SIMILAR:")
    print("-" * 70)
    
    # Pegar um produto com especificação completa
    prod_ref = db.fetch_one("""
        SELECT p.id, p.name, pet.codigo_dna, pet.largura_mm, pet.comprimento_mm,
               pet.tipo_correia_id, pet.material_base_id
        FROM products p
        INNER JOIN produto_especificacoes_tecnicas pet ON pet.produto_id = p.id
        WHERE pet.tipo_correia_id IS NOT NULL 
          AND pet.material_base_id IS NOT NULL
          AND pet.largura_mm IS NOT NULL
        LIMIT 1
    """)
    
    if prod_ref:
        print(f"  Produto referência: #{prod_ref['id']} - {prod_ref['name'][:50]}")
        print(f"  DNA: {prod_ref['codigo_dna']}")
        print(f"  Dimensões: L={prod_ref['largura_mm']} C={prod_ref['comprimento_mm']}")
        print(f"  Tipo={prod_ref['tipo_correia_id']} Material={prod_ref['material_base_id']}")
        
        # Buscar similares
        similares = db.fetch_all("""
            SELECT p.id, p.name, p.stock_quantity, pet.codigo_dna, 
                   pet.largura_mm, pet.comprimento_mm
            FROM products p
            INNER JOIN produto_especificacoes_tecnicas pet ON pet.produto_id = p.id
            WHERE p.id != %s
              AND p.stock_quantity > 0
              AND (
                  pet.tipo_correia_id = %s
                  OR pet.material_base_id = %s
                  OR (pet.largura_mm >= %s AND pet.comprimento_mm >= %s)
              )
            ORDER BY 
                CASE WHEN pet.tipo_correia_id = %s AND pet.material_base_id = %s THEN 1 ELSE 2 END,
                pet.largura_mm DESC
            LIMIT 10
        """, (
            prod_ref['id'],
            prod_ref['tipo_correia_id'],
            prod_ref['material_base_id'],
            prod_ref['largura_mm'] or 0,
            prod_ref['comprimento_mm'] or 0,
            prod_ref['tipo_correia_id'],
            prod_ref['material_base_id']
        ))
        
        print(f"\n  Encontrados {len(similares)} produtos similares:")
        for s in similares:
            print(f"    #{s['id']:4} | Est: {s['stock_quantity']:3} | L={s['largura_mm']} C={s['comprimento_mm']}")
            print(f"           DNA: {s['codigo_dna']}")
            print(f"           {s['name'][:55]}")
    else:
        print("  Nenhum produto com especificação completa encontrado")


if __name__ == "__main__":
    main()
