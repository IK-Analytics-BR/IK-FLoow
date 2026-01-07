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

def add_missing_columns():
    """Adiciona as colunas faltantes na tabela de produtos"""
    try:
        # Conectar ao banco de dados
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Verificar e adicionar a coluna barcode
        try:
            cursor.execute("ALTER TABLE products ADD COLUMN barcode VARCHAR(50) NULL AFTER name")
            print("Coluna 'barcode' adicionada com sucesso!")
        except Error as e:
            if "Duplicate column name" in str(e):
                print("Coluna 'barcode' já existe.")
            else:
                print(f"Erro ao adicionar coluna 'barcode': {e}")
        
        # Verificar e adicionar a coluna cost_price
        try:
            cursor.execute("ALTER TABLE products ADD COLUMN cost_price DECIMAL(10,2) NULL AFTER price")
            print("Coluna 'cost_price' adicionada com sucesso!")
        except Error as e:
            if "Duplicate column name" in str(e):
                print("Coluna 'cost_price' já existe.")
            else:
                print(f"Erro ao adicionar coluna 'cost_price': {e}")
        
        # Verificar e adicionar a coluna margin
        try:
            cursor.execute("ALTER TABLE products ADD COLUMN margin DECIMAL(10,2) NULL AFTER cost_price")
            print("Coluna 'margin' adicionada com sucesso!")
        except Error as e:
            if "Duplicate column name" in str(e):
                print("Coluna 'margin' já existe.")
            else:
                print(f"Erro ao adicionar coluna 'margin': {e}")
        
        # Commit das alterações
        connection.commit()
        print("\nAlterações concluídas com sucesso!")
        
    except Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    add_missing_columns()
