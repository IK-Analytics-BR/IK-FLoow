import os
import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv

# Load environment
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


def column_exists(cur, table, column):
    cur.execute(
        """
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
        """,
        (table, column),
    )
    return cur.fetchone()[0] > 0


def index_exists(cur, table, index_name):
    cur.execute(
        """
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND INDEX_NAME = %s
        """,
        (table, index_name),
    )
    return cur.fetchone()[0] > 0


def main():
    print('== MIGRAÇÃO: Estender tabela users com campos completos ==')
    cols = [
        ("cpf", "VARCHAR(20) NULL AFTER email"),
        ("phone", "VARCHAR(30) NULL AFTER cpf"),
        ("commission", "DECIMAL(5,2) NULL DEFAULT 0 AFTER phone"),
        ("employment_type", "VARCHAR(30) NULL AFTER commission"),
        ("cep", "VARCHAR(15) NULL AFTER employment_type"),
        ("address", "VARCHAR(120) NULL AFTER cep"),
        ("number", "VARCHAR(20) NULL AFTER address"),
        ("complement", "VARCHAR(60) NULL AFTER number"),
        ("neighborhood", "VARCHAR(60) NULL AFTER complement"),
        ("city", "VARCHAR(60) NULL AFTER neighborhood"),
        ("state", "VARCHAR(2) NULL AFTER city"),
        ("reference", "VARCHAR(120) NULL AFTER state"),
        ("notes", "TEXT NULL AFTER reference"),
    ]

    try:
        cnx = get_connection()
        cur = cnx.cursor()

        for col, ddl in cols:
            if not column_exists(cur, 'users', col):
                print(f"[DB] Adicionando coluna users.{col} ...")
                cur.execute(f"ALTER TABLE users ADD COLUMN {col} {ddl}")
            else:
                print(f"[DB] Coluna users.{col} já existe")

        # Índice único para CPF (opcional, permite NULLs)
        if not index_exists(cur, 'users', 'idx_users_cpf_unique'):
            try:
                print("[DB] Criando índice único em users.cpf ...")
                cur.execute("ALTER TABLE users ADD UNIQUE INDEX idx_users_cpf_unique (cpf)")
            except Exception as e:
                print(f"[WARN] Não foi possível criar UNIQUE idx_users_cpf_unique(cpf): {e}")
        else:
            print("[DB] Índice único idx_users_cpf_unique já existe")

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
