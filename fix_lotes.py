"""Script para corrigir lotes perdidos - OP-2025-0014 e OP-2025-0008"""
import sys
sys.path.insert(0, '.')
from app.database import Database

db = Database()

def corrigir_op(op_id, numero_op, qtd_faltando):
    print(f"\n{'='*50}")
    print(f"CORRIGINDO {numero_op} (ID={op_id}) - Faltam {qtd_faltando} unidades")
    print('='*50)
    
    # Verificar soma atual
    soma = db.fetch_one("""
        SELECT SUM(quantidade) AS total FROM op_lotes WHERE ordem_producao_id = %s
    """, (op_id,))
    soma_atual = float(soma.get('total') or 0) if soma else 0
    print(f"Soma atual: {soma_atual}")
    
    # Próxima sequência
    max_seq = db.fetch_one("""
        SELECT COALESCE(MAX(sequencia), 0) + 1 AS next_seq 
        FROM op_lotes WHERE ordem_producao_id = %s
    """, (op_id,))
    next_seq = int(max_seq.get('next_seq')) if max_seq else 1
    
    # Inserir lote corrigido (etapa 8 = primeira etapa)
    novo_lote_id = db.insert("""
        INSERT INTO op_lotes (
            ordem_producao_id, sequencia, quantidade, etapa_atual_id,
            status_operador, status, align_side, created_at
        ) VALUES (%s, %s, %s, 8, NULL, 'pendente', 'full', NOW())
    """, (op_id, next_seq, qtd_faltando))
    
    print(f"Novo lote criado: ID={novo_lote_id}, Seq={next_seq}, Qtd={qtd_faltando}")
    
    # Registrar no log
    db.insert("""
        INSERT INTO op_lotes_etapas_log (
            lote_id, ordem_producao_id, quantidade_movida,
            etapa_anterior_id, etapa_nova_id, status_anterior, status_novo,
            usuario_id, observacao, created_at
        ) VALUES (%s, %s, %s, NULL, 8, NULL, 'criado', 1, 
                  'Lote recriado - correção de dados perdidos durante testes', NOW())
    """, (novo_lote_id, op_id, qtd_faltando))
    
    print("Log registrado!")
    
    # Verificar soma final
    soma_final = db.fetch_one("""
        SELECT SUM(quantidade) AS total FROM op_lotes WHERE ordem_producao_id = %s
    """, (op_id,))
    soma_nova = float(soma_final.get('total') or 0) if soma_final else 0
    print(f"Soma após correção: {soma_nova}")
    
    return soma_nova

print("\n" + "="*60)
print("CORREÇÃO DE LOTES PERDIDOS")
print("="*60)

# Corrigir OP-2025-0014 (ID=14) - Faltam 3 unidades
soma14 = corrigir_op(14, 'OP-2025-0014', 3.0)

# Corrigir OP-2025-0008 (ID=8) - Faltam 3 unidades
soma8 = corrigir_op(8, 'OP-2025-0008', 3.0)

print("\n" + "="*60)
print("RESUMO FINAL")
print("="*60)
print(f"OP-2025-0014: Soma = {soma14} (esperado: 10) - {'OK' if soma14 == 10 else 'ERRO'}")
print(f"OP-2025-0008: Soma = {soma8} (esperado: 10) - {'OK' if soma8 == 10 else 'ERRO'}")
print("="*60)
