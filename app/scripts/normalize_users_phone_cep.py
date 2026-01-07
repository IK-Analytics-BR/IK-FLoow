import os
import re
import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv

# Load environment (.env in app/ preferred)
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


def digits_only(s: str) -> str:
    return re.sub(r'[^0-9]', '', s or '')


def format_phone(phone: str) -> str | None:
    d = digits_only(phone)
    if not d:
        return None
    if len(d) == 11:
        return f"({d[0:2]}) {d[2:7]}-{d[7:11]}"
    if len(d) == 10:
        return f"({d[0:2]}) {d[2:6]}-{d[6:10]}"
    # Tamanhos diferentes mantêm original (ou None se vazio)
    return phone or None


def format_cep(cep: str) -> str | None:
    d = digits_only(cep)
    if not d:
        return None
    if len(d) == 8:
        return f"{d[0:5]}-{d[5:8]}"
    return cep or None


def main():
    print('== Normalização de CEP e Telefone na tabela users ==')
    updated = 0
    examined = 0
    try:
        cnx = get_connection()
        cur = cnx.cursor(dictionary=True)

        # Selecionar colunas necessárias
        cur.execute("""
            SELECT id, phone, cep
            FROM users
        """)
        rows = cur.fetchall()

        for row in rows:
            examined += 1
            uid = row['id']
            phone = row.get('phone')
            cep = row.get('cep')

            new_phone = format_phone(phone) if phone is not None else None
            new_cep = format_cep(cep) if cep is not None else None

            # Decidir se precisa atualizar
            do_update = False
            params = []
            set_clauses = []

            # Só atualiza se houver diferença de valor (evita writes desnecessários)
            if (new_phone or None) != (phone or None):
                set_clauses.append("phone = %s")
                params.append(new_phone)
                do_update = True
            if (new_cep or None) != (cep or None):
                set_clauses.append("cep = %s")
                params.append(new_cep)
                do_update = True

            if do_update:
                params.append(uid)
                sql = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = %s"
                cur.execute(sql, params)
                updated += cur.rowcount

        cnx.commit()
        print(f"Registros verificados: {examined}")
        print(f"Registros atualizados: {updated}")
        cur.close()
        cnx.close()
        print('Normalização concluída.')
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
