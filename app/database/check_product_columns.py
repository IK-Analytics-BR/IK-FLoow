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

def check_product_columns():
    """Verifica as colunas da tabela de produtos"""
    try:
        # Conectar ao banco de dados
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        # Verificar se as colunas existem na tabela products
        cursor.execute("DESCRIBE products")
        columns = cursor.fetchall()
        
        print("\nColunas da tabela 'products':")
        print("=" * 60)
        print(f"{'Nome da Coluna':<20} {'Tipo':<20} {'Nulo':<10} {'Chave':<10}")
        print("-" * 60)
        
        for column in columns:
            print(f"{column['Field']:<20} {column['Type']:<20} {column['Null']:<10} {column['Key']:<10}")
        
        # Verificar colunas específicas
        required_columns = [
            'category_id', 'brand_id', 'group_id', 'subgroup_id', 
            'barcode', 'cost_price', 'margin', 'price'
        ]
        
        print("\nVerificação de colunas específicas:")
        print("=" * 60)
        
        for col_name in required_columns:
            exists = any(column['Field'] == col_name for column in columns)
            print(f"Coluna '{col_name}': {'EXISTE' if exists else 'NÃO EXISTE'}")
        
    except Error as e:
        print(f"Erro ao verificar colunas: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("\nConexão com o banco de dados fechada.")

if __name__ == "__main__":
    check_product_columns()
