import mysql.connector

def test_db_permissions():
    """Testa as permissões do banco de dados para inserção de produtos."""
    try:
        # Conectar ao banco de dados
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='aritana',
            database='supply_chain_system'
        )
        
        cursor = conn.cursor()
        
        print("Conexão com o banco de dados estabelecida com sucesso!")
        
        # Verificar permissões
        cursor.execute("SHOW GRANTS FOR CURRENT_USER")
        grants = cursor.fetchall()
        
        print("Permissões do usuário atual:")
        for grant in grants:
            print(grant[0])
        
        # Testar inserção direta
        print("\nTestando inserção direta na tabela products...")
        
        # Dados do produto para teste
        name = "Produto Teste Permissões"
        price = 150.00
        category = "outro"
        active = True
        
        # Inserir produto com campos mínimos
        query = "INSERT INTO products (name, price, category, active) VALUES (%s, %s, %s, %s)"
        params = (name, price, category, active)
        
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
        
        # Limpar o teste
        cursor.execute(f"DELETE FROM products WHERE id = {product_id}")
        conn.commit()
        print(f"Produto de teste removido do banco de dados.")
        
    except mysql.connector.Error as e:
        print(f"Erro ao testar permissões do banco de dados: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    test_db_permissions()
