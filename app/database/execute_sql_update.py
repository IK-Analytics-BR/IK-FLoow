import mysql.connector
import os

def execute_sql_file(file_path):
    """Executa um arquivo SQL no banco de dados MySQL."""
    try:
        # Conectar ao banco de dados
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='aritana',
            database='supply_chain_system'
        )
        
        print(f"Executando arquivo SQL: {file_path}")
        
        # Ler o arquivo SQL
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Dividir o script em comandos individuais
        commands = sql_script.split(';')
        
        # Executar cada comando
        cursor = conn.cursor()
        for cmd in commands:
            cmd = cmd.strip()
            if cmd:
                try:
                    cursor.execute(cmd)
                    print(f"Comando executado com sucesso: {cmd[:50]}...")
                except Exception as e:
                    print(f"Erro ao executar comando: {e}")
                    print(f"Comando: {cmd}")
        
        # Commit das alterações
        conn.commit()
        
        print("Alterações concluídas com sucesso!")
        
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        # Fechar a conexão
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    # Caminho para o arquivo SQL
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file = os.path.join(script_dir, "update_product_and_units.sql")
    
    # Executar o arquivo SQL
    execute_sql_file(sql_file)
