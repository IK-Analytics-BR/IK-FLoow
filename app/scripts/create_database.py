"""
Script para verificar e criar o banco de dados supply_chain_system
"""

import os
import mysql.connector
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco de dados
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'aritana')
DB_NAME = 'supply_chain_system'

def create_database():
    """Verifica e cria o banco de dados supply_chain_system"""
    try:
        # Conectar ao MySQL sem especificar um banco de dados
        print("\n[DEBUG] Conectando ao MySQL...")
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor(dictionary=True)
        print("[DEBUG] Conexão estabelecida com sucesso!")
        
        # Verificar se o banco de dados supply_chain_system existe
        print("\n[DEBUG] Verificando se o banco de dados supply_chain_system existe...")
        cursor.execute("SHOW DATABASES LIKE %s", (DB_NAME,))
        database_exists = cursor.fetchone() is not None
        
        if database_exists:
            print(f"[DEBUG] O banco de dados {DB_NAME} já existe.")
        else:
            print(f"[DEBUG] O banco de dados {DB_NAME} não existe. Criando...")
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            print(f"[DEBUG] Banco de dados {DB_NAME} criado com sucesso!")
        
        # Usar o banco de dados supply_chain_system
        print(f"\n[DEBUG] Usando o banco de dados {DB_NAME}...")
        cursor.execute(f"USE {DB_NAME}")
        
        # Verificar as tabelas existentes
        print("\n[DEBUG] Verificando as tabelas existentes...")
        cursor.execute("SHOW TABLES")
        tables = [table[f'Tables_in_{DB_NAME}'] for table in cursor.fetchall()]
        print(f"[DEBUG] Tabelas existentes: {tables}")
        
        # Fechar a conexão
        cursor.close()
        conn.close()
        print("\n[DEBUG] Conexão fechada.")
        
        print("\n[DEBUG] Agora você pode executar o script verify_all_database_tables.py para criar as tabelas necessárias.")
        print("[DEBUG] Em seguida, reinicie a aplicação para aplicar as alterações.")
        
        return True
        
    except mysql.connector.Error as e:
        print(f"[DEBUG] Erro ao conectar ao MySQL: {e}")
        return False

if __name__ == "__main__":
    create_database()
