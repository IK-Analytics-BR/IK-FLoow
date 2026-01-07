"""
Script para executar os scripts SQL dos novos módulos.
"""

import mysql.connector
from mysql.connector import Error
import os

def execute_sql_file(file_path, connection):
    """Executa um arquivo SQL."""
    print(f"Executando arquivo SQL: {file_path}")
    
    try:
        cursor = connection.cursor()
        
        # Ler o arquivo SQL
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_file = f.read()
        
        # Dividir o arquivo em comandos SQL individuais
        sql_commands = sql_file.split(';')
        
        # Executar cada comando SQL
        for command in sql_commands:
            if command.strip():
                try:
                    cursor.execute(command)
                    connection.commit()
                except Error as e:
                    print(f"Erro ao executar comando: {e}")
        
        cursor.close()
        print(f"Execução concluída para {file_path}!")
        
    except Error as e:
        print(f"Erro ao executar o script SQL: {e}")

def main():
    """Função principal."""
    try:
        # Conectar ao banco de dados
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='root',
            database='supply_chain'
        )
        
        if connection.is_connected():
            print("Conexão estabelecida com o banco de dados!")
            
            # Caminho dos scripts SQL
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Executar os scripts SQL
            financial_script = os.path.join(script_dir, 'create_financial_tables.sql')
            purchase_script = os.path.join(script_dir, 'create_purchase_tables.sql')
            
            if os.path.exists(financial_script):
                execute_sql_file(financial_script, connection)
            else:
                print(f"Script não encontrado: {financial_script}")
            
            if os.path.exists(purchase_script):
                execute_sql_file(purchase_script, connection)
            else:
                print(f"Script não encontrado: {purchase_script}")
            
            connection.close()
            print("Conexão fechada.")
        
    except Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")

if __name__ == "__main__":
    main()
