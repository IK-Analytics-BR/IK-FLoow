"""
Script para executar os scripts SQL dos novos módulos.
Este script executa os comandos SQL diretamente, sem depender de bibliotecas externas.
"""

import os
import subprocess

def main():
    """Função principal."""
    # Caminho dos scripts SQL
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Lista de scripts para executar
    scripts = [
        'create_financial_tables.sql',
        'create_purchase_tables.sql'
    ]
    
    # Configurações do banco de dados
    db_name = 'supply_chain'
    db_user = 'root'
    db_password = 'root'
    
    # Executar cada script
    for script_name in scripts:
        script_path = os.path.join(script_dir, script_name)
        if os.path.exists(script_path):
            print(f"Executando script: {script_name}")
            
            # Comando para executar o script SQL
            command = f'mysql -u {db_user} -p{db_password} {db_name} < {script_path}'
            
            try:
                # Executar o comando
                subprocess.run(command, shell=True, check=True)
                print(f"Script {script_name} executado com sucesso!")
            except subprocess.CalledProcessError as e:
                print(f"Erro ao executar o script {script_name}: {e}")
        else:
            print(f"Script não encontrado: {script_path}")

if __name__ == "__main__":
    main()
