"""Testar inserção de pausa"""
import sys
sys.path.insert(0, '.')
from app.database import Database

db = Database()

# Verificar lotes em producao
lotes = db.fetch_all("SELECT id, ordem_producao_id, etapa_atual_id FROM op_lotes WHERE status_operador = 'em_producao' LIMIT 2")
print('Lotes em producao:', lotes)

if lotes:
    lote = lotes[0]
    print(f"\nTestando com lote ID={lote['id']}")
    
    # Tentar inserir uma pausa
    try:
        pausa_id = db.insert("""
            INSERT INTO producao_pausas 
            (lote_id, ordem_producao_id, operador_id, motivo_id, etapa_id, inicio, observacao)
            VALUES (%s, %s, %s, %s, %s, NOW(), %s)
        """, (lote['id'], lote['ordem_producao_id'], 1, 2, lote.get('etapa_atual_id'), 'Teste via script'))
        print('Pausa criada com ID:', pausa_id)
        
        # Verificar
        pausas = db.fetch_all('SELECT * FROM producao_pausas')
        print('Total pausas no banco:', len(pausas))
        for p in pausas:
            print(f"  - ID={p['id']}, lote={p['lote_id']}, motivo={p['motivo_id']}, inicio={p['inicio']}")
    except Exception as e:
        print('ERRO ao inserir:', e)
else:
    print('Nenhum lote em producao encontrado!')
