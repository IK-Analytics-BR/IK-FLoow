"""Script para analisar lotes perdidos"""
import sys
sys.path.insert(0, '.')
from app.database import Database

db = Database()

def analisar_op(numero_op):
    print("=" * 60)
    print(f"ANÁLISE DE LOTES - {numero_op}")
    print("=" * 60)
    
    op = db.fetch_one("""
        SELECT id, numero_op, quantidade 
        FROM ordens_producao 
        WHERE numero_op = %s
    """, (numero_op,))
print(f"\n1. ORDEM DE PRODUÇÃO:")
print(f"   ID: {op.get('id') if op else 'N/A'}")
print(f"   Número: {op.get('numero_op') if op else 'N/A'}")
print(f"   Quantidade Total: {op.get('quantidade') if op else 'N/A'}")

if op:
    op_id = op.get('id')
    
    # 2. Buscar todos os lotes
    lotes = db.fetch_all("""
        SELECT id, sequencia, quantidade, etapa_atual_id, status_operador, 
               operador_id, created_at, updated_at
        FROM op_lotes 
        WHERE ordem_producao_id = %s
        ORDER BY id
    """, (op_id,)) or []
    
    print(f"\n2. LOTES ATUAIS (Total: {len(lotes)}):")
    total_lotes = 0
    for l in lotes:
        total_lotes += float(l.get('quantidade') or 0)
        print(f"   Lote {l.get('id')}: Seq={l.get('sequencia')}, Qtd={l.get('quantidade')}, "
              f"Etapa={l.get('etapa_atual_id')}, Status={l.get('status_operador')}")
    
    print(f"\n   SOMA TOTAL DOS LOTES: {total_lotes}")
    print(f"   QUANTIDADE ORIGINAL: {op.get('quantidade')}")
    print(f"   DIFERENÇA: {float(op.get('quantidade') or 0) - total_lotes}")
    
    # 3. Buscar histórico de movimentações
    logs = db.fetch_all("""
        SELECT l.id, l.lote_id, l.quantidade_movida, l.etapa_anterior_id, l.etapa_nova_id,
               l.status_anterior, l.status_novo, l.created_at, l.observacao,
               ea.nome AS etapa_anterior, en.nome AS etapa_nova
        FROM op_lotes_etapas_log l
        LEFT JOIN producao_etapas ea ON ea.id = l.etapa_anterior_id
        LEFT JOIN producao_etapas en ON en.id = l.etapa_nova_id
        WHERE l.ordem_producao_id = %s
        ORDER BY l.created_at DESC
        LIMIT 20
    """, (op_id,)) or []
    
    print(f"\n3. HISTÓRICO DE MOVIMENTAÇÕES (últimas 20):")
    for log in logs:
        print(f"   [{log.get('created_at')}] Lote {log.get('lote_id')}: "
              f"Qtd={log.get('quantidade_movida')}, "
              f"{log.get('etapa_anterior') or 'N/A'} -> {log.get('etapa_nova') or 'N/A'}, "
              f"{log.get('status_anterior') or 'N/A'} -> {log.get('status_novo') or 'N/A'}")

    # 4. Verificar lote 39 (parece estar faltando)
    lote39 = db.fetch_one("""
        SELECT * FROM op_lotes WHERE id = 39
    """)
    print(f"\n4. VERIFICAÇÃO DO LOTE 39:")
    if lote39:
        print(f"   Existe: SIM")
        for k, v in lote39.items():
            print(f"   {k}: {v}")
    else:
        print(f"   Existe: NÃO (foi deletado)")
    
    # 5. Buscar TODOS os lotes (incluindo deletados se houver soft delete)
    todos_lotes = db.fetch_all("""
        SELECT id, sequencia, quantidade, etapa_atual_id, status_operador, status
        FROM op_lotes 
        WHERE ordem_producao_id = %s
        ORDER BY id
    """, (op_id,)) or []
    
    print(f"\n5. TODOS OS LOTES (sem filtro):")
    for l in todos_lotes:
        print(f"   Lote {l.get('id')}: Qtd={l.get('quantidade')}, Status={l.get('status')}, StatusOp={l.get('status_operador')}")

    # 6. CORRIGIR: Inserir lote com as 3 unidades perdidas
    print("\n6. CORREÇÃO - Inserindo lote com 3 unidades perdidas...")
    
    # Verificar próxima sequência
    max_seq = db.fetch_one("""
        SELECT COALESCE(MAX(sequencia), 0) + 1 AS next_seq 
        FROM op_lotes WHERE ordem_producao_id = %s
    """, (op_id,))
    next_seq = max_seq.get('next_seq') if max_seq else 1
    
    # Inserir lote corrigido (volta para primeira etapa - etapa 8)
    novo_lote_id = db.insert("""
        INSERT INTO op_lotes (
            ordem_producao_id, sequencia, quantidade, etapa_atual_id,
            status_operador, status, align_side, created_at
        ) VALUES (%s, %s, 3.0000, 8, NULL, 'pendente', 'full', NOW())
    """, (op_id, next_seq))
    
    print(f"   Novo lote criado: ID={novo_lote_id}, Seq={next_seq}, Qtd=3")
    
    # Registrar no log
    db.insert("""
        INSERT INTO op_lotes_etapas_log (
            lote_id, ordem_producao_id, quantidade_movida,
            etapa_anterior_id, etapa_nova_id, status_anterior, status_novo,
            usuario_id, observacao, created_at
        ) VALUES (%s, %s, 3.0000, NULL, 8, NULL, 'criado', 1, 
                  'Lote recriado - correção de dados perdidos durante testes', NOW())
    """, (novo_lote_id, op_id))
    
    print("   Log registrado!")
    
    # Verificar soma final
    soma_final = db.fetch_one("""
        SELECT SUM(quantidade) AS total FROM op_lotes WHERE ordem_producao_id = %s
    """, (op_id,))
    print(f"\n   SOMA FINAL: {soma_final.get('total') if soma_final else 0}")

print("\n" + "=" * 60)
