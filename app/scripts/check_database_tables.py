"""
Script para verificar as tabelas do banco de dados e corrigir problemas
"""

import os
import mysql.connector
from dotenv import load_dotenv
import sys

# Adicionar o diretório pai ao caminho de importação
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco de dados
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'aritana')
DB_NAME = os.getenv('DB_NAME', 'supply_chain_system')

def check_database_tables():
    """Verifica as tabelas do banco de dados e corrige problemas"""
    try:
        # Conectar ao banco de dados
        print("\n[DEBUG] Conectando ao banco de dados...")
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor(dictionary=True)
        print("[DEBUG] Conexão estabelecida com sucesso!")
        
        # Verificar a tabela users
        print("\n[DEBUG] Verificando a tabela users...")
        cursor.execute("SHOW TABLES LIKE 'users'")
        users_exists = cursor.fetchone() is not None
        
        if users_exists:
            print("[DEBUG] A tabela users existe.")
            cursor.execute("SELECT COUNT(*) as count FROM users")
            users_count = cursor.fetchone()['count']
            print(f"[DEBUG] Número de usuários: {users_count}")
            
            # Verificar o usuário admin
            cursor.execute("SELECT * FROM users WHERE username = 'admin'")
            admin = cursor.fetchone()
            if admin:
                print(f"[DEBUG] Usuário admin encontrado: ID={admin['id']}, Senha={admin['password']}")
            else:
                print("[DEBUG] Usuário admin não encontrado!")
        else:
            print("[DEBUG] A tabela users não existe!")
        
        # Verificar a tabela products
        print("\n[DEBUG] Verificando a tabela products...")
        cursor.execute("SHOW TABLES LIKE 'products'")
        products_exists = cursor.fetchone() is not None
        
        if products_exists:
            print("[DEBUG] A tabela products existe.")
            cursor.execute("SELECT COUNT(*) as count FROM products")
            products_count = cursor.fetchone()['count']
            print(f"[DEBUG] Número de produtos: {products_count}")
        else:
            print("[DEBUG] A tabela products não existe! Criando tabela...")
            cursor.execute("""
                CREATE TABLE products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
                    stock INT NOT NULL DEFAULT 0,
                    min_stock INT NOT NULL DEFAULT 5,
                    category VARCHAR(50),
                    supplier_id INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    active BOOLEAN NOT NULL DEFAULT TRUE,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
                )
            """)
            print("[DEBUG] Tabela products criada com sucesso!")
            
            # Inserir alguns produtos de exemplo
            print("[DEBUG] Inserindo produtos de exemplo...")
            cursor.execute("""
                INSERT INTO products (name, description, price, stock, min_stock, category, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, ('Produto Exemplo 1', 'Descrição do produto 1', 99.99, 10, 5, 'Categoria 1', True))
            
            cursor.execute("""
                INSERT INTO products (name, description, price, stock, min_stock, category, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, ('Produto Exemplo 2', 'Descrição do produto 2', 149.99, 20, 8, 'Categoria 2', True))
            
            conn.commit()
            print("[DEBUG] Produtos de exemplo inseridos com sucesso!")
        
        # Verificar a tabela supplies
        print("\n[DEBUG] Verificando a tabela supplies...")
        cursor.execute("SHOW TABLES LIKE 'supplies'")
        supplies_exists = cursor.fetchone() is not None
        
        if supplies_exists:
            print("[DEBUG] A tabela supplies existe.")
            cursor.execute("SELECT COUNT(*) as count FROM supplies")
            supplies_count = cursor.fetchone()['count']
            print(f"[DEBUG] Número de insumos: {supplies_count}")
        else:
            print("[DEBUG] A tabela supplies não existe! Criando tabela...")
            cursor.execute("""
                CREATE TABLE supplies (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    supplier_id INT,
                    part_number VARCHAR(50),
                    stock INT DEFAULT 0,
                    min_stock INT DEFAULT 5,
                    unit_cost DECIMAL(10, 2),
                    location VARCHAR(100),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    active BOOLEAN NOT NULL DEFAULT TRUE,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
                )
            """)
            print("[DEBUG] Tabela supplies criada com sucesso!")
            
            # Inserir alguns insumos de exemplo
            print("[DEBUG] Inserindo insumos de exemplo...")
            cursor.execute("""
                INSERT INTO supplies (name, description, part_number, stock, min_stock, unit_cost, location, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, ('Insumo Exemplo 1', 'Descrição do insumo 1', 'INS-001', 15, 5, 29.99, 'Almoxarifado A', True))
            
            cursor.execute("""
                INSERT INTO supplies (name, description, part_number, stock, min_stock, unit_cost, location, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, ('Insumo Exemplo 2', 'Descrição do insumo 2', 'INS-002', 25, 10, 39.99, 'Almoxarifado B', True))
            
            conn.commit()
            print("[DEBUG] Insumos de exemplo inseridos com sucesso!")
        
        # Verificar a tabela customers
        print("\n[DEBUG] Verificando a tabela customers...")
        cursor.execute("SHOW TABLES LIKE 'customers'")
        customers_exists = cursor.fetchone() is not None
        
        if customers_exists:
            print("[DEBUG] A tabela customers existe.")
            cursor.execute("SELECT COUNT(*) as count FROM customers")
            customers_count = cursor.fetchone()['count']
            print(f"[DEBUG] Número de clientes: {customers_count}")
        else:
            print("[DEBUG] A tabela customers não existe!")
        
        # Verificar a tabela suppliers
        print("\n[DEBUG] Verificando a tabela suppliers...")
        cursor.execute("SHOW TABLES LIKE 'suppliers'")
        suppliers_exists = cursor.fetchone() is not None
        
        if suppliers_exists:
            print("[DEBUG] A tabela suppliers existe.")
            cursor.execute("SELECT COUNT(*) as count FROM suppliers")
            suppliers_count = cursor.fetchone()['count']
            print(f"[DEBUG] Número de fornecedores: {suppliers_count}")
        else:
            print("[DEBUG] A tabela suppliers não existe! Criando tabela...")
            cursor.execute("""
                CREATE TABLE suppliers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    cnpj VARCHAR(18),
                    contact_name VARCHAR(100),
                    phone VARCHAR(20),
                    email VARCHAR(100),
                    address VARCHAR(255),
                    city VARCHAR(100),
                    state VARCHAR(50),
                    zip_code VARCHAR(10),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    active BOOLEAN NOT NULL DEFAULT TRUE
                )
            """)
            print("[DEBUG] Tabela suppliers criada com sucesso!")
            
            # Inserir alguns fornecedores de exemplo
            print("[DEBUG] Inserindo fornecedores de exemplo...")
            cursor.execute("""
                INSERT INTO suppliers (name, cnpj, contact_name, phone, email, address, city, state, zip_code, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, ('Fornecedor Exemplo 1', '12.345.678/0001-90', 'Contato 1', '(11) 1234-5678', 'contato1@fornecedor.com', 'Rua Exemplo, 123', 'São Paulo', 'SP', '01234-567', True))
            
            conn.commit()
            print("[DEBUG] Fornecedores de exemplo inseridos com sucesso!")
        
        # Modificar o arquivo main_mysql.py para tratar valores nulos
        print("\n[DEBUG] Modificando o arquivo main_mysql.py para tratar valores nulos...")
        main_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'main_mysql.py')
        
        if os.path.exists(main_file_path):
            print(f"[DEBUG] Arquivo main_mysql.py encontrado: {main_file_path}")
            
            with open(main_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Verificar e corrigir o código do dashboard para tratar valores nulos
            if "customers_count = db.fetch_one(\"SELECT COUNT(*) as count FROM customers WHERE active = TRUE\")['count']" in content:
                print("[DEBUG] Encontrada a linha problemática no dashboard. Corrigindo...")
                
                # Substituir todas as linhas problemáticas
                content = content.replace(
                    "customers_count = db.fetch_one(\"SELECT COUNT(*) as count FROM customers WHERE active = TRUE\")['count']",
                    "result = db.fetch_one(\"SELECT COUNT(*) as count FROM customers WHERE active = TRUE\")\n    customers_count = result['count'] if result else 0"
                )
                
                content = content.replace(
                    "products_count = db.fetch_one(\"SELECT COUNT(*) as count FROM products WHERE active = TRUE\")['count']",
                    "result = db.fetch_one(\"SELECT COUNT(*) as count FROM products WHERE active = TRUE\")\n    products_count = result['count'] if result else 0"
                )
                
                content = content.replace(
                    "supplies_count = db.fetch_one(\"SELECT COUNT(*) as count FROM supplies WHERE active = TRUE\")['count']",
                    "result = db.fetch_one(\"SELECT COUNT(*) as count FROM supplies WHERE active = TRUE\")\n    supplies_count = result['count'] if result else 0"
                )
                
                content = content.replace(
                    "suppliers_count = db.fetch_one(\"SELECT COUNT(*) as count FROM suppliers WHERE active = TRUE\")['count']",
                    "result = db.fetch_one(\"SELECT COUNT(*) as count FROM suppliers WHERE active = TRUE\")\n    suppliers_count = result['count'] if result else 0"
                )
                
                with open(main_file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                print("[DEBUG] Arquivo main_mysql.py atualizado com sucesso!")
            else:
                print("[DEBUG] As linhas problemáticas não foram encontradas ou já foram corrigidas.")
        else:
            print(f"[DEBUG] Arquivo main_mysql.py não encontrado: {main_file_path}")
        
        print("\n[DEBUG] Verificação e correção das tabelas concluídas com sucesso!")
        print("[DEBUG] Por favor, reinicie a aplicação para aplicar as alterações.")
        
        return True
        
    except mysql.connector.Error as e:
        print(f"[DEBUG] Erro ao conectar ao banco de dados: {e}")
        return False
    except Exception as e:
        print(f"[DEBUG] Erro inesperado: {e}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("\n[DEBUG] Conexão fechada.")

if __name__ == "__main__":
    check_database_tables()
