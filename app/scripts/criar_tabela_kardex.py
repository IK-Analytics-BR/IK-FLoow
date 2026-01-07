"""Script para criar/atualizar tabela de movimentações Kardex."""
import pymysql

def get_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='aritana',
        database='supply_chain_system',
        autocommit=True
    )

def criar_tabela():
    conn = get_db()
    db = conn.cursor()
    
    # Criar tabela principal
    db.execute("""
        CREATE TABLE IF NOT EXISTS estoque_movimentacoes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            produto_id INT NOT NULL,
            tipo VARCHAR(50) NOT NULL,
            quantidade DECIMAL(15,4) NOT NULL,
            estoque_anterior DECIMAL(15,4) DEFAULT 0,
            estoque_posterior DECIMAL(15,4) DEFAULT 0,
            origem_tela VARCHAR(100),
            origem_rota VARCHAR(200),
            referencia_tipo VARCHAR(50),
            referencia_id INT,
            referencia_codigo VARCHAR(100),
            custo_unitario DECIMAL(15,4),
            valor_total DECIMAL(15,4),
            local_id INT DEFAULT 1,
            local_nome VARCHAR(100),
            observacao TEXT,
            usuario_id INT,
            usuario_nome VARCHAR(100),
            ip_address VARCHAR(45),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_produto (produto_id),
            INDEX idx_tipo (tipo),
            INDEX idx_data (created_at)
        )
    """)
    print("Tabela estoque_movimentacoes criada/verificada!")
    
    # Verificar se colunas novas existem, se não adicionar
    try:
        db.execute("ALTER TABLE estoque_movimentacoes ADD COLUMN origem_tela VARCHAR(100)")
        print("Coluna origem_tela adicionada")
    except:
        pass
    
    try:
        db.execute("ALTER TABLE estoque_movimentacoes ADD COLUMN origem_rota VARCHAR(200)")
        print("Coluna origem_rota adicionada")
    except:
        pass
    
    try:
        db.execute("ALTER TABLE estoque_movimentacoes ADD COLUMN referencia_codigo VARCHAR(100)")
        print("Coluna referencia_codigo adicionada")
    except:
        pass
    
    try:
        db.execute("ALTER TABLE estoque_movimentacoes ADD COLUMN usuario_nome VARCHAR(100)")
        print("Coluna usuario_nome adicionada")
    except:
        pass
    
    try:
        db.execute("ALTER TABLE estoque_movimentacoes ADD COLUMN ip_address VARCHAR(45)")
        print("Coluna ip_address adicionada")
    except:
        pass
    
    try:
        db.execute("ALTER TABLE estoque_movimentacoes ADD COLUMN local_nome VARCHAR(100)")
        print("Coluna local_nome adicionada")
    except:
        pass
    
    try:
        db.execute("ALTER TABLE estoque_movimentacoes ADD COLUMN valor_total DECIMAL(15,4)")
        print("Coluna valor_total adicionada")
    except:
        pass
    
    print("\n✅ Sistema Kardex configurado com sucesso!")

if __name__ == '__main__':
    criar_tabela()
