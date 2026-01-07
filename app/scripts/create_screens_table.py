"""
Script para criar a tabela de controle de telas no banco de dados
"""

import os
import mysql.connector
from dotenv import load_dotenv
import sys

# Adicionar o diretório pai ao caminho de importação
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco de dados
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'aritana')
DB_NAME = os.getenv('DB_NAME', 'supply_chain_system')

def create_screens_table():
    """Cria a tabela de controle de telas no banco de dados"""
    try:
        # Conectar ao banco de dados
        print("\n[DEBUG] Conectando ao banco de dados...")
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor(dictionary=True)
        print("[DEBUG] Conexão estabelecida com sucesso!")
        
        # Ler o arquivo SQL
        sql_file_path = os.path.join(os.path.dirname(__file__), 'create_screens_table.sql')
        print(f"[DEBUG] Lendo arquivo SQL: {sql_file_path}")
        
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        
        # Executar o script SQL
        print("[DEBUG] Executando script SQL...")
        
        # Dividir o script em comandos individuais
        sql_commands = sql_script.split(';')
        
        for command in sql_commands:
            command = command.strip()
            if command:
                cursor.execute(command)
                conn.commit()
        
        print("[DEBUG] Script SQL executado com sucesso!")
        
        # Verificar se a tabela foi criada
        cursor.execute("SHOW TABLES LIKE 'screen_documentation'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            print("[DEBUG] Tabela screen_documentation criada com sucesso!")
            
            # Contar registros na tabela
            cursor.execute("SELECT COUNT(*) as count FROM screen_documentation")
            count = cursor.fetchone()['count']
            print(f"[DEBUG] Número de registros na tabela: {count}")
        else:
            print("[DEBUG] Erro: A tabela screen_documentation não foi criada!")
        
        print("\n[DEBUG] Processo concluído!")
        
        return True
        
    except mysql.connector.Error as e:
        print(f"[DEBUG] Erro ao conectar ao banco de dados: {e}")
        return False
    except Exception as e:
        print(f"[DEBUG] Erro inesperado: {e}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("\n[DEBUG] Conexão fechada.")

if __name__ == "__main__":
    create_screens_table()
