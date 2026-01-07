# -*- coding: utf-8 -*-
"""
Diagnóstico completo do fluxo de OP
"""
import sys
sys.path.insert(0, 'c:/Users/arita/CascadeProjects/SupplyChainSystem')

from app.database import Database

def main():
    db = Database()
    
    print("=" * 70)
    print("DIAGNOSTICO COMPLETO - FLUXO DE OP")
    print("=" * 70)
    
    # 1. Buscar orcamento e suas OPs
    orc = db.fetch_one("SELECT * FROM orcamentos WHERE numero = 'ORC-2025-0026'")
    orc_id = orc['id']
    print(f"\n1. ORCAMENTO: ID={orc_id}, Numero={orc['numero']}, Status={orc['status']}")
    
    # 2. Itens do orcamento
    itens = db.fetch_all("""
        SELECT oi.*, p.name AS produto_nome, p.stock_quantity
        FROM orcamento_itens oi
        JOIN products p ON p.id = oi.produto_id
        WHERE oi.orcamento_id = %s
    """, (orc_id,))
    
    print(f"\n2. ITENS DO ORCAMENTO:")
    for item in itens:
        print(f"   - Produto: {item['produto_nome']}")
        print(f"     Quantidade orcamento: {item['quantidade']}")
        print(f"     qtd_estoque_alocada: {item.get('qtd_estoque_alocada')}")
        print(f"     qtd_a_produzir: {item.get('qtd_a_produzir')}")
        print(f"     status_alocacao: {item.get('status_alocacao')}")
        print(f"     Estoque atual produto: {item['stock_quantity']}")
    
    # 3. Vinculos orcamento_op_itens
    vinculos = db.fetch_all("""
        SELECT * FROM orcamento_op_itens WHERE orcamento_id = %s
    """, (orc_id,))
    print(f"\n3. VINCULOS orcamento_op_itens: {len(vinculos)}")
    for v in vinculos:
        print(f"   vinculo_id={v['id']}, op_id={v['ordem_producao_id']}, qtd={v['quantidade']}")
    
    # 4. OPs criadas
    print(f"\n4. OPs NA TABELA ordens_producao:")
    for v in vinculos:
        op = db.fetch_one("SELECT * FROM ordens_producao WHERE id = %s", (v['ordem_producao_id'],))
        if op:
            print(f"   OP ID={op['id']}")
            print(f"      numero_op: {op.get('numero_op')}")
            print(f"      quantidade: {op['quantidade']}")
            print(f"      tipo_op: {op.get('tipo_op')}")
            print(f"      status: {op['status']}")
            print(f"      etapa_atual_id: {op.get('etapa_atual_id')}")
            print(f"      obs_estoque: {op.get('obs_estoque')}")
        else:
            print(f"   OP ID={v['ordem_producao_id']} NAO ENCONTRADA!")
    
    # 5. Verificar VIEW vw_ordens_producao_resumo
    print(f"\n5. VIEW vw_ordens_producao_resumo:")
    for v in vinculos:
        vw = db.fetch_one("SELECT * FROM vw_ordens_producao_resumo WHERE id = %s", (v['ordem_producao_id'],))
        if vw:
            print(f"   OP ID={vw['id']} ENCONTRADA na view")
            print(f"      numero_op: {vw.get('numero_op')}")
            print(f"      status: {vw.get('status')}")
        else:
            print(f"   OP ID={v['ordem_producao_id']} NAO ESTA NA VIEW!")
    
    # 6. Verificar LOTES (op_lotes)
    print(f"\n6. LOTES (op_lotes):")
    for v in vinculos:
        lotes = db.fetch_all("SELECT * FROM op_lotes WHERE ordem_producao_id = %s", (v['ordem_producao_id'],))
        print(f"   OP ID={v['ordem_producao_id']}: {len(lotes)} lote(s)")
        for lote in lotes:
            print(f"      Lote ID={lote['id']}, qtd={lote['quantidade']}, etapa={lote.get('etapa_atual_id')}, status={lote.get('status')}")
    
    # 7. Reservas de estoque
    print(f"\n7. RESERVAS DE ESTOQUE (estoque_reservas):")
    reservas = db.fetch_all("""
        SELECT er.*, p.name AS produto_nome
        FROM estoque_reservas er
        JOIN products p ON p.id = er.produto_id
        WHERE er.tipo_origem = 'orcamento' AND er.origem_id = %s
    """, (orc_id,))
    print(f"   Total: {len(reservas)} reserva(s)")
    for r in reservas:
        print(f"   - Produto: {r['produto_nome']}, Qtd: {r['quantidade']}, Status: {r['status']}")
    
    # 8. Verificar se estoque foi BAIXADO (movimentacoes)
    print(f"\n8. MOVIMENTACOES DE ESTOQUE (estoque_movimentacoes):")
    try:
        movs = db.fetch_all("""
            SELECT em.*, p.name AS produto_nome
            FROM estoque_movimentacoes em
            JOIN products p ON p.id = em.produto_id
            WHERE em.referencia_tipo = 'orcamento' AND em.referencia_id = %s
        """, (orc_id,))
        print(f"   Total: {len(movs)} movimentacao(oes)")
        for m in movs:
            print(f"   - Produto: {m['produto_nome']}, Tipo: {m.get('tipo')}, Qtd: {m.get('quantidade')}")
    except Exception as e:
        print(f"   Tabela nao existe ou erro: {e}")
    
    # 9. Verificar materia-prima do produto
    print(f"\n9. ESPECIFICACOES TECNICAS / MATERIA-PRIMA:")
    if itens:
        prod_id = itens[0]['produto_id']
        # Buscar template de producao
        template = db.fetch_one("""
            SELECT * FROM produto_templates_producao 
            WHERE produto_id = %s AND ativo = 1 
            LIMIT 1
        """, (prod_id,))
        if template:
            print(f"   Template ID={template['id']}")
            template_itens = db.fetch_all("""
                SELECT ti.*, p.name AS item_nome, p.stock_quantity
                FROM produto_template_itens ti
                LEFT JOIN products p ON p.id = ti.produto_id
                WHERE ti.template_id = %s
            """, (template['id'],))
            print(f"   Itens do template ({len(template_itens)}):")
            for ti in template_itens:
                print(f"      - {ti.get('item_nome') or ti.get('descricao')}: {ti['quantidade']} x (estoque: {ti.get('stock_quantity')})")
        else:
            print(f"   Produto {prod_id} NAO tem template de producao")
    
    # 10. Definicao da VIEW
    print(f"\n10. DEFINICAO DA VIEW vw_ordens_producao_resumo:")
    try:
        view_def = db.fetch_one("SHOW CREATE VIEW vw_ordens_producao_resumo")
        if view_def:
            create_stmt = view_def.get('Create View', '')
            # Mostrar apenas primeiras linhas
            lines = create_stmt.split('\n')[:10]
            for line in lines:
                print(f"   {line}")
            if len(create_stmt.split('\n')) > 10:
                print("   ...")
    except Exception as e:
        print(f"   Erro ao obter definicao: {e}")
    
    print("\n" + "=" * 70)
    print("FIM DO DIAGNOSTICO")
    print("=" * 70)

if __name__ == "__main__":
    main()
