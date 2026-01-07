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

def debug_produto_cadastro():
    """Simula o cadastro de um produto para identificar o problema"""
    try:
        # Conectar ao banco de dados
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        # Verificar o esquema da tabela products
        print("\n1. Esquema da tabela 'products':")
        print("=" * 80)
        cursor.execute("DESCRIBE products")
        columns = cursor.fetchall()
        
        for column in columns:
            print(f"{column['Field']:<20} {column['Type']:<20} {column['Null']:<10} {column['Key']:<10}")
        
        # Simular uma inserção de produto
        print("\n2. Tentando inserir um produto de teste:")
        print("=" * 80)
        
        # Dados de teste
        name = "Produto Teste"
        description = "Descrição de teste"
        barcode = "123456789"
        cost_price = 100.00
        margin = 50.00
        price = 150.00
        category_id = None
        brand_id = None
        group_id = None
        subgroup_id = None
        
        # Verificar quais colunas são obrigatórias
        print("\n3. Colunas obrigatórias (NOT NULL):")
        print("=" * 80)
        required_columns = []
        for column in columns:
            if column['Null'] == 'NO' and column['Key'] != 'PRI' and column['Extra'] != 'auto_increment':
                required_columns.append(column['Field'])
                print(f"- {column['Field']}")
        
        # Tentar inserir o produto
        try:
            print("\n4. Executando INSERT:")
            print("=" * 80)
            
            # Construir a query baseada nas colunas existentes
            query = """
                INSERT INTO products (name, description, barcode, cost_price, margin, price, 
                                    category_id, brand_id, group_id, subgroup_id, category)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (name, description, barcode, cost_price, margin, price, 
                     category_id, brand_id, group_id, subgroup_id, "outro")  # Adicionando um valor para a coluna category
            
            print(f"Query: {query}")
            print(f"Params: {params}")
            
            cursor.execute(query, params)
            connection.commit()
            
            print("\nInserção bem-sucedida!")
            print(f"ID do produto inserido: {cursor.lastrowid}")
            
        except Error as e:
            print(f"\nErro ao inserir produto: {e}")
            print("\n5. Tentando identificar o problema:")
            print("=" * 80)
            
            # Verificar se o problema é a coluna category
            if "column 'category'" in str(e) and "cannot be null" in str(e):
                print("O problema é que a coluna 'category' não pode ser nula.")
                print("Tentando inserir com um valor para category...")
                
                try:
                    query = """
                        INSERT INTO products (name, description, barcode, cost_price, margin, price, 
                                            category_id, brand_id, group_id, subgroup_id, category)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    params = (name, description, barcode, cost_price, margin, price, 
                             category_id, brand_id, group_id, subgroup_id, "outro")
                    
                    cursor.execute(query, params)
                    connection.commit()
                    
                    print("\nInserção bem-sucedida com categoria 'outro'!")
                    print(f"ID do produto inserido: {cursor.lastrowid}")
                    
                except Error as e2:
                    print(f"\nErro ao inserir produto com categoria 'outro': {e2}")
            
    except Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("\nConexão com o banco de dados fechada.")

if __name__ == "__main__":
    debug_produto_cadastro()
