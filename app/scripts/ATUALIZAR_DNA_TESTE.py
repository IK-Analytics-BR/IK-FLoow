import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from app.database import Database

db = Database()

# Atualizar DNA do produto de teste
db.execute("""
    UPDATE produto_especificacoes_tecnicas 
    SET codigo_dna = 'SIN-PU-T10-L50-C2080' 
    WHERE produto_id = 2799
""")
print("DNA atualizado para: SIN-PU-T10-L50-C2080")

# Verificar
p = db.fetch_one("""
    SELECT p.id, p.name, p.stock_quantity, pet.codigo_dna, pet.largura_mm, pet.comprimento_mm
    FROM products p
    INNER JOIN produto_especificacoes_tecnicas pet ON pet.produto_id = p.id
    WHERE p.id = 2799
""")
if p:
    print(f"Produto #{p['id']}: {p['name']}")
    print(f"DNA: {p['codigo_dna']}")
    print(f"Dimensoes: L={p['largura_mm']}mm x C={p['comprimento_mm']}mm")
    print(f"Estoque: {p['stock_quantity']}")
