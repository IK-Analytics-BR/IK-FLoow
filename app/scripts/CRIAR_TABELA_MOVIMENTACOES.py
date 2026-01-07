# -*- coding: utf-8 -*-
"""
Criar tabela de movimentações de estoque
"""
import sys
sys.path.insert(0, 'c:/Users/arita/CascadeProjects/SupplyChainSystem')

from app.database import Database

def main():
    db = Database()
    
    print("=== CRIANDO TABELA ESTOQUE_MOVIMENTACOES ===\n")
    
    # 1. Criar tabela
    print("1. Criando tabela estoque_movimentacoes...")
    try:
        db.execute("""
            CREATE TABLE IF NOT EXISTS estoque_movimentacoes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                produto_id INT NOT NULL,
                tipo ENUM('entrada', 'saida', 'ajuste', 'reserva', 'baixa_producao', 'devolucao') NOT NULL,
                quantidade DECIMAL(15,4) NOT NULL,
                estoque_anterior DECIMAL(15,4),
                estoque_posterior DECIMAL(15,4),
                referencia_tipo VARCHAR(50),
                referencia_id INT,
                custo_unitario DECIMAL(15,4),
                local_origem VARCHAR(100),
                local_destino VARCHAR(100),
                observacao TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by INT,
                INDEX idx_produto (produto_id),
                INDEX idx_tipo (tipo),
                INDEX idx_referencia (referencia_tipo, referencia_id),
                INDEX idx_data (created_at)
            )
        """)
        print("   [OK] Tabela criada")
    except Exception as e:
        if "already exists" in str(e):
            print("   [JA EXISTE]")
        else:
            print(f"   [ERRO] {e}")
    
    print("\n=== CONCLUIDO ===")

if __name__ == "__main__":
    main()
