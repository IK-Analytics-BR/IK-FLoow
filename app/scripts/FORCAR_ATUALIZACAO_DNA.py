import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from app.database import Database

db = Database()

print("1. Verificando especificacao atual...")
esp = db.fetch_one("""
    SELECT * FROM produto_especificacoes_tecnicas WHERE produto_id = 2799
""")
print(f"   ID especificacao: {esp['id'] if esp else 'NAO ENCONTRADA'}")
if esp:
    print(f"   codigo_dna atual: {esp['codigo_dna']}")
    print(f"   largura_mm: {esp['largura_mm']}")
    print(f"   comprimento_mm: {esp['comprimento_mm']}")

print("\n2. Atualizando DNA e dimensoes...")
db.execute("""
    UPDATE produto_especificacoes_tecnicas 
    SET codigo_dna = 'SIN-PU-T10-L50-C2080',
        largura_mm = 50,
        comprimento_mm = 2080
    WHERE produto_id = 2799
""")
print("   UPDATE executado")

print("\n3. Verificando apos update...")
esp2 = db.fetch_one("""
    SELECT * FROM produto_especificacoes_tecnicas WHERE produto_id = 2799
""")
if esp2:
    print(f"   codigo_dna: {esp2['codigo_dna']}")
    print(f"   largura_mm: {esp2['largura_mm']}")
    print(f"   comprimento_mm: {esp2['comprimento_mm']}")

print("\n4. Listando produtos similares (tipo_correia_id=1, com estoque)...")
similares = db.fetch_all("""
    SELECT p.id, p.name, p.stock_quantity, 
           pet.codigo_dna, pet.largura_mm, pet.comprimento_mm,
           pet.tipo_correia_id, pet.material_base_id
    FROM products p
    INNER JOIN produto_especificacoes_tecnicas pet ON pet.produto_id = p.id
    WHERE p.stock_quantity > 0
      AND pet.tipo_correia_id = 1
    ORDER BY pet.largura_mm DESC
    LIMIT 10
""")
print(f"   Encontrados {len(similares)} produtos tipo SIN com estoque:")
for s in similares:
    print(f"   #{s['id']:4} | L={s['largura_mm']} C={s['comprimento_mm']} | Est={s['stock_quantity']}")
    print(f"         DNA: {s['codigo_dna']}")
    print(f"         {s['name'][:50]}")
