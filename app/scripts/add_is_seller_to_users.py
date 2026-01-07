import os
import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv

# Try to load .env in app/ first, else root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
APP_ENV = os.path.join(BASE_DIR, '.env')
if os.path.exists(APP_ENV):
    load_dotenv(APP_ENV)
else:
    load_dotenv()


def get_connection():
    cfg = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'aritana'),
        'database': os.getenv('DB_NAME', 'supply_chain_system'),
        'autocommit': True,
    }
    return mysql.connector.connect(**cfg)


def main():
    print('== MIGRAÇÃO: Adicionar coluna users.is_seller (BOOLEAN) ==')
    try:
        cnx = get_connection()
        cur = cnx.cursor()

        # Detect if column exists
        cur.execute(
            """
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'users'
              AND COLUMN_NAME = 'is_seller'
            """
        )
        (exists_count,) = cur.fetchone()
        if exists_count == 0:
            print('[DB] Adicionando coluna is_seller em users...')
            cur.execute("ALTER TABLE users ADD COLUMN is_seller TINYINT(1) NOT NULL DEFAULT 0 AFTER status")
            cur.execute("ALTER TABLE users ADD INDEX idx_users_is_seller (is_seller)")
        else:
            print('[DB] Coluna is_seller já existe em users')

        print('Migração concluída com sucesso.')
        cur.close()
        cnx.close()
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print('Erro de acesso: verifique usuário/senha do banco.')
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print('Erro: Banco de dados não existe.')
        else:
            print(f'Erro de banco: {err}')
    except Exception as e:
        print(f'Erro inesperado: {e}')


if __name__ == '__main__':
    main()
