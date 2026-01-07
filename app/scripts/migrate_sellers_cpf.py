import os
import re
import datetime
import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv

# Load .env from app/ if present, else root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
APP_ENV = os.path.join(BASE_DIR, '.env')
if os.path.exists(APP_ENV):
    load_dotenv(APP_ENV)
else:
    load_dotenv()


def cpf_digits_only(cpf: str) -> str:
    return re.sub(r'[^0-9]', '', cpf or '')


def format_cpf(digits: str) -> str:
    d = cpf_digits_only(digits)
    if len(d) != 11:
        return ''
    return f"{d[0:3]}.{d[3:6]}.{d[6:9]}-{d[9:11]}"


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
    print("== MIGRAÇÃO: Formatar CPFs de sellers para 000.000.000-00 ==")
    try:
        cnx = get_connection()
        cur = cnx.cursor(dictionary=True)

        # Cria pasta de logs
        logs_dir = os.path.join(BASE_DIR, 'migration_logs')
        os.makedirs(logs_dir, exist_ok=True)
        log_path = os.path.join(
            logs_dir,
            f"migrate_sellers_cpf_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        )

        with open(log_path, 'w', encoding='utf-8') as log:
            def logline(msg: str):
                print(msg)
                log.write(msg + "\n")

            logline("Iniciando migração de CPFs em sellers...")

            # Buscar sellers com CPF preenchido
            cur.execute("""
                SELECT id, cpf FROM sellers
                WHERE cpf IS NOT NULL AND TRIM(cpf) <> '' AND active = TRUE
            """)
            rows = cur.fetchall()

            total = len(rows)
            updated = 0
            already_formatted = 0
            invalid = 0
            conflicts = []

            logline(f"Total de registros analisados: {total}")

            for row in rows:
                sid = row['id']
                cpf_raw = row['cpf']
                digits = cpf_digits_only(cpf_raw)

                if len(digits) != 11:
                    invalid += 1
                    logline(f"[INVALIDO] id={sid} cpf='{cpf_raw}' -> não possui 11 dígitos úteis")
                    continue

                cpf_fmt = format_cpf(digits)
                if cpf_fmt == (cpf_raw or '').strip():
                    already_formatted += 1
                    continue

                # Verificar conflito: outro registro com mesmos dígitos
                cur.execute(
                    """
                    SELECT id FROM sellers
                    WHERE REPLACE(REPLACE(REPLACE(cpf, '.', ''), '-', ''), ' ', '') = %s
                      AND id <> %s AND active = TRUE
                    LIMIT 1
                    """,
                    (digits, sid),
                )
                other = cur.fetchone()
                if other:
                    conflicts.append((sid, cpf_raw, other['id']))
                    logline(f"[CONFLITO] id_atual={sid} cpf='{cpf_raw}' conflita com id={other['id']} (mesmos dígitos)")
                    continue

                # Tentar atualizar
                try:
                    cur.execute(
                        """
                        UPDATE sellers
                        SET cpf = %s
                        WHERE id = %s
                        """,
                        (cpf_fmt, sid),
                    )
                    updated += 1
                except Exception as e:
                    logline(f"[ERRO] id={sid} cpf='{cpf_raw}' ao atualizar: {e}")

            logline("")
            logline("Resumo:")
            logline(f" - Atualizados: {updated}")
            logline(f" - Já formatados: {already_formatted}")
            logline(f" - Inválidos (não 11 dígitos): {invalid}")
            logline(f" - Conflitos: {len(conflicts)}")
            if conflicts:
                logline("Detalhes de conflitos (id_atual, cpf_atual, id_conflitante):")
                for c in conflicts:
                    logline(f"   {c[0]}, {c[1]}, {c[2]}")

        cur.close()
        cnx.close()
        print(f"Migração concluída. Veja o relatório em: {log_path}")

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Erro de acesso: verifique usuário/senha do banco.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Erro: Banco de dados não existe.")
        else:
            print(f"Erro de banco: {err}")
    except Exception as e:
        print(f"Erro inesperado: {e}")


if __name__ == '__main__':
    main()
