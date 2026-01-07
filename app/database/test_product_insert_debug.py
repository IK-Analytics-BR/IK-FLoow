import mysql.connector
import sys
import os

def test_product_insert():
    """
    Testa a inserção direta de um produto no banco de dados para identificar o erro.
    """
    try:
        # Conectar ao banco de dados
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='aritana',
            database='supply_chain_system'
        )
        
        cursor = conn.cursor()
        
        # Dados do produto para teste
        name = "Produto Teste Debug"
        description = "Descrição do produto teste debug"
        barcode = "7891234567893"
        unit_measure = "UN"
        category = "outro"
        price = 100.00
        
        # Inserir produto com apenas os campos obrigatórios
        query = """
        INSERT INTO products (name, barcode, unit_measure, price, category, active)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        params = (name, barcode, unit_measure, price, category, True)
        
        print(f"Executando query: {query}")
        print(f"Parâmetros: {params}")
        
        cursor.execute(query, params)
        conn.commit()
        
        product_id = cursor.lastrowid
        print(f"Produto inserido com sucesso! ID: {product_id}")
        
        # Verificar se o produto foi inserido
        cursor.execute(f"SELECT * FROM products WHERE id = {product_id}")
        product = cursor.fetchone()
        if product:
            print("Produto encontrado no banco de dados!")
        else:
            print("Produto não encontrado no banco de dados!")
        
    except mysql.connector.Error as e:
        print(f"Erro ao inserir produto: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    test_product_insert()
