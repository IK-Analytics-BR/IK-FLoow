"""
Script para executar arquivos SQL usando mysql-connector-python.
"""

import mysql.connector
import os

# Configurações do banco de dados
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'supply_chain'
}

def execute_sql_file(file_path, connection):
    """Executa um arquivo SQL."""
    print(f"Executando arquivo SQL: {file_path}")
    
    try:
        cursor = connection.cursor()
        
        # Ler o arquivo SQL
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Dividir o conteúdo em comandos SQL individuais
        # Precisamos lidar com delimitadores personalizados para procedures e triggers
        delimiter = ';'
        commands = []
        current_command = ''
        
        for line in sql_content.splitlines():
            # Ignorar comentários e linhas vazias
            if line.strip().startswith('--') or not line.strip():
                continue
            
            # Verificar se há uma alteração de delimitador
            if line.strip().upper().startswith('DELIMITER'):
                if current_command:
                    commands.append(current_command)
                    current_command = ''
                
                # Extrair o novo delimitador
                delimiter = line.strip().split()[1]
                continue
            
            # Adicionar a linha ao comando atual
            current_command += line + '\n'
            
            # Se a linha terminar com o delimitador atual, é o fim do comando
            if line.strip().endswith(delimiter):
                # Remover o delimitador do final do comando
                if delimiter != ';':
                    current_command = current_command.rsplit(delimiter, 1)[0] + ';'
                
                commands.append(current_command)
                current_command = ''
        
        # Adicionar o último comando se houver
        if current_command.strip():
            commands.append(current_command)
        
        # Executar cada comando SQL
        for i, command in enumerate(commands):
            if command.strip():
                try:
                    print(f"Executando comando {i+1}/{len(commands)}...")
                    cursor.execute(command)
                    connection.commit()
                except Exception as e:
                    print(f"Erro ao executar o comando {i+1}: {str(e)}")
                    print(f"Comando: {command[:100]}...")  # Mostrar apenas os primeiros 100 caracteres
        
        cursor.close()
        print(f"Arquivo SQL executado com sucesso!")
        
    except Exception as e:
        print(f"Erro ao executar o arquivo SQL: {str(e)}")

def main():
    """Função principal."""
    # Caminho dos scripts SQL
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Lista de scripts para executar
    scripts = [
        'create_financial_tables.sql',
        'create_purchase_tables.sql'
    ]
    
    try:
        # Conectar ao banco de dados
        print("Conectando ao banco de dados MySQL...")
        connection = mysql.connector.connect(**DB_CONFIG)
        
        if connection.is_connected():
            print("Conexão estabelecida com sucesso!")
            
            # Executar cada script
            for script_name in scripts:
                script_path = os.path.join(script_dir, script_name)
                if os.path.exists(script_path):
                    execute_sql_file(script_path, connection)
                else:
                    print(f"Script não encontrado: {script_path}")
            
            connection.close()
            print("Conexão fechada.")
        
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {str(e)}")

if __name__ == "__main__":
    main()
