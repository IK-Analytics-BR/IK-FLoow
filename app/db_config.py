"""
Módulo centralizado para conexões de banco de dados
DETECÇÃO AUTOMÁTICA DE AMBIENTE (LOCAL vs PRODUÇÃO)
"""
import mysql.connector
from mysql.connector import Error

# Importar configuração automática
from auto_config import config

def get_db_connection():
    """
    Retorna uma conexão com o banco de dados MySQL
    DETECTA AUTOMATICAMENTE se é LOCAL ou PRODUÇÃO
    
    Uso:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM produtos")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
    """
    try:
        connection = mysql.connector.connect(**config.DB_CONFIG)
        return connection
    except Error as e:
        print(f"[DB_CONFIG] Erro ao conectar ao MySQL: {e}")
        print(f"[DB_CONFIG] Host tentado: {config.DB_CONFIG['host']}")
        raise

def get_db_config():
    """
    Retorna um dicionário com as configurações do banco de dados
    
    Uso:
        db_config = get_db_config()
        conn = mysql.connector.connect(**db_config)
    """
    return config.DB_CONFIG

# Para compatibilidade com código antigo
def get_direct_db():
    """Alias para get_db_connection() - para compatibilidade"""
    return get_db_connection()
