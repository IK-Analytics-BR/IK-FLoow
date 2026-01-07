import mysql.connector

def check_products_table():
    """Verifica a estrutura da tabela products."""
    try:
        # Conectar ao banco de dados
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='aritana',
            database='supply_chain_system'
        )
        
        cursor = conn.cursor()
        
        # Verificar a estrutura da tabela products
        cursor.execute("DESCRIBE products")
        columns = cursor.fetchall()
        
        print("Colunas da tabela products:")
        for column in columns:
            print(f"{column[0]} - {column[1]} - {column[2]} - {column[3]}")
        
    except mysql.connector.Error as e:
        print(f"Erro ao verificar tabela products: {e}")
    finally:
        # Fechar a conexão
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    check_products_table()
