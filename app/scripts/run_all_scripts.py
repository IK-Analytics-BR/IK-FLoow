"""
Script para executar automaticamente todos os scripts SQL
"""

import os
import mysql.connector
from dotenv import load_dotenv
import sys

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco de dados
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'supply_chain')

# Lista de scripts SQL a serem executados
SQL_SCRIPTS = [
    'create_financial_tables.sql',
    'create_purchase_tables.sql',
    'create_invoice_tables.sql',
    'create_inventory_tables.sql',
    'create_users_tables.sql'
]

def execute_sql_script(cursor, script_path):
    """Executa um script SQL"""
    try:
        print(f"Executando script: {script_path}")
        
        # Ler o conteúdo do script
        with open(script_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        # Dividir o script em comandos individuais
        # Considerando que os comandos são separados por ponto e vírgula
        # e tratando corretamente os delimitadores para procedures e triggers
        commands = []
        delimiter = ';'
        current_command = ''
        
        for line in sql_content.splitlines():
            line = line.strip()
            
            # Ignorar comentários e linhas vazias
            if not line or line.startswith('--'):
                continue
            
            # Verificar se há mudança de delimitador
            if line.upper().startswith('DELIMITER'):
                if current_command:
                    commands.append(current_command)
                    current_command = ''
                
                # Extrair o novo delimitador
                delimiter = line.split()[1]
                continue
            
            # Adicionar a linha ao comando atual
            current_command += line + '\n'
            
            # Verificar se o comando está completo
            if line.endswith(delimiter):
                # Remover o delimitador do final do comando
                if delimiter != ';':
                    current_command = current_command.rsplit(delimiter, 1)[0]
                else:
                    current_command = current_command.rstrip(';\n')
                
                commands.append(current_command)
                current_command = ''
        
        # Adicionar o último comando se houver
        if current_command:
            commands.append(current_command)
        
        # Executar cada comando
        for i, command in enumerate(commands):
            if command.strip():
                try:
                    cursor.execute(command)
                    print(f"  Comando {i+1}/{len(commands)} executado com sucesso.")
                except Exception as e:
                    print(f"  Erro ao executar o comando {i+1}/{len(commands)}: {e}")
        
        print(f"Script {script_path} executado com sucesso!")
        return True
    
    except Exception as e:
        print(f"Erro ao executar o script {script_path}: {e}")
        return False

def main():
    """Função principal"""
    # Verificar se o banco de dados existe, se não, criar
    try:
        # Conectar ao servidor MySQL sem especificar o banco de dados
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        
        # Criar o banco de dados se não existir
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        print(f"Banco de dados '{DB_NAME}' verificado/criado com sucesso!")
        
        # Fechar a conexão
        cursor.close()
        conn.close()
        
        # Reconectar especificando o banco de dados
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        
        # Obter o diretório atual do script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Executar cada script SQL
        success_count = 0
        for script in SQL_SCRIPTS:
            script_path = os.path.join(script_dir, script)
            if os.path.exists(script_path):
                if execute_sql_script(cursor, script_path):
                    success_count += 1
            else:
                print(f"Arquivo não encontrado: {script_path}")
        
        # Commit das alterações
        conn.commit()
        
        # Fechar a conexão
        cursor.close()
        conn.close()
        
        print(f"\nResumo da execução:")
        print(f"Total de scripts: {len(SQL_SCRIPTS)}")
        print(f"Scripts executados com sucesso: {success_count}")
        print(f"Scripts com falha: {len(SQL_SCRIPTS) - success_count}")
        
        if success_count == len(SQL_SCRIPTS):
            print("\nTodos os scripts foram executados com sucesso!")
            return 0
        else:
            print("\nAlguns scripts falharam. Verifique os logs acima.")
            return 1
    
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
