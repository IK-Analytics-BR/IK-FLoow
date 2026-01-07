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

def execute_sql_file(file_path):
    """Executa um arquivo SQL com múltiplas queries"""
    try:
        # Conectar ao banco de dados
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print(f"Executando arquivo SQL: {file_path}")
        
        # Ler o arquivo SQL
        with open(file_path, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        
        # Dividir o script em comandos individuais
        # Considerando que cada comando termina com ponto e vírgula
        commands = sql_script.split(';')
        
        # Executar cada comando
        for command in commands:
            # Ignorar linhas vazias ou comentários
            command = command.strip()
            if command and not command.startswith('--'):
                try:
                    cursor.execute(command)
                    print(f"Comando executado com sucesso: {command[:50]}...")
                except Error as e:
                    if "Duplicate column name" in str(e) or "already exists" in str(e):
                        print(f"Aviso: {e}")
                    else:
                        print(f"Erro ao executar comando: {e}")
                        print(f"Comando: {command}")
        
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
    # Caminho do arquivo SQL
    sql_file_path = os.path.join(os.path.dirname(__file__), 'update_product_fields.sql')
    
    # Verificar se o arquivo existe
    if not os.path.exists(sql_file_path):
        print(f"Arquivo não encontrado: {sql_file_path}")
        sys.exit(1)
    
    # Executar o arquivo SQL
    execute_sql_file(sql_file_path)
