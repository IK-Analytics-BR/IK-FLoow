# -*- coding: utf-8 -*-
"""
Preparar teste completo do fluxo de OP com estoque
"""
import sys
sys.path.insert(0, 'c:/Users/arita/CascadeProjects/SupplyChainSystem')

from app.database import Database

def main():
    db = Database()
    
    print("=" * 70)
    print("PREPARANDO TESTE COMPLETO")
    print("=" * 70)
    
    # 1. Buscar orcamento ORC-2025-0026
    orc = db.fetch_one("SELECT * FROM orcamentos WHERE numero = 'ORC-2025-0026'")
    orc_id = orc['id']
    print(f"\n1. Orcamento: ID={orc_id}, Numero={orc['numero']}")
    
    # 2. Limpar dados anteriores
    print("\n2. Limpando dados anteriores...")
    db.execute("DELETE FROM estoque_movimentacoes WHERE referencia_tipo = 'orcamento' AND referencia_id = %s", (orc_id,))
    db.execute("DELETE FROM estoque_reservas WHERE tipo_origem = 'orcamento' AND origem_id = %s", (orc_id,))
    db.execute("DELETE FROM orcamento_op_itens WHERE orcamento_id = %s", (orc_id,))
    db.execute("DELETE FROM orcamento_op_grupos WHERE orcamento_id = %s", (orc_id,))
    print("   [OK]")
    
    # 3. Resetar item do orcamento
    print("\n3. Resetando item do orcamento...")
    db.execute("""
        UPDATE orcamento_itens 
        SET status_alocacao = 'pendente', qtd_estoque_alocada = 0, qtd_a_produzir = 0
        WHERE orcamento_id = %s
    """, (orc_id,))
    print("   [OK]")
    
    # 4. Resetar status do orcamento
    print("\n4. Resetando status do orcamento para 'enviado'...")
    db.execute("""
        UPDATE orcamentos SET status = 'enviado', data_aprovacao = NULL WHERE id = %s
    """, (orc_id,))
    print("   [OK]")
    
    # 5. Verificar e ajustar estoque do produto
    item = db.fetch_one("""
        SELECT oi.produto_id, oi.quantidade, p.name, p.stock_quantity
        FROM orcamento_itens oi
        JOIN products p ON p.id = oi.produto_id
        WHERE oi.orcamento_id = %s
    """, (orc_id,))
    
    print(f"\n5. Produto: {item['name']}")
    print(f"   Quantidade no orcamento: {item['quantidade']}")
    print(f"   Estoque atual: {item['stock_quantity']}")
    
    # Garantir estoque suficiente
    qtd_necessaria = float(item['quantidade']) + 10
    if float(item['stock_quantity'] or 0) < qtd_necessaria:
        print(f"\n6. Ajustando estoque para {qtd_necessaria}...")
        db.execute("UPDATE products SET stock_quantity = %s WHERE id = %s", 
                   (qtd_necessaria, item['produto_id']))
        print("   [OK]")
    else:
        print(f"\n6. Estoque suficiente: {item['stock_quantity']}")
    
    # 7. Verificar etapa de separacao
    etapa_sep = db.fetch_one("SELECT * FROM producao_etapas WHERE tipo_etapa = 'separacao'")
    if etapa_sep:
        print(f"\n7. Etapa de Separacao: ID={etapa_sep['id']}, nome={etapa_sep['nome']}")
    else:
        print("\n7. [AVISO] Etapa de separacao NAO encontrada!")
    
    print("\n" + "=" * 70)
    print("TESTE PRONTO!")
    print("=" * 70)
    print(f"\n1. Acesse: http://127.0.0.1:8080/orcamentos/{orc_id}")
    print("2. Clique em APROVAR")
    print("3. Deve criar OP de SEPARACAO")
    print("4. Estoque deve ser BAIXADO")
    print("5. OP deve aparecer no Gantt: http://127.0.0.1:8080/industria/ordem-producao/producao/gantt")
    print("\nVerifique no terminal do servidor as mensagens de [ESTOQUE]")

if __name__ == "__main__":
    main()
