# -*- coding: utf-8 -*-
"""
Criar/Corrigir etapa de Separação e Embalagem para OPs de estoque
"""
import sys
sys.path.insert(0, 'c:/Users/arita/CascadeProjects/SupplyChainSystem')

from app.database import Database

def main():
    db = Database()
    
    print("=== CRIANDO ETAPA DE SEPARACAO E EMBALAGEM ===\n")
    
    # 1. Verificar se existe
    etapa = db.fetch_one("""
        SELECT * FROM producao_etapas 
        WHERE nome LIKE '%Separa%Embalag%' OR tipo_etapa = 'separacao'
    """)
    
    if etapa:
        print(f"1. Etapa ja existe: ID={etapa['id']}, nome={etapa['nome']}")
        etapa_id = etapa['id']
    else:
        # Pegar maior ordem
        max_ordem = db.fetch_one("SELECT MAX(ordem) as max_ordem FROM producao_etapas")
        nova_ordem = (max_ordem['max_ordem'] or 0) + 10
        
        # Criar etapa
        etapa_id = db.insert("""
            INSERT INTO producao_etapas (nome, descricao, ordem, ativo, tipo_etapa, cor_hex, icone)
            VALUES (%s, %s, %s, 1, 'separacao', '#17a2b8', 'fa-boxes')
        """, (
            'Separacao e Embalagem (Estoque)',
            'Produto ja produzido - apenas separar do estoque e embalar para envio',
            nova_ordem
        ))
        print(f"1. Etapa criada: ID={etapa_id}")
    
    # 2. Atualizar OPs de tipo separacao para usar esta etapa
    print(f"\n2. Atualizando OPs de separacao para etapa {etapa_id}...")
    affected = db.execute("""
        UPDATE ordens_producao 
        SET etapa_atual_id = %s 
        WHERE tipo_op = 'separacao'
    """, (etapa_id,))
    print(f"   {affected} OP(s) atualizada(s)")
    
    # 3. Atualizar lotes dessas OPs
    print(f"\n3. Atualizando lotes das OPs de separacao...")
    affected_lotes = db.execute("""
        UPDATE op_lotes l
        INNER JOIN ordens_producao op ON op.id = l.ordem_producao_id
        SET l.etapa_atual_id = %s
        WHERE op.tipo_op = 'separacao'
    """, (etapa_id,))
    print(f"   {affected_lotes} lote(s) atualizado(s)")
    
    # 4. Verificar resultado
    print(f"\n4. Verificando OPs de separacao:")
    ops_sep = db.fetch_all("""
        SELECT op.id, op.numero_op, op.quantidade, op.etapa_atual_id, e.nome as etapa_nome
        FROM ordens_producao op
        LEFT JOIN producao_etapas e ON e.id = op.etapa_atual_id
        WHERE op.tipo_op = 'separacao'
    """)
    for op in ops_sep:
        print(f"   OP {op['numero_op']}: etapa={op['etapa_atual_id']} ({op.get('etapa_nome')})")
    
    # 5. Verificar se etapa esta visivel no Gantt (precisa estar no grupo correto)
    print(f"\n5. Verificando grupos de etapas:")
    grupos = db.fetch_all("SELECT * FROM producao_etapas_grupos WHERE ativo = 1 ORDER BY ordem")
    for g in grupos:
        print(f"   Grupo ID={g['id']}: {g['nome']}")
    
    # Associar etapa ao primeiro grupo se nao tiver grupo
    etapa_atual = db.fetch_one("SELECT * FROM producao_etapas WHERE id = %s", (etapa_id,))
    if etapa_atual and not etapa_atual.get('grupo_etapas_id') and grupos:
        print(f"\n6. Associando etapa ao grupo {grupos[0]['id']}...")
        db.execute("UPDATE producao_etapas SET grupo_etapas_id = %s WHERE id = %s", 
                   (grupos[0]['id'], etapa_id))
        print("   OK")
    
    print("\n=== CONCLUIDO ===")
    print(f"Etapa de Separacao: ID={etapa_id}")
    print("As OPs de separacao agora devem aparecer no Gantt")

if __name__ == "__main__":
    main()
