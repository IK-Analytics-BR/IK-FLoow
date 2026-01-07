"""
Script para adicionar especificação técnica ao produto de teste
e garantir estoque em produtos com especificações
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.database import Database

def main():
    db = Database()
    
    print("=" * 70)
    print("ADICIONAR ESPECIFICAÇÕES E ESTOQUE PARA TESTE DNA")
    print("=" * 70)
    
    # 1. Buscar produto T10 2080X50MM
    print("\n1. Buscando produto T10 2080X50MM...")
    produto = db.fetch_one("""
        SELECT p.id, p.name, p.stock_quantity,
               pet.id as esp_id, pet.codigo_dna
        FROM products p
        LEFT JOIN produto_especificacoes_tecnicas pet ON pet.produto_id = p.id
        WHERE p.name LIKE '%T10%2080%' OR p.name LIKE '%2080%T10%'
        LIMIT 1
    """)
    
    if produto:
        print(f"   Encontrado: #{produto['id']} - {produto['name']}")
        print(f"   Estoque: {produto['stock_quantity']}")
        print(f"   DNA existente: {produto['codigo_dna']}")
        
        if not produto['esp_id']:
            # Buscar IDs de tipo e material
            tipo_sin = db.fetch_one("SELECT id FROM tipos_correia WHERE codigo = 'SIN'")
            mat_pu = db.fetch_one("SELECT id FROM materiais_correia WHERE codigo = 'PU'")
            perfil_t10 = db.fetch_one("SELECT id FROM perfis_correia WHERE codigo = 'T10'")
            
            tipo_id = tipo_sin['id'] if tipo_sin else 1
            mat_id = mat_pu['id'] if mat_pu else 1
            perfil_id = perfil_t10['id'] if perfil_t10 else None
            
            # Inserir especificação (2080 x 50mm)
            db.execute("""
                INSERT INTO produto_especificacoes_tecnicas 
                (produto_id, largura_mm, comprimento_mm, tipo_correia_id, 
                 material_base_id, perfil_id, codigo_dna, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, (produto['id'], 50, 2080, tipo_id, mat_id, perfil_id, 'SIN-PU-T10-L50-C2080'))
            
            print(f"   [OK] Especificacao criada: SIN-PU-T10 L=50mm C=2080mm")
    else:
        print("   Produto não encontrado")
    
    # 2. Garantir estoque em todos produtos com especificação
    print("\n2. Atualizando estoque para produtos com especificação...")
    db.execute("""
        UPDATE products p
        INNER JOIN produto_especificacoes_tecnicas pet ON pet.produto_id = p.id
        SET p.stock_quantity = FLOOR(RAND() * 50) + 10
        WHERE p.stock_quantity IS NULL OR p.stock_quantity <= 0
    """)
    
    # 3. Criar produtos de teste variados para DNA
    print("\n3. Criando produtos de teste com dimensões variadas...")
    
    produtos_teste = [
        # Largura maior que 50mm (derivável de 50mm)
        ('CORREIA T10 100MM X 3000MM PU TESTE', 100, 3000, 'SIN-PU-T10-L100-C3000'),
        ('CORREIA T10 80MM X 2500MM PU TESTE', 80, 2500, 'SIN-PU-T10-L80-C2500'),
        ('CORREIA T10 60MM X 2200MM PU TESTE', 60, 2200, 'SIN-PU-T10-L60-C2200'),
        # Comprimento maior que 2080mm (derivável)
        ('CORREIA T10 50MM X 3500MM PU TESTE', 50, 3500, 'SIN-PU-T10-L50-C3500'),
        ('CORREIA T10 50MM X 4000MM PU TESTE', 50, 4000, 'SIN-PU-T10-L50-C4000'),
        # Ambos maiores (melhor opção derivável)
        ('CORREIA T10 120MM X 5000MM PU TESTE', 120, 5000, 'SIN-PU-T10-L120-C5000'),
        ('CORREIA T10 150MM X 6000MM PU TESTE', 150, 6000, 'SIN-PU-T10-L150-C6000'),
        # Mesmo tipo, material diferente
        ('CORREIA T10 100MM X 3000MM BORRACHA TESTE', 100, 3000, 'SIN-BOR-T10-L100-C3000'),
        # Tipo diferente, mesmo material
        ('CORREIA AT10 100MM X 3000MM PU TESTE', 100, 3000, 'SIN-PU-AT10-L100-C3000'),
    ]
    
    tipo_sin = db.fetch_one("SELECT id FROM tipos_correia WHERE codigo = 'SIN'")
    mat_pu = db.fetch_one("SELECT id FROM materiais_correia WHERE codigo = 'PU'")
    mat_bor = db.fetch_one("SELECT id FROM materiais_correia WHERE codigo = 'BOR'")
    perfil_t10 = db.fetch_one("SELECT id FROM perfis_correia WHERE codigo = 'T10'")
    perfil_at10 = db.fetch_one("SELECT id FROM perfis_correia WHERE codigo = 'AT10'")
    
    for nome, largura, comprimento, dna in produtos_teste:
        # Verificar se já existe
        existe = db.fetch_one("SELECT id FROM products WHERE name = %s", (nome,))
        if existe:
            print(f"   Já existe: {nome[:50]}")
            continue
        
        # Criar produto
        db.execute("""
            INSERT INTO products (name, internal_code, stock_quantity, price, active, created_at)
            VALUES (%s, %s, %s, 100.00, 1, NOW())
        """, (nome, f'TESTE-{largura}-{comprimento}', 25))
        
        prod_id = db.fetch_one("SELECT LAST_INSERT_ID() as id")['id']
        
        # Determinar tipo e material
        mat_id = mat_bor['id'] if 'BORRACHA' in nome else mat_pu['id']
        perfil_id = perfil_at10['id'] if 'AT10' in nome else perfil_t10['id']
        
        # Criar especificação
        db.execute("""
            INSERT INTO produto_especificacoes_tecnicas 
            (produto_id, largura_mm, comprimento_mm, tipo_correia_id, 
             material_base_id, perfil_id, codigo_dna, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        """, (prod_id, largura, comprimento, tipo_sin['id'], mat_id, perfil_id, dna))
        
        print(f"   [OK] Criado: {nome[:50]} | L={largura} C={comprimento}")
    
    # 4. Mostrar estatísticas finais
    print("\n4. Estatísticas finais:")
    stats = db.fetch_one("""
        SELECT 
            COUNT(DISTINCT pet.produto_id) as com_especificacao,
            COUNT(DISTINCT CASE WHEN p.stock_quantity > 0 THEN p.id END) as com_estoque,
            COUNT(DISTINCT CASE WHEN pet.largura_mm IS NOT NULL THEN p.id END) as com_largura,
            COUNT(DISTINCT CASE WHEN pet.comprimento_mm IS NOT NULL THEN p.id END) as com_comprimento
        FROM produto_especificacoes_tecnicas pet
        INNER JOIN products p ON p.id = pet.produto_id
    """)
    
    print(f"   Produtos com especificação: {stats['com_especificacao']}")
    print(f"   Com estoque > 0: {stats['com_estoque']}")
    print(f"   Com largura definida: {stats['com_largura']}")
    print(f"   Com comprimento definido: {stats['com_comprimento']}")
    
    # 5. Simular busca DNA para o produto T10 2080x50
    print("\n5. Simulando busca DNA para T10 50x2080mm:")
    similares = db.fetch_all("""
        SELECT 
            p.id, p.name, p.stock_quantity,
            pet.largura_mm, pet.comprimento_mm, pet.codigo_dna,
            CASE 
                WHEN pet.largura_mm >= 50 AND pet.comprimento_mm >= 2080 THEN 'DERIVAVEL'
                ELSE 'PARCIAL'
            END as tipo
        FROM products p
        INNER JOIN produto_especificacoes_tecnicas pet ON pet.produto_id = p.id
        WHERE p.stock_quantity > 0
          AND pet.tipo_correia_id = (SELECT id FROM tipos_correia WHERE codigo = 'SIN')
          AND (pet.largura_mm >= 50 OR pet.comprimento_mm >= 2080)
        ORDER BY pet.largura_mm DESC, pet.comprimento_mm DESC
        LIMIT 10
    """)
    
    print(f"   Encontrados {len(similares)} produtos deriváveis:")
    for s in similares:
        print(f"   - #{s['id']} L={s['largura_mm']} C={s['comprimento_mm']} Est={s['stock_quantity']} [{s['tipo']}]")
        print(f"     {s['name'][:55]}")
    
    print("\n" + "=" * 70)
    print("CONCLUÍDO! Agora teste novamente no orçamento.")
    print("=" * 70)


if __name__ == "__main__":
    main()
