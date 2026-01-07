"""
Script para verificar a tabela de usuários e criar um usuário administrador
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

def hash_password(password):
    """Cria um hash da senha usando SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_users_table():
    """Verifica a tabela de usuários e cria um usuário administrador"""
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
            WHERE role = 'admin' AND active = TRUE
        """)
        
        result = cursor.fetchone()
        admin_exists = result['count'] > 0
        
        if admin_exists:
            print("Já existe um usuário administrador.")
            cursor.execute("""
                SELECT id, username, name, role, status
                FROM users
                WHERE role = 'admin' AND active = TRUE
            """)
            admins = cursor.fetchall()
            print("Administradores existentes:")
            for admin in admins:
                print(f"  ID: {admin['id']} - Username: {admin['username']} - Nome: {admin['name']} - Status: {admin['status']}")
            
            # Atualizar a senha do primeiro administrador
            admin_id = admins[0]['id']
            new_password = 'admin123'
            hashed_password = hash_password(new_password)
            
            cursor.execute("""
                UPDATE users
                SET password = %s, status = 'active'
                WHERE id = %s
            """, (hashed_password, admin_id))
            
            conn.commit()
            print(f"Senha do administrador {admins[0]['username']} atualizada para 'admin123'.")
        else:
            print("Não existe usuário administrador. Criando...")
            
            # Criar usuário administrador
            username = 'admin'
            password = 'admin123'
            hashed_password = hash_password(password)
            
            cursor.execute("""
                INSERT INTO users (username, password, name, email, role, status, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (username, hashed_password, 'Administrador', 'admin@example.com', 'admin', 'active', True))
            
            conn.commit()
            print(f"Usuário administrador criado com sucesso. Username: {username}, Senha: {password}")
        
        return True
        
    except mysql.connector.Error as e:
        print(f"Erro ao verificar a tabela de usuários: {e}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Conexão fechada.")

if __name__ == "__main__":
    check_users_table()
