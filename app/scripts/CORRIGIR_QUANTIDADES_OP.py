# -*- coding: utf-8 -*-
"""
Diagnosticar e corrigir diferenças de quantidade entre orçamentos e OPs
"""
import sys
sys.path.insert(0, 'c:/Users/arita/CascadeProjects/SupplyChainSystem')

from app.database import Database

def main():
    db = Database()
    
    print("=" * 80)
    print("DIAGNOSTICO E CORRECAO DE QUANTIDADES - ORCAMENTOS vs OPs")
    print("=" * 80)
    
    # 1. Buscar todos os vinculos orcamento -> OP
    print("\n1. COMPARANDO QUANTIDADES:")
    print("-" * 80)
    print(f"{'Orcamento':<15} {'Item':<8} {'Qtd Orc':<12} {'OP':<10} {'Qtd OP':<12} {'Diferenca':<12} {'Status'}")
    print("-" * 80)
    
    diferencas = db.fetch_all("""
        SELECT 
            o.numero AS orcamento_numero,
            oi.id AS item_id,
            oi.quantidade AS qtd_orcamento,
            ooi.ordem_producao_id AS op_id,
            op.numero_op,
            op.quantidade AS qtd_op,
            ooi.quantidade AS qtd_vinculo,
            l.id AS lote_id,
            l.quantidade AS qtd_lote
        FROM orcamento_op_itens ooi
        INNER JOIN orcamento_itens oi ON oi.id = ooi.orcamento_item_id
        INNER JOIN orcamentos o ON o.id = ooi.orcamento_id
        INNER JOIN ordens_producao op ON op.id = ooi.ordem_producao_id
        LEFT JOIN op_lotes l ON l.ordem_producao_id = op.id
        ORDER BY o.id DESC, ooi.id
    """)
    
    correcoes = []
    
    for d in diferencas:
        qtd_orc = float(d['qtd_orcamento'])
        qtd_op = float(d['qtd_op'])
        diff = qtd_orc - qtd_op
        
        status = "OK" if diff == 0 else "DIFERENTE"
        
        print(f"{d['orcamento_numero']:<15} {d['item_id']:<8} {qtd_orc:<12.2f} {d['numero_op'] or d['op_id']:<10} {qtd_op:<12.2f} {diff:<12.2f} {status}")
        
        if diff != 0:
            correcoes.append({
                'op_id': d['op_id'],
                'lote_id': d['lote_id'],
                'qtd_correta': qtd_orc,
                'qtd_atual_op': qtd_op,
                'qtd_atual_lote': float(d['qtd_lote']) if d['qtd_lote'] else None,
                'vinculo_id': d['item_id']
            })
    
    print("-" * 80)
    print(f"Total de registros: {len(diferencas)}")
    print(f"Com diferenca: {len(correcoes)}")
    
    # 2. Aplicar correcoes
    if correcoes:
        print("\n2. APLICANDO CORRECOES:")
        print("-" * 80)
        
        for c in correcoes:
            print(f"\n   OP ID={c['op_id']}:")
            print(f"      Quantidade atual: {c['qtd_atual_op']}")
            print(f"      Quantidade correta: {c['qtd_correta']}")
            
            # Corrigir OP
            db.execute("""
                UPDATE ordens_producao SET quantidade = %s WHERE id = %s
            """, (c['qtd_correta'], c['op_id']))
            print(f"      [OK] ordens_producao atualizada")
            
            # Corrigir vinculo
            db.execute("""
                UPDATE orcamento_op_itens SET quantidade = %s WHERE ordem_producao_id = %s
            """, (c['qtd_correta'], c['op_id']))
            print(f"      [OK] orcamento_op_itens atualizado")
            
            # Corrigir lote se existir
            if c['lote_id']:
                db.execute("""
                    UPDATE op_lotes SET quantidade = %s WHERE id = %s
                """, (c['qtd_correta'], c['lote_id']))
                print(f"      [OK] op_lotes (ID={c['lote_id']}) atualizado")
        
        print("\n" + "=" * 80)
        print("CORRECOES APLICADAS COM SUCESSO!")
        print("=" * 80)
    else:
        print("\n[OK] Todas as quantidades estao corretas!")
    
    # 3. Verificacao final
    print("\n3. VERIFICACAO FINAL:")
    print("-" * 80)
    
    verificacao = db.fetch_all("""
        SELECT 
            o.numero AS orcamento,
            oi.quantidade AS qtd_orcamento,
            op.numero_op,
            op.quantidade AS qtd_op,
            l.quantidade AS qtd_lote
        FROM orcamento_op_itens ooi
        INNER JOIN orcamento_itens oi ON oi.id = ooi.orcamento_item_id
        INNER JOIN orcamentos o ON o.id = ooi.orcamento_id
        INNER JOIN ordens_producao op ON op.id = ooi.ordem_producao_id
        LEFT JOIN op_lotes l ON l.ordem_producao_id = op.id
        ORDER BY o.id DESC
        LIMIT 10
    """)
    
    print(f"{'Orcamento':<15} {'Qtd Orc':<12} {'OP':<15} {'Qtd OP':<12} {'Qtd Lote':<12}")
    print("-" * 80)
    for v in verificacao:
        print(f"{v['orcamento']:<15} {float(v['qtd_orcamento']):<12.2f} {v['numero_op'] or 'N/A':<15} {float(v['qtd_op']):<12.2f} {float(v['qtd_lote']) if v['qtd_lote'] else 'N/A':<12}")

if __name__ == "__main__":
    main()
