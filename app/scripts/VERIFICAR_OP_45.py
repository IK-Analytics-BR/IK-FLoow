# -*- coding: utf-8 -*-
"""
Verificar detalhes da OP 45 e seu orcamento de origem
"""
import sys
sys.path.insert(0, 'c:/Users/arita/CascadeProjects/SupplyChainSystem')

from app.database import Database

def main():
    db = Database()
    
    print("=== INVESTIGACAO OP 45 ===\n")
    
    # 1. Dados da OP 45
    op = db.fetch_one("SELECT * FROM ordens_producao WHERE id = 45")
    print(f"1. OP 45:")
    print(f"   numero_op: {op.get('numero_op')}")
    print(f"   quantidade: {op['quantidade']}")
    print(f"   produto_id: {op['produto_id']}")
    print(f"   cliente_id: {op.get('cliente_id')}")
    print(f"   empresa_id: {op.get('empresa_id')}")
    print(f"   observacoes: {op.get('observacoes')}")
    
    # 2. Buscar vinculo com orcamento
    vinculo = db.fetch_one("""
        SELECT * FROM orcamento_op_itens WHERE ordem_producao_id = 45
    """)
    if vinculo:
        print(f"\n2. Vinculo orcamento_op_itens:")
        print(f"   orcamento_id: {vinculo['orcamento_id']}")
        print(f"   orcamento_item_id: {vinculo['orcamento_item_id']}")
        print(f"   quantidade no vinculo: {vinculo['quantidade']}")
        
        # 3. Buscar orcamento
        orc = db.fetch_one("SELECT * FROM orcamentos WHERE id = %s", (vinculo['orcamento_id'],))
        print(f"\n3. Orcamento:")
        print(f"   numero: {orc['numero']}")
        print(f"   status: {orc['status']}")
        
        # 4. Buscar item do orcamento
        item = db.fetch_one("SELECT * FROM orcamento_itens WHERE id = %s", (vinculo['orcamento_item_id'],))
        print(f"\n4. Item do orcamento:")
        print(f"   produto_id: {item['produto_id']}")
        print(f"   quantidade: {item['quantidade']}")
        print(f"   qtd_estoque_alocada: {item.get('qtd_estoque_alocada')}")
        print(f"   qtd_a_produzir: {item.get('qtd_a_produzir')}")
    else:
        print("\n2. SEM vinculo com orcamento_op_itens!")
        # Tentar encontrar pelo observacoes
        if op.get('observacoes'):
            print(f"   observacoes: {op.get('observacoes')}")
    
    # 5. Verificar etapa 10
    etapa = db.fetch_one("SELECT * FROM producao_etapas WHERE id = 10")
    print(f"\n5. Etapa 10:")
    if etapa:
        print(f"   nome: {etapa['nome']}")
        print(f"   tipo_etapa: {etapa.get('tipo_etapa')}")
        print(f"   ativo: {etapa.get('ativo')}")
    
    # 6. Verificar filtros do Gantt - etapas ativas
    print(f"\n6. Etapas ativas no sistema:")
    etapas = db.fetch_all("SELECT id, nome, tipo_etapa, ativo FROM producao_etapas WHERE ativo = 1 ORDER BY ordem")
    for e in etapas:
        print(f"   ID={e['id']}: {e['nome']} (tipo={e.get('tipo_etapa')})")

if __name__ == "__main__":
    main()
