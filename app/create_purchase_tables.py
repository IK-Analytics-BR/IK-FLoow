"""
Script para criar as tabelas relacionadas a pedidos de compra.
"""

from database import get_db

def create_purchase_tables():
    """Cria as tabelas necessárias para o funcionamento dos pedidos de compra."""
    db = get_db()
    
    # 1. Criar tabela de pedidos de compra
    print("Criando tabela de pedidos de compra...")
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_number VARCHAR(20) NOT NULL,
            supplier_id INT NOT NULL,
            order_date DATE NOT NULL,
            expected_delivery_date DATE,
            payment_terms VARCHAR(100),
            delivery_address TEXT,
            notes TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'draft',
            created_by INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
            UNIQUE KEY (order_number)
        )
    """)
    
    # 2. Criar tabela de itens de pedido de compra
    print("Criando tabela de itens de pedido de compra...")
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS purchase_order_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            purchase_order_id INT NOT NULL,
            product_id INT NOT NULL,
            quantity DECIMAL(15,4) NOT NULL,
            unit_price DECIMAL(15,4) NOT NULL,
            total_price DECIMAL(15,4) NOT NULL,
            expected_delivery_date DATE,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)
    
    # 3. Verificar se a tabela suppliers existe
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
    
    print("\nTabelas de pedidos de compra criadas com sucesso!")

if __name__ == "__main__":
    create_purchase_tables()
