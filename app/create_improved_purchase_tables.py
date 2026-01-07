"""
Script para criar as tabelas melhoradas relacionadas a pedidos de compra.
"""

from database import get_db

def create_improved_purchase_tables():
    """Cria as tabelas melhoradas para o funcionamento dos pedidos de compra."""
    db = get_db()
    
    # 1. Verificar se a tabela suppliers existe e criar se necessário
    tables = db.fetch_all("SHOW TABLES")
    if not any(table.get('Tables_in_supply_chain_system') == 'suppliers' for table in tables):
        print("Criando tabela de fornecedores...")
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                legal_name VARCHAR(100),
                tax_id VARCHAR(20),
                contact_name VARCHAR(100),
                email VARCHAR(100),
                phone VARCHAR(20),
                address TEXT,
                city VARCHAR(50),
                state VARCHAR(2),
                zip_code VARCHAR(10),
                country VARCHAR(50) DEFAULT 'Brasil',
                website VARCHAR(100),
                notes TEXT,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        # Inserir um fornecedor padrão
        db.insert("""
            INSERT INTO suppliers (name, legal_name, tax_id, contact_name, email, phone, active)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, ("Fornecedor Padrão", "Fornecedor Padrão Ltda", "00.000.000/0001-00", "Contato Padrão", "contato@fornecedor.com", "(00) 0000-0000", True))
        print("Fornecedor padrão criado.")
    
    # 2. Criar tabela de condições de pagamento
    print("Criando tabela de condições de pagamento...")
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS payment_terms (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            days VARCHAR(100) NOT NULL,
            description TEXT,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    # Inserir condições de pagamento padrão
    payment_terms = [
        ("À vista", "0", "Pagamento à vista"),
        ("30 dias", "30", "Pagamento em 30 dias"),
        ("30/60 dias", "30,60", "Pagamento em 2 parcelas de 30 e 60 dias"),
        ("30/60/90 dias", "30,60,90", "Pagamento em 3 parcelas de 30, 60 e 90 dias")
    ]
    
    for term in payment_terms:
        existing = db.fetch_one("SELECT id FROM payment_terms WHERE name = %s", (term[0],))
        if not existing:
            db.insert("""
                INSERT INTO payment_terms (name, days, description, active)
                VALUES (%s, %s, %s, %s)
            """, (term[0], term[1], term[2], True))
    
    # 3. Criar tabela de formas de pagamento
    print("Criando tabela de formas de pagamento...")
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS payment_methods (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    # Inserir formas de pagamento padrão
    payment_methods = [
        ("Boleto", "Pagamento via boleto bancário"),
        ("PIX", "Pagamento via PIX"),
        ("Transferência", "Pagamento via transferência bancária"),
        ("Cartão de Crédito", "Pagamento via cartão de crédito"),
        ("Dinheiro", "Pagamento em dinheiro")
    ]
    
    for method in payment_methods:
        existing = db.fetch_one("SELECT id FROM payment_methods WHERE name = %s", (method[0],))
        if not existing:
            db.insert("""
                INSERT INTO payment_methods (name, description, active)
                VALUES (%s, %s, %s)
            """, (method[0], method[1], True))
    
    # 4. Criar tabela de centros de custo
    print("Criando tabela de centros de custo...")
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS cost_centers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            code VARCHAR(20) NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    # Inserir centro de custo padrão
    existing = db.fetch_one("SELECT id FROM cost_centers WHERE code = %s", ("ADM",))
    if not existing:
        db.insert("""
            INSERT INTO cost_centers (code, name, description, active)
            VALUES (%s, %s, %s, %s)
        """, ("ADM", "Administrativo", "Centro de custo administrativo", True))
    
    # 5. Criar ou alterar tabela de pedidos de compra com estrutura completa
    print("Criando/alterando tabela de pedidos de compra...")
    
    # Verificar se a tabela já existe
    if any(table.get('Tables_in_supply_chain_system') == 'purchase_orders' for table in tables):
        # Tabela já existe, verificar se precisa adicionar colunas
        print("Tabela purchase_orders já existe, verificando se precisa adicionar colunas...")
        
        # Verificar colunas existentes
        columns = db.fetch_all("DESCRIBE purchase_orders")
        column_names = [column['Field'] for column in columns]
        
        # Adicionar colunas que não existem
        new_columns = {
            "contact_name": "VARCHAR(100)",
            "payment_term_id": "INT",
            "payment_method_id": "INT",
            "cost_center_id": "INT",
            "subtotal": "DECIMAL(15,4) DEFAULT 0",
            "discount_percent": "DECIMAL(5,2) DEFAULT 0",
            "discount_value": "DECIMAL(15,4) DEFAULT 0",
            "shipping_cost": "DECIMAL(15,4) DEFAULT 0",
            "insurance_cost": "DECIMAL(15,4) DEFAULT 0",
            "other_costs": "DECIMAL(15,4) DEFAULT 0",
            "tax_value": "DECIMAL(15,4) DEFAULT 0",
            "total_value": "DECIMAL(15,4) DEFAULT 0"
        }
        
        for column, data_type in new_columns.items():
            if column not in column_names:
                print(f"Adicionando coluna {column} à tabela purchase_orders...")
                db.execute_query(f"ALTER TABLE purchase_orders ADD COLUMN {column} {data_type}")
        
        # Adicionar chaves estrangeiras se não existirem
        foreign_keys = {
            "payment_term_id": "payment_terms(id)",
            "payment_method_id": "payment_methods(id)",
            "cost_center_id": "cost_centers(id)"
        }
        
        for column, reference in foreign_keys.items():
            if column not in column_names:
                print(f"Adicionando chave estrangeira para {column}...")
                db.execute_query(f"ALTER TABLE purchase_orders ADD CONSTRAINT fk_{column} FOREIGN KEY ({column}) REFERENCES {reference}")
    else:
        # Criar a tabela do zero
        db.execute_query("""
            CREATE TABLE purchase_orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_number VARCHAR(20) NOT NULL,
                supplier_id INT NOT NULL,
                order_date DATE NOT NULL,
                expected_delivery_date DATE,
                contact_name VARCHAR(100),
                payment_term_id INT,
                payment_method_id INT,
                cost_center_id INT,
                delivery_address TEXT,
                notes TEXT,
                subtotal DECIMAL(15,4) DEFAULT 0,
                discount_percent DECIMAL(5,2) DEFAULT 0,
                discount_value DECIMAL(15,4) DEFAULT 0,
                shipping_cost DECIMAL(15,4) DEFAULT 0,
                insurance_cost DECIMAL(15,4) DEFAULT 0,
                other_costs DECIMAL(15,4) DEFAULT 0,
                tax_value DECIMAL(15,4) DEFAULT 0,
                total_value DECIMAL(15,4) DEFAULT 0,
                status VARCHAR(20) NOT NULL DEFAULT 'draft',
                created_by INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY (payment_term_id) REFERENCES payment_terms(id),
                FOREIGN KEY (payment_method_id) REFERENCES payment_methods(id),
                FOREIGN KEY (cost_center_id) REFERENCES cost_centers(id),
                UNIQUE KEY (order_number)
            )
        """)
    
    # 6. Criar ou alterar tabela de itens de pedido de compra
    print("Criando/alterando tabela de itens de pedido de compra...")
    
    if any(table.get('Tables_in_supply_chain_system') == 'purchase_order_items' for table in tables):
        # Tabela já existe, verificar se precisa adicionar colunas
        print("Tabela purchase_order_items já existe, verificando se precisa adicionar colunas...")
        
        # Verificar colunas existentes
        columns = db.fetch_all("DESCRIBE purchase_order_items")
        column_names = [column['Field'] for column in columns]
        
        # Adicionar colunas que não existem
        new_columns = {
            "discount_percent": "DECIMAL(5,2) DEFAULT 0",
            "discount_value": "DECIMAL(15,4) DEFAULT 0",
            "tax_percent": "DECIMAL(5,2) DEFAULT 0",
            "tax_value": "DECIMAL(15,4) DEFAULT 0",
            "lot_number": "VARCHAR(50)",
            "serial_number": "VARCHAR(50)",
            "received_quantity": "DECIMAL(15,4) DEFAULT 0"
        }
        
        for column, data_type in new_columns.items():
            if column not in column_names:
                print(f"Adicionando coluna {column} à tabela purchase_order_items...")
                db.execute_query(f"ALTER TABLE purchase_order_items ADD COLUMN {column} {data_type}")
    else:
        # Criar a tabela do zero
        db.execute_query("""
            CREATE TABLE purchase_order_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                purchase_order_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity DECIMAL(15,4) NOT NULL,
                unit_price DECIMAL(15,4) NOT NULL,
                discount_percent DECIMAL(5,2) DEFAULT 0,
                discount_value DECIMAL(15,4) DEFAULT 0,
                tax_percent DECIMAL(5,2) DEFAULT 0,
                tax_value DECIMAL(15,4) DEFAULT 0,
                total_price DECIMAL(15,4) NOT NULL,
                expected_delivery_date DATE,
                lot_number VARCHAR(50),
                serial_number VARCHAR(50),
                received_quantity DECIMAL(15,4) DEFAULT 0,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
    
    # 7. Criar tabela de recebimento de pedidos
    print("Criando tabela de recebimento de pedidos...")
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS purchase_order_receipts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            purchase_order_id INT NOT NULL,
            receipt_date DATE NOT NULL,
            invoice_number VARCHAR(50),
            invoice_date DATE,
            invoice_value DECIMAL(15,4),
            notes TEXT,
            created_by INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id)
        )
    """)
    
    # 8. Criar tabela de itens de recebimento
    print("Criando tabela de itens de recebimento...")
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS purchase_order_receipt_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            receipt_id INT NOT NULL,
            purchase_order_item_id INT NOT NULL,
            quantity DECIMAL(15,4) NOT NULL,
            lot_number VARCHAR(50),
            serial_number VARCHAR(50),
            expiry_date DATE,
            location_id INT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (receipt_id) REFERENCES purchase_order_receipts(id),
            FOREIGN KEY (purchase_order_item_id) REFERENCES purchase_order_items(id),
            FOREIGN KEY (location_id) REFERENCES stock_locations(id)
        )
    """)
    
    # 9. Criar tabela de contas a pagar relacionadas a pedidos
    print("Criando tabela de contas a pagar relacionadas a pedidos...")
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS accounts_payable (
            id INT AUTO_INCREMENT PRIMARY KEY,
            purchase_order_id INT,
            invoice_id INT,
            document_number VARCHAR(50),
            description TEXT,
            supplier_id INT NOT NULL,
            issue_date DATE NOT NULL,
            due_date DATE NOT NULL,
            amount DECIMAL(15,4) NOT NULL,
            payment_method_id INT,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            payment_date DATE,
            payment_amount DECIMAL(15,4),
            notes TEXT,
            created_by INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY (payment_method_id) REFERENCES payment_methods(id)
        )
    """)
    
    print("\nTabelas de pedidos de compra melhoradas criadas com sucesso!")

if __name__ == "__main__":
    create_improved_purchase_tables()
