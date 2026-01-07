"""Script para analisar lotes perdidos - OP-2025-0014 e OP-2025-0008"""
import sys
sys.path.insert(0, '.')
from app.database import Database

db = Database()

def analisar_op(numero_op):
    print("\n" + "=" * 60)
    print(f"ANÁLISE DE LOTES - {numero_op}")
    print("=" * 60)
    
    op = db.fetch_one("""
        SELECT id, numero_op, quantidade 
        FROM ordens_producao 
        WHERE numero_op = %s
    """, (numero_op,))
    
    if not op:
        print(f"OP {numero_op} não encontrada!")
        return None
    
    op_id = op.get('id')
    qtd_original = float(op.get('quantidade') or 0)
    
    print(f"\n1. ORDEM DE PRODUÇÃO:")
    print(f"   ID: {op_id}")
    print(f"   Número: {op.get('numero_op')}")
    print(f"   Quantidade Total: {qtd_original}")
    
    # Buscar todos os lotes
    lotes = db.fetch_all("""
        SELECT id, sequencia, quantidade, etapa_atual_id, status_operador
        FROM op_lotes 
        WHERE ordem_producao_id = %s
        ORDER BY id
    """, (op_id,)) or []
    
    print(f"\n2. LOTES ATUAIS (Total: {len(lotes)}):")
    total_lotes = 0
    for l in lotes:
        qtd = float(l.get('quantidade') or 0)
        total_lotes += qtd
        print(f"   Lote {l.get('id')}: Seq={l.get('sequencia')}, Qtd={qtd}, "
              f"Etapa={l.get('etapa_atual_id')}, Status={l.get('status_operador')}")
    
    diferenca = qtd_original - total_lotes
    print(f"\n   SOMA TOTAL DOS LOTES: {total_lotes}")
    print(f"   QUANTIDADE ORIGINAL: {qtd_original}")
    print(f"   DIFERENÇA (PERDIDA): {diferenca}")
    
    return {
        'op_id': op_id,
        'numero_op': numero_op,
        'qtd_original': qtd_original,
        'qtd_atual': total_lotes,
        'diferenca': diferenca
    }

# Analisar as duas OPs
resultado_14 = analisar_op('OP-2025-0014')
resultado_08 = analisar_op('OP-2025-0008')

print("\n" + "=" * 60)
print("RESUMO DAS CORREÇÕES NECESSÁRIAS")
print("=" * 60)

if resultado_14 and resultado_14['diferenca'] > 0:
    print(f"\nOP-2025-0014: Faltam {resultado_14['diferenca']} unidades")
    
if resultado_08 and resultado_08['diferenca'] > 0:
    print(f"\nOP-2025-0008: Faltam {resultado_08['diferenca']} unidades")

print("\n" + "=" * 60)
