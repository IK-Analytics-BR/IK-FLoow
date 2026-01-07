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

def execute_sql_file(file_path):
    """Executa os comandos SQL de um arquivo"""
    try:
        # Conectar ao banco de dados
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Ler o arquivo SQL
        with open(file_path, 'r') as file:
            sql_script = file.read()
        
        # Dividir o script em comandos individuais
        sql_commands = sql_script.split(';')
        
        # Executar cada comando
        for command in sql_commands:
            if command.strip():
                print(f"Executando: {command[:50]}...")
                cursor.execute(command)
        
        # Commit das alterações
        connection.commit()
        print("Script SQL executado com sucesso!")
        
    except Error as e:
        print(f"Erro ao executar o script SQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Conexão com o banco de dados fechada.")

def create_product_tables():
    """Cria as tabelas para Marca, Grupo e Subgrupo de produtos"""
    # Definir os comandos SQL para criar as tabelas
    sql_commands = [
        """
        CREATE TABLE IF NOT EXISTS product_brands (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS product_groups (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS product_subgroups (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            group_id INT NOT NULL,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES product_groups(id)
        )
        """,
        """
        CREATE INDEX idx_product_brands_name ON product_brands(name)
        """,
        """
        CREATE INDEX idx_product_groups_name ON product_groups(name)
        """,
        """
        CREATE INDEX idx_product_subgroups_name ON product_subgroups(name)
        """,
        """
        CREATE INDEX idx_product_subgroups_group_id ON product_subgroups(group_id)
        """
    ]
    
    # Verificar se as colunas já existem na tabela products antes de adicioná-las
    alter_commands = [
        """
        SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_schema = 'supply_chain_system' 
        AND table_name = 'products' 
        AND column_name = 'brand_id'
        """,
        """
        SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_schema = 'supply_chain_system' 
        AND table_name = 'products' 
        AND column_name = 'group_id'
        """,
        """
        SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_schema = 'supply_chain_system' 
        AND table_name = 'products' 
        AND column_name = 'subgroup_id'
        """
    ]
    
    try:
        # Conectar ao banco de dados
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Executar os comandos para criar as tabelas
        for command in sql_commands:
            print(f"Executando: {command[:50]}...")
            cursor.execute(command)
        
        # Verificar se as colunas já existem e adicionar se necessário
        for i, check_command in enumerate(alter_commands):
            cursor.execute(check_command)
            result = cursor.fetchone()
            
            if result[0] == 0:  # Se a coluna não existe
                column_name = check_command.split("column_name = '")[1].split("'")[0]
                print(f"Adicionando coluna {column_name} à tabela products...")
                
                if column_name == 'brand_id':
                    cursor.execute("ALTER TABLE products ADD COLUMN brand_id INT")
                    cursor.execute("ALTER TABLE products ADD CONSTRAINT fk_products_brand FOREIGN KEY (brand_id) REFERENCES product_brands(id)")
                elif column_name == 'group_id':
                    cursor.execute("ALTER TABLE products ADD COLUMN group_id INT")
                    cursor.execute("ALTER TABLE products ADD CONSTRAINT fk_products_group FOREIGN KEY (group_id) REFERENCES product_groups(id)")
                elif column_name == 'subgroup_id':
                    cursor.execute("ALTER TABLE products ADD COLUMN subgroup_id INT")
                    cursor.execute("ALTER TABLE products ADD CONSTRAINT fk_products_subgroup FOREIGN KEY (subgroup_id) REFERENCES product_subgroups(id)")
        
        # Commit das alterações
        connection.commit()
        print("Tabelas criadas com sucesso!")
        
    except Error as e:
        print(f"Erro ao criar as tabelas: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    # Executar o script SQL do arquivo
    # script_path = os.path.join(os.path.dirname(__file__), 'product_tables.sql')
    # execute_sql_file(script_path)
    
    # Ou criar as tabelas diretamente
    create_product_tables()
