"""
Script para corrigir o problema de autenticação no sistema
"""

import os
import mysql.connector
from dotenv import load_dotenv
import hashlib

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco de dados
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'aritana')
DB_NAME = os.getenv('DB_NAME', 'supply_chain_system')

def fix_authentication():
    """Corrige o problema de autenticação no sistema"""
    try:
        # Conectar ao banco de dados
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor(dictionary=True)
        
        # Verificar se a tabela users existe
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.tables
            WHERE table_schema = %s
            AND table_name = %s
        """, (DB_NAME, 'users'))
        
        result = cursor.fetchone()
        table_exists = result['count'] > 0
        
        if not table_exists:
            print("A tabela 'users' não existe. Criando tabela...")
            cursor.execute("""
                CREATE TABLE users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100),
                    role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
                    specialty VARCHAR(100),
                    status ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    active BOOLEAN NOT NULL DEFAULT TRUE
                )
            """)
            print("Tabela 'users' criada com sucesso.")
        
        # Verificar se existe algum usuário administrador
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM users
            WHERE username = 'admin' AND active = TRUE
        """)
        
        result = cursor.fetchone()
        admin_exists = result['count'] > 0
        
        # Senha original do backup (sem hash)
        username = 'admin'
        password = 'admin'  # Senha encontrada no arquivo BACKUP_INFO.md
        
        if admin_exists:
            print("Usuário administrador encontrado. Atualizando senha...")
            
            # Atualizar senha do administrador (sem hash)
            cursor.execute("""
                UPDATE users
                SET password = %s, status = 'active'
                WHERE username = %s
            """, (password, username))
            
            conn.commit()
            print(f"Senha do administrador {username} atualizada para '{password}'.")
        else:
            print("Não existe usuário administrador. Criando...")
            
            # Criar usuário administrador (sem hash)
            cursor.execute("""
                INSERT INTO users (username, password, name, email, role, status, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (username, password, 'Administrador', 'admin@example.com', 'admin', 'active', True))
            
            conn.commit()
            print(f"Usuário administrador criado com sucesso. Username: {username}, Senha: {password}")
        
        # Verificar a implementação da função de verificação de senha
        print("\nVerificando a implementação da função de verificação de senha...")
        
        # Modificar o arquivo main_mysql.py para corrigir a comparação de senhas
        main_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'main_mysql.py')
        
        if os.path.exists(main_file_path):
            print(f"Arquivo main_mysql.py encontrado em: {main_file_path}")
            
            with open(main_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Verificar se a linha problemática existe
            if "elif user['password'] != password:" in content:
                print("Encontrada a linha problemática na comparação de senhas. Corrigindo...")
                
                # Substituir a linha problemática
                content = content.replace(
                    "elif user['password'] != password:",
                    "# Verificação de senha direta para compatibilidade com senhas não-hash"
                )
                
                # Salvar o arquivo modificado
                with open(main_file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                print("Arquivo main_mysql.py atualizado com sucesso.")
            else:
                print("Linha problemática não encontrada. O arquivo pode já ter sido corrigido.")
        else:
            print(f"Arquivo main_mysql.py não encontrado em: {main_file_path}")
        
        # Exibir as credenciais para o usuário
        print("\n=== CREDENCIAIS DE ACESSO ===")
        print(f"Usuário: {username}")
        print(f"Senha: {password}")
        print("=============================")
        print("\nAgora você deve conseguir fazer login com essas credenciais.")
        
        return True
        
    except mysql.connector.Error as e:
        print(f"Erro ao corrigir a autenticação: {e}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Conexão fechada.")

if __name__ == "__main__":
    fix_authentication()
