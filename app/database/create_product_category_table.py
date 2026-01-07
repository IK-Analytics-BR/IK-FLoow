import sys
import os
import mysql.connector
from mysql.connector import Error

# Adicionar o diretório pai ao caminho de importação
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configurações do banco de dados
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'aritana',
    'database': 'supply_chain_system'
}

def create_product_category_table():
    """Cria a tabela para Categorias de produtos"""
    # Definir os comandos SQL para criar a tabela
    sql_commands = [
        """
        CREATE TABLE IF NOT EXISTS product_categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE INDEX idx_product_categories_name ON product_categories(name)
        """
    ]
    
    # Verificar se a coluna já existe na tabela products antes de adicioná-la
    alter_commands = [
        """
        SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_schema = 'supply_chain_system' 
        AND table_name = 'products' 
        AND column_name = 'category_id'
        """
    ]
    
    try:
        # Conectar ao banco de dados
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Executar os comandos para criar a tabela
        for command in sql_commands:
            print(f"Executando: {command[:50]}...")
            cursor.execute(command)
        
        # Verificar se a coluna já existe e adicionar se necessário
        for check_command in alter_commands:
            cursor.execute(check_command)
            result = cursor.fetchone()
            
            if result[0] == 0:  # Se a coluna não existe
                print(f"Adicionando coluna category_id à tabela products...")
                cursor.execute("ALTER TABLE products ADD COLUMN category_id INT")
                cursor.execute("ALTER TABLE products ADD CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES product_categories(id)")
        
        # Commit das alterações
        connection.commit()
        print("Tabela de categorias de produtos criada com sucesso!")
        
    except Error as e:
        print(f"Erro ao criar a tabela de categorias: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    create_product_category_table()
