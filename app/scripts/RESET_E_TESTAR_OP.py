# -*- coding: utf-8 -*-
"""
Reset orçamento ORC-2025-0026 e testar geração de OP
"""
import sys
sys.path.insert(0, 'c:/Users/arita/CascadeProjects/SupplyChainSystem')

from app.database import Database

def main():
    db = Database()
    
    print("=== RESET E TESTE DE OP ===\n")
    
    # 1. Buscar orcamento
    orc = db.fetch_one("SELECT * FROM orcamentos WHERE numero = 'ORC-2025-0026'")
    orc_id = orc['id']
    print(f"Orcamento ID: {orc_id}")
    
    # 2. Limpar vinculos anteriores
    print("\n1. Limpando vinculos anteriores...")
    db.execute("DELETE FROM orcamento_op_itens WHERE orcamento_id = %s", (orc_id,))
    db.execute("DELETE FROM orcamento_op_grupos WHERE orcamento_id = %s", (orc_id,))
    db.execute("DELETE FROM estoque_reservas WHERE tipo_origem = 'orcamento' AND origem_id = %s", (orc_id,))
    print("   [OK] Vinculos limpos")
    
    # 3. Resetar status do item
    print("\n2. Resetando status dos itens...")
    db.execute("""
        UPDATE orcamento_itens 
        SET status_alocacao = 'pendente', qtd_estoque_alocada = 0, qtd_a_produzir = 0
        WHERE orcamento_id = %s
    """, (orc_id,))
    print("   [OK] Itens resetados")
    
    # 4. Resetar status do orcamento para 'enviado' para poder aprovar novamente
    print("\n3. Resetando status do orcamento para 'enviado'...")
    db.execute("""
        UPDATE orcamentos SET status = 'enviado', data_aprovacao = NULL WHERE id = %s
    """, (orc_id,))
    print("   [OK] Orcamento resetado para 'enviado'")
    
    # 5. Verificar estoque do produto
    item = db.fetch_one("""
        SELECT oi.produto_id, oi.quantidade, p.name, p.stock_quantity
        FROM orcamento_itens oi
        JOIN products p ON p.id = oi.produto_id
        WHERE oi.orcamento_id = %s
    """, (orc_id,))
    
    print(f"\n4. Produto: {item['name']}")
    print(f"   Quantidade no orcamento: {item['quantidade']}")
    print(f"   Estoque atual: {item['stock_quantity']}")
    
    # Se não tem estoque, adicionar para teste
    if not item['stock_quantity'] or float(item['stock_quantity']) < float(item['quantidade']):
        print(f"\n5. Adicionando estoque para teste...")
        db.execute("UPDATE products SET stock_quantity = %s WHERE id = %s", 
                   (float(item['quantidade']) + 10, item['produto_id']))
        print(f"   [OK] Estoque atualizado para {float(item['quantidade']) + 10}")
    else:
        print(f"\n5. Estoque suficiente: {item['stock_quantity']}")
    
    print("\n=== PRONTO PARA TESTAR ===")
    print("Agora va ao sistema, acesse o orcamento ORC-2025-0026 e clique em APROVAR")
    print("URL: http://127.0.0.1:8080/orcamentos/46")

if __name__ == "__main__":
    main()
