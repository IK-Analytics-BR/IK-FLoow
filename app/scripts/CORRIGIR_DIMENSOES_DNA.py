"""
Script para corrigir dimensoes nas especificacoes tecnicas existentes
e adicionar estoque para teste
"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.database import Database

def extrair_dimensoes(nome):
    """Extrai largura e comprimento do nome do produto"""
    nome_upper = nome.upper()
    largura = None
    comprimento = None
    
    # Padrao: XXXXxYYmm ou XXXX X YY MM
    match = re.search(r'(\d+)\s*[Xx]\s*(\d+)\s*MM', nome_upper)
    if match:
        # Geralmente primeiro numero maior eh comprimento
        n1, n2 = int(match.group(1)), int(match.group(2))
        if n1 > n2:
            comprimento, largura = n1, n2
        else:
            largura, comprimento = n1, n2
        return largura, comprimento
    
    # Padrao: XXXX X YY (sem MM)
    match = re.search(r'(\d{3,})\s*[Xx]\s*(\d{2,})', nome)
    if match:
        n1, n2 = int(match.group(1)), int(match.group(2))
        if n1 > n2:
            comprimento, largura = n1, n2
        else:
            largura, comprimento = n1, n2
        return largura, comprimento
    
    return largura, comprimento

def main():
    db = Database()
    
    print("=" * 70)
    print("CORRIGIR DIMENSOES NAS ESPECIFICACOES TECNICAS")
    print("=" * 70)
    
    # 1. Buscar especificacoes sem dimensoes
    print("\n1. Buscando especificacoes sem dimensoes...")
    sem_dim = db.fetch_all("""
        SELECT pet.id, pet.produto_id, p.name, pet.codigo_dna,
               pet.largura_mm, pet.comprimento_mm
        FROM produto_especificacoes_tecnicas pet
        INNER JOIN products p ON p.id = pet.produto_id
        WHERE pet.largura_mm IS NULL OR pet.comprimento_mm IS NULL
        LIMIT 50
    """)
    
    print(f"   Encontradas {len(sem_dim)} especificacoes sem dimensoes")
    
    atualizadas = 0
    for esp in sem_dim:
        largura, comprimento = extrair_dimensoes(esp['name'])
        if largura or comprimento:
            db.execute("""
                UPDATE produto_especificacoes_tecnicas 
                SET largura_mm = COALESCE(largura_mm, %s),
                    comprimento_mm = COALESCE(comprimento_mm, %s),
                    codigo_dna = CONCAT(
                        SUBSTRING_INDEX(codigo_dna, '-', 3),
                        CASE WHEN %s IS NOT NULL THEN CONCAT('-L', %s) ELSE '' END,
                        CASE WHEN %s IS NOT NULL THEN CONCAT('-C', %s) ELSE '' END
                    )
                WHERE id = %s
            """, (largura, comprimento, largura, largura, comprimento, comprimento, esp['id']))
            atualizadas += 1
            print(f"   [OK] #{esp['produto_id']}: L={largura} C={comprimento} - {esp['name'][:40]}")
    
    print(f"\n   Total atualizadas: {atualizadas}")
    
    # 2. Atualizar produto especifico T10 2080X50MM
    print("\n2. Atualizando produto T10 2080X50MM...")
    db.execute("""
        UPDATE produto_especificacoes_tecnicas pet
        INNER JOIN products p ON p.id = pet.produto_id
        SET pet.largura_mm = 50, 
            pet.comprimento_mm = 2080,
            pet.codigo_dna = 'SIN-PU-T10-L50-C2080'
        WHERE p.name LIKE '%T10%2080%50%' OR p.name LIKE '%2080%50%T10%'
    """)
    print("   [OK] Dimensoes atualizadas: L=50mm C=2080mm")
    
    # 3. Adicionar estoque para todos produtos com especificacao
    print("\n3. Adicionando estoque (10-60 unidades)...")
    db.execute("""
        UPDATE products p
        INNER JOIN produto_especificacoes_tecnicas pet ON pet.produto_id = p.id
        SET p.stock_quantity = FLOOR(RAND() * 50) + 10
        WHERE p.stock_quantity IS NULL OR p.stock_quantity <= 0
    """)
    
    # Contar atualizados
    qtd = db.fetch_one("""
        SELECT COUNT(*) as total 
        FROM products p 
        INNER JOIN produto_especificacoes_tecnicas pet ON pet.produto_id = p.id
        WHERE p.stock_quantity > 0
    """)
    print(f"   [OK] {qtd['total']} produtos com estoque")
    
    # 4. Verificar resultado
    print("\n4. Verificando produto de teste...")
    prod = db.fetch_one("""
        SELECT p.id, p.name, p.stock_quantity,
               pet.codigo_dna, pet.largura_mm, pet.comprimento_mm,
               pet.tipo_correia_id, pet.material_base_id
        FROM products p
        INNER JOIN produto_especificacoes_tecnicas pet ON pet.produto_id = p.id
        WHERE p.name LIKE '%T10%2080%'
        LIMIT 1
    """)
    
    if prod:
        print(f"   Produto: #{prod['id']} - {prod['name']}")
        print(f"   DNA: {prod['codigo_dna']}")
        print(f"   Dimensoes: L={prod['largura_mm']}mm x C={prod['comprimento_mm']}mm")
        print(f"   Estoque: {prod['stock_quantity']}")
        print(f"   Tipo ID: {prod['tipo_correia_id']} | Material ID: {prod['material_base_id']}")
    
    # 5. Listar produtos derivaveis (L >= 50 E C >= 2080)
    print("\n5. Produtos derivaveis para L=50mm C=2080mm:")
    derivaveis = db.fetch_all("""
        SELECT p.id, p.name, p.stock_quantity,
               pet.largura_mm, pet.comprimento_mm, pet.codigo_dna
        FROM products p
        INNER JOIN produto_especificacoes_tecnicas pet ON pet.produto_id = p.id
        WHERE p.stock_quantity > 0
          AND (pet.largura_mm >= 50 OR pet.comprimento_mm >= 2080)
        ORDER BY pet.largura_mm DESC, pet.comprimento_mm DESC
        LIMIT 15
    """)
    
    print(f"   Encontrados {len(derivaveis)} produtos:")
    for d in derivaveis:
        marcador = "[DERIVAVEL]" if (d['largura_mm'] or 0) >= 50 and (d['comprimento_mm'] or 0) >= 2080 else "[PARCIAL]"
        print(f"   {marcador} #{d['id']} L={d['largura_mm']} C={d['comprimento_mm']} Est={d['stock_quantity']}")
        print(f"            {d['name'][:50]}")
    
    print("\n" + "=" * 70)
    print("CONCLUIDO! Teste novamente em http://localhost:8080/orcamentos/novo#")
    print("=" * 70)


if __name__ == "__main__":
    main()
