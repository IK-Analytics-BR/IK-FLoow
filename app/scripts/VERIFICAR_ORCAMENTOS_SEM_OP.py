# -*- coding: utf-8 -*-
"""
Verificar orçamentos aprovados sem OP vinculada
"""
import sys
sys.path.insert(0, 'c:/Users/arita/CascadeProjects/SupplyChainSystem')

from app.database import Database

def main():
    db = Database()
    
    print("=" * 80)
    print("VERIFICACAO DE ORCAMENTOS E OPs")
    print("=" * 80)
    
    # 1. Orcamentos aprovados SEM OP
    print("\n1. ORCAMENTOS APROVADOS SEM OP VINCULADA:")
    print("-" * 80)
    
    orcs_sem_op = db.fetch_all("""
        SELECT 
            o.id, o.numero, o.status,
            oi.id AS item_id,
            oi.quantidade,
            p.name AS produto_nome
        FROM orcamentos o 
        JOIN orcamento_itens oi ON oi.orcamento_id = o.id 
        JOIN products p ON p.id = oi.produto_id 
        LEFT JOIN orcamento_op_itens ooi ON ooi.orcamento_item_id = oi.id 
        WHERE ooi.id IS NULL 
          AND o.status IN ('aprovado', 'em_producao')
        ORDER BY o.id DESC
    """)
    
    if orcs_sem_op:
        for r in orcs_sem_op:
            print(f"  {r['numero']} (Status: {r['status']})")
            print(f"    Item {r['item_id']}: {r['quantidade']} x {r['produto_nome'][:50]}")
    else:
        print("  Nenhum orcamento aprovado sem OP")
    
    # 2. Todos os orcamentos recentes
    print("\n2. ULTIMOS 10 ORCAMENTOS:")
    print("-" * 80)
    print(f"{'Numero':<15} {'Status':<12} {'Itens':<6} {'OPs':<6}")
    print("-" * 80)
    
    ultimos = db.fetch_all("""
        SELECT 
            o.id, o.numero, o.status,
            (SELECT COUNT(*) FROM orcamento_itens oi WHERE oi.orcamento_id = o.id) AS qtd_itens,
            (SELECT COUNT(DISTINCT ooi.ordem_producao_id) FROM orcamento_op_itens ooi WHERE ooi.orcamento_id = o.id) AS qtd_ops
        FROM orcamentos o
        ORDER BY o.id DESC
        LIMIT 10
    """)
    
    for u in ultimos:
        print(f"{u['numero']:<15} {u['status']:<12} {u['qtd_itens']:<6} {u['qtd_ops']:<6}")
    
    # 3. Detalhes das OPs recentes
    print("\n3. ULTIMAS 10 OPs CRIADAS:")
    print("-" * 80)
    print(f"{'OP':<15} {'Tipo':<12} {'Qtd':<10} {'Status':<12} {'Orcamento'}")
    print("-" * 80)
    
    ops = db.fetch_all("""
        SELECT 
            op.id, op.numero_op, op.quantidade, op.tipo_op, op.status,
            o.numero AS orcamento_numero
        FROM ordens_producao op
        LEFT JOIN orcamento_op_itens ooi ON ooi.ordem_producao_id = op.id
        LEFT JOIN orcamentos o ON o.id = ooi.orcamento_id
        ORDER BY op.id DESC
        LIMIT 10
    """)
    
    for op in ops:
        numero = op['numero_op'] or f"OP#{op['id']}"
        tipo = op['tipo_op'] or 'N/A'
        orc = op['orcamento_numero'] or 'N/A'
        print(f"{numero:<15} {tipo:<12} {float(op['quantidade']):<10.2f} {op['status']:<12} {orc}")

if __name__ == "__main__":
    main()
