import mysql.connector
import os
import sys

def execute_sql_file(file_path):
    """
    Executa um arquivo SQL no banco de dados MySQL
    """
    try:
        # Conectar ao banco de dados
        print(f"Conectando ao banco de dados MySQL...")
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='aritana',
            database='supply_chain_system',
            autocommit=True
        )
        
        if connection.is_connected():
            print(f"Conexão estabelecida com sucesso!")
            
            # Ler o arquivo SQL
            print(f"Lendo arquivo SQL: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as file:
                sql_script = file.read()
            
            # Dividir o script em comandos individuais
            sql_commands = sql_script.split(';')
            
            # Executar cada comando
            cursor = connection.cursor()
            count = 0
            for command in sql_commands:
                if command.strip():
                    print(f"Executando comando SQL #{count+1}...")
                    cursor.execute(command)
                    count += 1
            
            print(f"Execução concluída! {count} comandos executados com sucesso.")
            
            # Fechar cursor e conexão
            cursor.close()
            connection.close()
            print("Conexão fechada.")
            
            return True
        else:
            print("Falha ao conectar ao banco de dados.")
            return False
            
    except Exception as e:
        print(f"Erro ao executar o script SQL: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Usar o arquivo combinado por padrão
        file_path = os.path.join(os.path.dirname(__file__), "insert_all_teste.sql")
    
    if os.path.exists(file_path):
        execute_sql_file(file_path)
    else:
        print(f"Arquivo não encontrado: {file_path}")
