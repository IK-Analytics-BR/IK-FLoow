"""
Script para verificar e corrigir todas as tabelas do projeto no MySQL
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

# Lista de tabelas essenciais que devem existir no banco de dados
ESSENTIAL_TABLES = [
    'users',
    'customers',
    'suppliers',
    'products',
    'supplies',
    'equipment',
    'maintenance_plans',
    'service_orders',
    'service_order_items',
    'service_order_labor',
    'alerts',
    'hour_meter_readings',
    'technicians',
    'bank_accounts',
    'accounts_payable',
    'accounts_receivable'
]

# Definições das tabelas (estrutura SQL para criação)
TABLE_DEFINITIONS = {
    'users': """
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
    """,
    'customers': """
        CREATE TABLE customers (
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
    """,
    'suppliers': """
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
    """,
    'products': """
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
    """,
    'supplies': """
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
    """,
    'equipment': """
        CREATE TABLE equipment (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            model VARCHAR(50),
            serial_number VARCHAR(50),
            customer_id INT NOT NULL,
            location VARCHAR(100),
            status ENUM('active', 'inactive', 'maintenance') NOT NULL DEFAULT 'active',
            purchase_date DATE,
            warranty_end_date DATE,
            last_maintenance_date DATE,
            next_maintenance_date DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            active BOOLEAN NOT NULL DEFAULT TRUE,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """,
    'maintenance_plans': """
        CREATE TABLE maintenance_plans (
            id INT AUTO_INCREMENT PRIMARY KEY,
            task VARCHAR(100) NOT NULL,
            description TEXT,
            customer_id INT NOT NULL,
            equipment_id INT NOT NULL,
            frequency_days INT NOT NULL,
            estimated_hours DECIMAL(5, 2),
            last_execution_date DATE,
            next_execution_date DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            active BOOLEAN NOT NULL DEFAULT TRUE,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (equipment_id) REFERENCES equipment(id)
        )
    """,
    'service_orders': """
        CREATE TABLE service_orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_number VARCHAR(20) NOT NULL,
            customer_id INT NOT NULL,
            equipment_id INT NOT NULL,
            supply_id INT,
            maintenance_plan_id INT,
            type ENUM('preventive', 'corrective', 'predictive') NOT NULL,
            technician_id INT,
            status ENUM('open', 'in_progress', 'completed', 'canceled') NOT NULL DEFAULT 'open',
            observations TEXT,
            downtime_minutes INT DEFAULT 0,
            open_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completion_date TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            active BOOLEAN NOT NULL DEFAULT TRUE,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (equipment_id) REFERENCES equipment(id),
            FOREIGN KEY (supply_id) REFERENCES supplies(id),
            FOREIGN KEY (maintenance_plan_id) REFERENCES maintenance_plans(id),
            FOREIGN KEY (technician_id) REFERENCES technicians(id),
            UNIQUE KEY (order_number)
        )
    """,
    'service_order_items': """
        CREATE TABLE service_order_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            service_order_id INT NOT NULL,
            supply_id INT NOT NULL,
            quantity INT NOT NULL,
            unit_cost DECIMAL(10, 2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (service_order_id) REFERENCES service_orders(id),
            FOREIGN KEY (supply_id) REFERENCES supplies(id)
        )
    """,
    'service_order_labor': """
        CREATE TABLE service_order_labor (
            id INT AUTO_INCREMENT PRIMARY KEY,
            service_order_id INT NOT NULL,
            technician_id INT NOT NULL,
            hours_worked DECIMAL(10, 2) NOT NULL,
            hourly_rate DECIMAL(10, 2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (service_order_id) REFERENCES service_orders(id),
            FOREIGN KEY (technician_id) REFERENCES technicians(id)
        )
    """,
    'alerts': """
        CREATE TABLE alerts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            equipment_id INT,
            supply_id INT,
            alert_type VARCHAR(50) NOT NULL,
            message TEXT NOT NULL,
            priority ENUM('low', 'medium', 'high') NOT NULL DEFAULT 'medium',
            status ENUM('active', 'acknowledged', 'resolved') NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE SET NULL,
            FOREIGN KEY (supply_id) REFERENCES supplies(id) ON DELETE SET NULL
        )
    """,
    'hour_meter_readings': """
        CREATE TABLE hour_meter_readings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            equipment_id INT NOT NULL,
            reading_date DATE NOT NULL,
            hours DECIMAL(10, 2) NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (equipment_id) REFERENCES equipment(id)
        )
    """,
    'technicians': """
        CREATE TABLE technicians (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            registration_number VARCHAR(50),
            specialty VARCHAR(100),
            status ENUM('active', 'inactive', 'on_leave') NOT NULL DEFAULT 'active',
            phone VARCHAR(20),
            email VARCHAR(100),
            cpf VARCHAR(14),
            address VARCHAR(255),
            city VARCHAR(100),
            state VARCHAR(50),
            zip_code VARCHAR(10),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            active BOOLEAN NOT NULL DEFAULT TRUE
        )
    """,
    'bank_accounts': """
        CREATE TABLE bank_accounts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            bank_name VARCHAR(100),
            agency VARCHAR(20),
            account_number VARCHAR(20),
            pix_key VARCHAR(100),
            cost_center VARCHAR(50),
            status ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            active BOOLEAN NOT NULL DEFAULT TRUE
        )
    """,
    'accounts_payable': """
        CREATE TABLE accounts_payable (
            id INT AUTO_INCREMENT PRIMARY KEY,
            supplier_id INT,
            description VARCHAR(255) NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            due_date DATE NOT NULL,
            payment_date DATE,
            payment_method ENUM('boleto', 'pix', 'transfer', 'credit_card', 'cash') NOT NULL,
            bank_account_id INT,
            status ENUM('pending', 'paid', 'overdue', 'canceled') NOT NULL DEFAULT 'pending',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL,
            FOREIGN KEY (bank_account_id) REFERENCES bank_accounts(id) ON DELETE SET NULL
        )
    """,
    'accounts_receivable': """
        CREATE TABLE accounts_receivable (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT,
            description VARCHAR(255) NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            due_date DATE NOT NULL,
            payment_date DATE,
            payment_method ENUM('boleto', 'pix', 'transfer', 'credit_card', 'cash') NOT NULL,
            bank_account_id INT,
            status ENUM('pending', 'received', 'overdue', 'canceled') NOT NULL DEFAULT 'pending',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
            FOREIGN KEY (bank_account_id) REFERENCES bank_accounts(id) ON DELETE SET NULL
        )
    """
}

# Dados de exemplo para inserir nas tabelas
SAMPLE_DATA = {
    'users': [
        ("INSERT INTO users (username, password, name, email, role, status, active) VALUES (%s, %s, %s, %s, %s, %s, %s)",
         ('admin', 'admin', 'Administrador', 'admin@example.com', 'admin', 'active', True))
    ],
    'customers': [
        ("INSERT INTO customers (name, cnpj, contact_name, phone, email, address, city, state, zip_code, notes, active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
         ('Cliente Exemplo 1', '12.345.678/0001-90', 'João Silva', '(11) 98765-4321', 'joao@cliente.com', 'Rua dos Clientes, 123', 'São Paulo', 'SP', '01234-567', 'Cliente corporativo', True)),
        ("INSERT INTO customers (name, cnpj, contact_name, phone, email, address, city, state, zip_code, notes, active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
         ('Cliente Exemplo 2', '98.765.432/0001-10', 'Maria Oliveira', '(11) 91234-5678', 'maria@cliente.com', 'Av. dos Clientes, 456', 'São Paulo', 'SP', '04321-765', 'Cliente VIP', True))
    ],
    'suppliers': [
        ("INSERT INTO suppliers (name, cnpj, contact_name, phone, email, address, city, state, zip_code, notes, active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
         ('Fornecedor Exemplo 1', '12.345.678/0001-90', 'Carlos Souza', '(11) 98765-4321', 'carlos@fornecedor.com', 'Rua dos Fornecedores, 123', 'São Paulo', 'SP', '01234-567', 'Fornecedor de peças', True))
    ],
    'products': [
        ("INSERT INTO products (name, description, price, stock, min_stock, category, active) VALUES (%s, %s, %s, %s, %s, %s, %s)",
         ('Produto Exemplo 1', 'Descrição do produto 1', 99.99, 10, 5, 'Categoria 1', True)),
        ("INSERT INTO products (name, description, price, stock, min_stock, category, active) VALUES (%s, %s, %s, %s, %s, %s, %s)",
         ('Produto Exemplo 2', 'Descrição do produto 2', 149.99, 20, 8, 'Categoria 2', True))
    ],
    'supplies': [
        ("INSERT INTO supplies (name, description, part_number, stock, min_stock, unit_cost, location, active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
         ('Insumo Exemplo 1', 'Descrição do insumo 1', 'INS-001', 15, 5, 29.99, 'Almoxarifado A', True)),
        ("INSERT INTO supplies (name, description, part_number, stock, min_stock, unit_cost, location, active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
         ('Insumo Exemplo 2', 'Descrição do insumo 2', 'INS-002', 25, 10, 39.99, 'Almoxarifado B', True))
    ],
    'technicians': [
        ("INSERT INTO technicians (name, registration_number, specialty, status, phone, email, cpf, address, city, state, zip_code, notes, active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
         ('Técnico Exemplo 1', 'T001', 'Elétrica', 'active', '(11) 91234-5678', 'tecnico1@exemplo.com', '123.456.789-00', 'Rua dos Técnicos, 123', 'São Paulo', 'SP', '01234-567', 'Técnico especializado em elétrica', True)),
        ("INSERT INTO technicians (name, registration_number, specialty, status, phone, email, cpf, address, city, state, zip_code, notes, active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
         ('Técnico Exemplo 2', 'T002', 'Mecânica', 'active', '(11) 98765-4321', 'tecnico2@exemplo.com', '987.654.321-00', 'Rua dos Técnicos, 456', 'São Paulo', 'SP', '04321-765', 'Técnico especializado em mecânica', True))
    ],
    'bank_accounts': [
        ("INSERT INTO bank_accounts (name, bank_name, agency, account_number, pix_key, cost_center, status, active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
         ('Conta Principal', 'Banco Exemplo', '1234', '12345-6', 'exemplo@pix.com', 'Administrativo', 'active', True))
    ]
}

def verify_all_database_tables():
    """Verifica e corrige todas as tabelas do projeto no MySQL"""
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
        
        # Verificar todas as tabelas essenciais
        print("\n[DEBUG] Verificando todas as tabelas essenciais...")
        
        # Obter a lista de tabelas existentes
        cursor.execute("SHOW TABLES")
        existing_tables = [table[f'Tables_in_{DB_NAME}'] for table in cursor.fetchall()]
        print(f"[DEBUG] Tabelas existentes: {existing_tables}")
        
        # Verificar e criar tabelas ausentes
        missing_tables = [table for table in ESSENTIAL_TABLES if table not in existing_tables]
        print(f"[DEBUG] Tabelas ausentes: {missing_tables}")
        
        # Criar tabelas na ordem correta (considerando dependências)
        created_tables = []
        
        # Primeira passagem: criar tabelas sem dependências
        for table in missing_tables:
            if table in ['users', 'customers', 'suppliers', 'technicians', 'bank_accounts']:
                try:
                    print(f"[DEBUG] Criando tabela {table}...")
                    cursor.execute(TABLE_DEFINITIONS[table])
                    created_tables.append(table)
                    print(f"[DEBUG] Tabela {table} criada com sucesso!")
                    
                    # Inserir dados de exemplo
                    if table in SAMPLE_DATA:
                        print(f"[DEBUG] Inserindo dados de exemplo na tabela {table}...")
                        for query, params in SAMPLE_DATA[table]:
                            cursor.execute(query, params)
                        conn.commit()
                        print(f"[DEBUG] Dados de exemplo inseridos na tabela {table} com sucesso!")
                except mysql.connector.Error as e:
                    print(f"[DEBUG] Erro ao criar tabela {table}: {e}")
        
        # Remover tabelas já criadas da lista de ausentes
        missing_tables = [table for table in missing_tables if table not in created_tables]
        
        # Segunda passagem: criar tabelas com dependências de primeiro nível
        for table in missing_tables:
            if table in ['products', 'supplies', 'equipment']:
                try:
                    print(f"[DEBUG] Criando tabela {table}...")
                    cursor.execute(TABLE_DEFINITIONS[table])
                    created_tables.append(table)
                    print(f"[DEBUG] Tabela {table} criada com sucesso!")
                    
                    # Inserir dados de exemplo
                    if table in SAMPLE_DATA:
                        print(f"[DEBUG] Inserindo dados de exemplo na tabela {table}...")
                        for query, params in SAMPLE_DATA[table]:
                            cursor.execute(query, params)
                        conn.commit()
                        print(f"[DEBUG] Dados de exemplo inseridos na tabela {table} com sucesso!")
                except mysql.connector.Error as e:
                    print(f"[DEBUG] Erro ao criar tabela {table}: {e}")
        
        # Remover tabelas já criadas da lista de ausentes
        missing_tables = [table for table in missing_tables if table not in created_tables]
        
        # Terceira passagem: criar tabelas com dependências de segundo nível
        for table in missing_tables:
            if table in ['maintenance_plans', 'alerts', 'hour_meter_readings', 'accounts_payable', 'accounts_receivable']:
                try:
                    print(f"[DEBUG] Criando tabela {table}...")
                    cursor.execute(TABLE_DEFINITIONS[table])
                    created_tables.append(table)
                    print(f"[DEBUG] Tabela {table} criada com sucesso!")
                except mysql.connector.Error as e:
                    print(f"[DEBUG] Erro ao criar tabela {table}: {e}")
        
        # Remover tabelas já criadas da lista de ausentes
        missing_tables = [table for table in missing_tables if table not in created_tables]
        
        # Quarta passagem: criar tabelas com dependências de terceiro nível
        for table in missing_tables:
            if table in ['service_orders']:
                try:
                    print(f"[DEBUG] Criando tabela {table}...")
                    cursor.execute(TABLE_DEFINITIONS[table])
                    created_tables.append(table)
                    print(f"[DEBUG] Tabela {table} criada com sucesso!")
                except mysql.connector.Error as e:
                    print(f"[DEBUG] Erro ao criar tabela {table}: {e}")
        
        # Remover tabelas já criadas da lista de ausentes
        missing_tables = [table for table in missing_tables if table not in created_tables]
        
        # Quinta passagem: criar tabelas com dependências de quarto nível
        for table in missing_tables:
            if table in ['service_order_items', 'service_order_labor']:
                try:
                    print(f"[DEBUG] Criando tabela {table}...")
                    cursor.execute(TABLE_DEFINITIONS[table])
                    created_tables.append(table)
                    print(f"[DEBUG] Tabela {table} criada com sucesso!")
                except mysql.connector.Error as e:
                    print(f"[DEBUG] Erro ao criar tabela {table}: {e}")
        
        # Verificar o conteúdo das tabelas
        print("\n[DEBUG] Verificando o conteúdo das tabelas...")
        for table in ESSENTIAL_TABLES:
            if table in existing_tables or table in created_tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                print(f"[DEBUG] Tabela {table}: {count} registros")
                
                # Se a tabela estiver vazia e tiver dados de exemplo, inserir
                if count == 0 and table in SAMPLE_DATA:
                    print(f"[DEBUG] Tabela {table} está vazia. Inserindo dados de exemplo...")
                    for query, params in SAMPLE_DATA[table]:
                        cursor.execute(query, params)
                    conn.commit()
                    print(f"[DEBUG] Dados de exemplo inseridos na tabela {table} com sucesso!")
        
        # Verificar se o usuário admin existe
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()
        if admin_user:
            print(f"[DEBUG] Usuário admin encontrado: ID={admin_user['id']}, Senha={admin_user['password']}")
            
            # Garantir que a senha do admin seja 'admin'
            if admin_user['password'] != 'admin':
                print("[DEBUG] Atualizando a senha do usuário admin...")
                cursor.execute("UPDATE users SET password = 'admin', status = 'active' WHERE username = 'admin'")
                conn.commit()
                print("[DEBUG] Senha do usuário admin atualizada para 'admin'")
        else:
            print("[DEBUG] Usuário admin não encontrado. Criando...")
            cursor.execute("""
                INSERT INTO users (username, password, name, email, role, status, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, ('admin', 'admin', 'Administrador', 'admin@example.com', 'admin', 'active', True))
            conn.commit()
            print("[DEBUG] Usuário admin criado com sucesso!")
        
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
    verify_all_database_tables()
