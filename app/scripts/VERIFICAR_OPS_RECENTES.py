# -*- coding: utf-8 -*-
"""
Verificar OPs recentes e por que nao aparecem no Gantt
"""
import sys
sys.path.insert(0, 'c:/Users/arita/CascadeProjects/SupplyChainSystem')

from app.database import Database

def main():
    db = Database()
    
    print("=" * 70)
    print("VERIFICACAO DE OPs RECENTES")
    print("=" * 70)
    
    # 1. Ultimas 10 OPs na tabela ordens_producao
    print("\n1. ULTIMAS 10 OPs (ordens_producao):")
    ops = db.fetch_all("""
        SELECT id, numero_op, produto_id, quantidade, tipo_op, status, 
               empresa_id, cliente_id, etapa_atual_id, created_at
        FROM ordens_producao 
        ORDER BY id DESC 
        LIMIT 10
    """)
    for o in ops:
        print(f"   ID={o['id']}, num={o.get('numero_op')}, qtd={o['quantidade']}, tipo={o.get('tipo_op')}")
        print(f"      empresa_id={o.get('empresa_id')}, cliente_id={o.get('cliente_id')}, etapa={o.get('etapa_atual_id')}")
    
    # 2. Verificar na VIEW
    print("\n2. MESMAS OPs NA VIEW vw_ordens_producao_resumo:")
    for o in ops:
        vw = db.fetch_one("SELECT * FROM vw_ordens_producao_resumo WHERE id = %s", (o['id'],))
        if vw:
            print(f"   ID={o['id']}: OK na view")
        else:
            print(f"   ID={o['id']}: NAO APARECE NA VIEW!")
            # Verificar motivo
            emp = db.fetch_one("SELECT id FROM empresas WHERE id = %s", (o.get('empresa_id'),))
            cli = db.fetch_one("SELECT id FROM customers WHERE id = %s", (o.get('cliente_id'),))
            prod = db.fetch_one("SELECT id FROM products WHERE id = %s", (o.get('produto_id'),))
            print(f"      empresa existe: {emp is not None}, cliente existe: {cli is not None}, produto existe: {prod is not None}")
    
    # 3. Verificar lotes
    print("\n3. LOTES DAS ULTIMAS 10 OPs:")
    for o in ops:
        lotes = db.fetch_all("SELECT * FROM op_lotes WHERE ordem_producao_id = %s", (o['id'],))
        print(f"   OP ID={o['id']}: {len(lotes)} lote(s)")
        for l in lotes:
            print(f"      Lote {l['id']}: qtd={l['quantidade']}, etapa={l.get('etapa_atual_id')}, status={l.get('status')}")
    
    # 4. Verificar se VIEW tem filtro por status
    print("\n4. OPs por STATUS:")
    status_count = db.fetch_all("""
        SELECT status, COUNT(*) as total FROM ordens_producao GROUP BY status
    """)
    for s in status_count:
        print(f"   {s['status']}: {s['total']}")
    
    # 5. Verificar OPs com tipo_op = separacao
    print("\n5. OPs com tipo_op = 'separacao':")
    ops_sep = db.fetch_all("""
        SELECT id, numero_op, quantidade, status, empresa_id, cliente_id
        FROM ordens_producao 
        WHERE tipo_op = 'separacao'
        ORDER BY id DESC
    """)
    print(f"   Total: {len(ops_sep)}")
    for o in ops_sep:
        print(f"   ID={o['id']}, num={o.get('numero_op')}, qtd={o['quantidade']}, empresa={o.get('empresa_id')}, cliente={o.get('cliente_id')}")

if __name__ == "__main__":
    main()
