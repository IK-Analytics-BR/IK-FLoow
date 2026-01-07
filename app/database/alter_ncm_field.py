import mysql.connector

def alter_ncm_field():
    """Altera o tamanho do campo NCM na tabela products."""
    try:
        # Conectar ao banco de dados
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='aritana',
            database='supply_chain_system'
        )
        
        cursor = conn.cursor()
        
        # Verificar o tamanho atual do campo NCM
        cursor.execute("SHOW COLUMNS FROM products LIKE 'ncm'")
        column_info = cursor.fetchone()
        print(f"Informações atuais do campo NCM: {column_info}")
        
        # Alterar o tamanho do campo NCM para VARCHAR(20)
        print("Alterando o tamanho do campo NCM para VARCHAR(20)...")
        cursor.execute("ALTER TABLE products MODIFY COLUMN ncm VARCHAR(20)")
        
        # Verificar o novo tamanho do campo NCM
        cursor.execute("SHOW COLUMNS FROM products LIKE 'ncm'")
        column_info = cursor.fetchone()
        print(f"Novas informações do campo NCM: {column_info}")
        
        # Commit das alterações
        conn.commit()
        print("Alteração concluída com sucesso!")
        
    except mysql.connector.Error as e:
        print(f"Erro ao alterar o campo NCM: {e}")
    finally:
        # Fechar a conexão
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    alter_ncm_field()
