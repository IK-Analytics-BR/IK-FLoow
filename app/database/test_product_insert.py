import mysql.connector
import datetime

def test_product_insert():
    try:
        # Conectar ao banco de dados
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='aritana',
            database='supply_chain_system'
        )
        
        cursor = conn.cursor()
        
        # Consultar a estrutura da tabela products
        cursor.execute("DESCRIBE products")
        columns = cursor.fetchall()
        print("Estrutura da tabela products:")
        for column in columns:
            print(f"{column[0]} - {column[1]} - {column[2]} - {column[3]}")
        
        # Inserir um produto de teste
        query = """
        INSERT INTO products (
            internal_code, name, description, barcode, unit_measure, 
            category_id, brand_id, group_id, subgroup_id,
            price, cost_price, margin, max_discount,
            active, category
        ) VALUES (
            'TEST001', 'Produto Teste', 'Descrição do produto teste', '7891234567890', 'UN',
            NULL, NULL, NULL, NULL,
            100.00, 50.00, 100.00, 10.00,
            TRUE, 'outro'
        )
        """
        
        cursor.execute(query)
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
