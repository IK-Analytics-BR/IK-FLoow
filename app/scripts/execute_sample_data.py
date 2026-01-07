"""
Script para executar os scripts SQL de dados de exemplo.
"""

import mysql.connector
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco de dados
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'supply_chain'
}

def execute_sql_file(file_path):
    """Executa um arquivo SQL."""
    print(f"Executando arquivo SQL: {file_path}")
    
    try:
        # Conectar ao banco de dados
        print("Conectando ao banco de dados MySQL...")
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        print("Conexão estabelecida com sucesso!")
        
        # Ler o arquivo SQL
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_file = f.read()
        
        # Dividir o arquivo em comandos SQL individuais
        # Ignorar comentários e linhas vazias
        sql_commands = []
        lines = sql_file.split('\n')
        current_command = ''
        
        for line in lines:
            line = line.strip()
            
            # Ignorar comentários e linhas vazias
            if line.startswith('--') or line == '':
                continue
            
            # Adicionar a linha ao comando atual
            current_command += line + ' '
            
            # Se a linha terminar com ponto e vírgula, é o fim do comando
            if line.endswith(';'):
                sql_commands.append(current_command)
                current_command = ''
        
        # Executar cada comando SQL
        for i, command in enumerate(sql_commands):
            if command.strip():
                print(f"Executando comando SQL #{i+1}...")
                try:
                    cursor.execute(command)
                    
                    # Se o comando for um SELECT, buscar os resultados
                    if command.lower().strip().startswith('select'):
                        results = cursor.fetchall()
                        if results:
                            print(f"Resultados: {len(results)} registros")
                    
                    # Commit após cada comando
                    conn.commit()
                except Exception as e:
                    print(f"Erro ao executar o comando SQL #{i+1}: {str(e)}")
                    print(f"Comando: {command}")
        
        print(f"Execução concluída! {len(sql_commands)} comandos executados.")
        
    except Exception as e:
        print(f"Erro ao executar o script SQL: {str(e)}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Conexão fechada.")

def main():
    """Função principal."""
    # Caminho dos scripts SQL
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Executar os scripts SQL
    scripts = [
        'insert_sample_sellers.sql',
        'insert_sample_routes.sql',
        'insert_sample_manifests.sql'
    ]
    
    for script in scripts:
        script_path = os.path.join(script_dir, script)
        if os.path.exists(script_path):
            print(f"\n{'='*50}")
            print(f"Executando script: {script}")
            print(f"{'='*50}")
            execute_sql_file(script_path)
        else:
            print(f"Script não encontrado: {script_path}")

if __name__ == "__main__":
    main()
