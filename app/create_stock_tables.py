"""
Script para criar as tabelas de estoque necessárias no banco de dados.
"""

from database import get_db

def create_stock_tables():
    """Cria as tabelas de estoque necessárias."""
    db = get_db()
    
    # 1. Criar tabela de locais de estoque
    print("Criando tabela de locais de estoque...")
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS stock_locations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    # Inserir local padrão se não existir
    result = db.fetch_one("SELECT COUNT(*) as count FROM stock_locations")
    if result and result['count'] == 0:
        db.insert("""
            INSERT INTO stock_locations (name, description, active)
            VALUES (%s, %s, %s)
        """, ("Estoque Principal", "Local principal de armazenamento", True))
        print("Local de estoque padrão criado.")
    
    # 2. Criar tabela de estoque atual
    print("Criando tabela de estoque atual...")
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS current_stock (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT NOT NULL,
            location_id INT NOT NULL,
            quantity DECIMAL(15,4) DEFAULT 0,
            min_stock DECIMAL(15,4) DEFAULT 0,
            max_stock DECIMAL(15,4) DEFAULT 0,
            last_purchase_date DATE,
            last_sale_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (location_id) REFERENCES stock_locations(id),
            UNIQUE KEY product_location (product_id, location_id)
        )
    """)
    
    # 3. Criar tabela de movimentações de estoque
    print("Criando tabela de movimentações de estoque...")
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT NOT NULL,
            movement_type VARCHAR(50) NOT NULL,
            quantity DECIMAL(15,4) NOT NULL,
            reference_id INT,
            reference_type VARCHAR(50),
            unit_cost DECIMAL(15,4),
            location_id INT NOT NULL,
            notes TEXT,
            created_by INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (location_id) REFERENCES stock_locations(id)
        )
    """)
    
    # 4. Inicializar estoque para produtos existentes
    print("Inicializando estoque para produtos existentes...")
    products = db.fetch_all("SELECT id FROM products WHERE active = TRUE")
    location_id = 1  # ID do local padrão
    
    for product in products:
        # Verificar se já existe estoque para este produto
        stock = db.fetch_one("""
            SELECT * FROM current_stock 
            WHERE product_id = %s AND location_id = %s
        """, (product['id'], location_id))
        
        if not stock:
            # Usar o campo stock_quantity da tabela products se existir
            product_detail = db.fetch_one("SELECT stock_quantity FROM products WHERE id = %s", (product['id'],))
            quantity = product_detail.get('stock_quantity', 0) if product_detail else 0
            
            # Inserir estoque inicial
            db.insert("""
                INSERT INTO current_stock (product_id, location_id, quantity, min_stock, max_stock)
                VALUES (%s, %s, %s, %s, %s)
            """, (product['id'], location_id, quantity, 5, 100))
            print(f"Estoque inicial criado para produto ID {product['id']}: {quantity} unidades")
    
    print("\nTabelas de estoque criadas e inicializadas com sucesso!")

if __name__ == "__main__":
    create_stock_tables()
