import mysql.connector

def add_ncm_column():
    """Adiciona a coluna NCM à tabela products."""
    try:
        # Conectar ao banco de dados
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='aritana',
            database='supply_chain_system'
        )
        
        cursor = conn.cursor()
        
        # Verificar se a coluna NCM já existe
        cursor.execute("SHOW COLUMNS FROM products LIKE 'ncm'")
        ncm_exists = cursor.fetchone()
        
        if not ncm_exists:
            print("Adicionando coluna NCM à tabela products...")
            cursor.execute("ALTER TABLE products ADD COLUMN ncm VARCHAR(8) DEFAULT NULL COMMENT 'Nomenclatura Comum do Mercosul' AFTER unit_measure")
            print("Coluna NCM adicionada com sucesso!")
        else:
            print("A coluna NCM já existe na tabela products.")
        
        # Commit das alterações
        conn.commit()
        
    except mysql.connector.Error as e:
        print(f"Erro ao adicionar coluna NCM: {e}")
    finally:
        # Fechar a conexão
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    add_ncm_column()
