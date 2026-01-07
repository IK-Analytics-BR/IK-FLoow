"""
Script para criar tabela estoque_empresa e atualizar estrutura do banco.
"""
import pymysql

# Configuração do banco
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'aritana',
    'database': 'supply_chain_system',
    'charset': 'utf8mb4'
}

def executar():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # 1. Criar tabela estoque_empresa
        print("Criando tabela estoque_empresa...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS estoque_empresa (
                id INT AUTO_INCREMENT PRIMARY KEY,
                empresa_id INT NOT NULL,
                produto_id INT NOT NULL,
                quantidade DECIMAL(15,4) DEFAULT 0,
                quantidade_reservada DECIMAL(15,4) DEFAULT 0,
                custo_medio DECIMAL(15,4) DEFAULT 0,
                ultimo_custo DECIMAL(15,4) DEFAULT 0,
                local_id INT DEFAULT 1,
                estoque_minimo DECIMAL(15,4) DEFAULT 0,
                estoque_maximo DECIMAL(15,4) DEFAULT 0,
                ultima_entrada DATETIME NULL,
                ultima_saida DATETIME NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                UNIQUE KEY uk_empresa_produto_local (empresa_id, produto_id, local_id),
                INDEX idx_empresa (empresa_id),
                INDEX idx_produto (produto_id),
                INDEX idx_quantidade (quantidade)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        conn.commit()
        print("[OK] Tabela estoque_empresa criada")
        
        # 2. Verificar e adicionar coluna empresa_id em estoque_movimentacoes
        print("Verificando coluna empresa_id em estoque_movimentacoes...")
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'supply_chain_system' 
            AND TABLE_NAME = 'estoque_movimentacoes' 
            AND COLUMN_NAME = 'empresa_id'
        """)
        result = cursor.fetchone()
        
        if result[0] == 0:
            print("Adicionando coluna empresa_id...")
            cursor.execute("""
                ALTER TABLE estoque_movimentacoes 
                ADD COLUMN empresa_id INT NULL AFTER id
            """)
            conn.commit()
            print("[OK] Coluna empresa_id adicionada")
        else:
            print("[OK] Coluna empresa_id ja existe")
        
        # 3. Criar índice para empresa_id
        print("Criando índice idx_mov_empresa...")
        try:
            cursor.execute("""
                ALTER TABLE estoque_movimentacoes 
                ADD INDEX idx_mov_empresa (empresa_id)
            """)
            conn.commit()
            print("[OK] Indice criado")
        except Exception as e:
            if "Duplicate key name" in str(e):
                print("[OK] Indice ja existe")
            else:
                print(f"Aviso: {e}")
        
        # 4. Atualizar movimentações existentes com empresa padrão
        print("Atualizando movimentações existentes com empresa_id = 1...")
        cursor.execute("""
            UPDATE estoque_movimentacoes 
            SET empresa_id = 1 
            WHERE empresa_id IS NULL
        """)
        conn.commit()
        print(f"[OK] {cursor.rowcount} movimentacoes atualizadas")
        
        # 5. Migrar dados de products.stock_quantity para empresa padrão
        print("Migrando estoque de products para estoque_empresa...")
        cursor.execute("""
            INSERT INTO estoque_empresa (empresa_id, produto_id, quantidade, local_id)
            SELECT 
                1 as empresa_id,
                p.id as produto_id,
                COALESCE(p.stock_quantity, 0) as quantidade,
                1 as local_id
            FROM products p
            WHERE p.active = 1
            ON DUPLICATE KEY UPDATE 
                quantidade = VALUES(quantidade)
        """)
        conn.commit()
        print(f"[OK] {cursor.rowcount} produtos migrados para estoque_empresa")
        
        # 6. Criar índices adicionais
        print("Criando índices adicionais...")
        try:
            cursor.execute("""
                ALTER TABLE estoque_movimentacoes 
                ADD INDEX idx_mov_empresa_produto (empresa_id, produto_id)
            """)
            conn.commit()
        except:
            pass
        
        try:
            cursor.execute("""
                ALTER TABLE estoque_movimentacoes 
                ADD INDEX idx_mov_data (created_at)
            """)
            conn.commit()
        except:
            pass
        print("[OK] Indices criados")
        
        # 7. Verificar resultado
        cursor.execute("SELECT COUNT(*) FROM estoque_empresa")
        total = cursor.fetchone()[0]
        print(f"\n[SUCCESS] Script executado com sucesso!")
        print(f"   Total de registros em estoque_empresa: {total}")
        
    except Exception as e:
        print(f"[ERROR] Erro: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    executar()
