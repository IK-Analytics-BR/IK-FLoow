-- Script para criar as tabelas do Módulo de Compras
-- Importação NF-e e Estoque

-- Tabela de Fornecedores (complemento)
-- Adicionando campos específicos para o módulo de compras
ALTER TABLE suppliers
ADD COLUMN IF NOT EXISTS contact_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS contact_email VARCHAR(100),
ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(20),
ADD COLUMN IF NOT EXISTS payment_terms VARCHAR(100),
ADD COLUMN IF NOT EXISTS delivery_time INT COMMENT 'Tempo médio de entrega em dias',
ADD COLUMN IF NOT EXISTS min_order_value DECIMAL(10, 2) COMMENT 'Valor mínimo para pedidos',
ADD COLUMN IF NOT EXISTS last_purchase_date DATE,
ADD COLUMN IF NOT EXISTS rating INT COMMENT 'Avaliação de 1 a 5';

-- Tabela de Produtos Fornecidos
CREATE TABLE IF NOT EXISTS supplier_products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT NOT NULL,
    product_id INT NOT NULL,
    supplier_code VARCHAR(50) COMMENT 'Código do produto no fornecedor',
    last_price DECIMAL(10, 2) NOT NULL,
    min_quantity INT COMMENT 'Quantidade mínima para compra',
    delivery_time INT COMMENT 'Tempo de entrega em dias',
    last_purchase_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    UNIQUE KEY (supplier_id, product_id)
);

-- Tabela de Histórico de Preços
CREATE TABLE IF NOT EXISTS price_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT NOT NULL,
    product_id INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    date DATE NOT NULL,
    invoice_number VARCHAR(50),
    purchase_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Tabela de Pedidos de Compra
CREATE TABLE IF NOT EXISTS purchase_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_number VARCHAR(20) NOT NULL UNIQUE,
    supplier_id INT NOT NULL,
    order_date DATE NOT NULL,
    expected_delivery_date DATE,
    status ENUM('draft', 'sent', 'confirmed', 'partially_received', 'received', 'canceled') NOT NULL DEFAULT 'draft',
    total_amount DECIMAL(10, 2) NOT NULL DEFAULT 0,
    payment_terms VARCHAR(100),
    delivery_address TEXT,
    notes TEXT,
    created_by INT NOT NULL COMMENT 'ID do usuário que criou o pedido',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Tabela de Itens do Pedido de Compra
CREATE TABLE IF NOT EXISTS purchase_order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    purchase_order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    expected_delivery_date DATE,
    received_quantity INT NOT NULL DEFAULT 0,
    status ENUM('pending', 'partially_received', 'received', 'canceled') NOT NULL DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Tabela de Notas Fiscais de Entrada
CREATE TABLE IF NOT EXISTS purchase_invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_number VARCHAR(50) NOT NULL,
    invoice_series VARCHAR(10),
    supplier_id INT NOT NULL,
    issue_date DATE NOT NULL,
    entry_date DATE NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    tax_amount DECIMAL(10, 2) NOT NULL DEFAULT 0,
    freight_amount DECIMAL(10, 2) NOT NULL DEFAULT 0,
    discount_amount DECIMAL(10, 2) NOT NULL DEFAULT 0,
    purchase_order_id INT,
    xml_file VARCHAR(255) COMMENT 'Caminho para o arquivo XML',
    pdf_file VARCHAR(255) COMMENT 'Caminho para o arquivo PDF',
    status ENUM('draft', 'confirmed', 'canceled') NOT NULL DEFAULT 'draft',
    notes TEXT,
    created_by INT NOT NULL COMMENT 'ID do usuário que registrou a nota',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Tabela de Itens da Nota Fiscal
CREATE TABLE IF NOT EXISTS purchase_invoice_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity DECIMAL(10, 3) NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    tax_amount DECIMAL(10, 2) NOT NULL DEFAULT 0,
    discount_amount DECIMAL(10, 2) NOT NULL DEFAULT 0,
    purchase_order_item_id INT,
    ncm VARCHAR(20) COMMENT 'Código NCM do produto',
    cfop VARCHAR(10) COMMENT 'Código CFOP',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (invoice_id) REFERENCES purchase_invoices(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (purchase_order_item_id) REFERENCES purchase_order_items(id)
);

-- Tabela de Movimentações de Estoque
CREATE TABLE IF NOT EXISTS stock_movements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    movement_type ENUM('purchase', 'sale', 'adjustment', 'transfer', 'return') NOT NULL,
    quantity DECIMAL(10, 3) NOT NULL COMMENT 'Positivo para entrada, negativo para saída',
    reference_id INT COMMENT 'ID da referência (nota fiscal, pedido, etc.)',
    reference_type VARCHAR(50) COMMENT 'Tipo da referência (invoice, order, etc.)',
    unit_cost DECIMAL(10, 2) COMMENT 'Custo unitário na movimentação',
    location_id INT COMMENT 'ID do local de estoque',
    notes TEXT,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Tabela de Locais de Estoque
CREATE TABLE IF NOT EXISTS stock_locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabela de Estoque Atual (pode ser uma view materializada)
CREATE TABLE IF NOT EXISTS current_stock (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    location_id INT NOT NULL,
    quantity DECIMAL(10, 3) NOT NULL DEFAULT 0,
    reserved_quantity DECIMAL(10, 3) NOT NULL DEFAULT 0,
    available_quantity DECIMAL(10, 3) GENERATED ALWAYS AS (quantity - reserved_quantity) STORED,
    min_stock DECIMAL(10, 3) NOT NULL DEFAULT 0,
    max_stock DECIMAL(10, 3) NOT NULL DEFAULT 0,
    last_count_date DATE,
    average_cost DECIMAL(10, 2) NOT NULL DEFAULT 0,
    last_purchase_date DATE,
    last_sale_date DATE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (location_id) REFERENCES stock_locations(id),
    UNIQUE KEY (product_id, location_id)
);

-- Tabela de Importação de XML
CREATE TABLE IF NOT EXISTS xml_imports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    import_date DATETIME NOT NULL,
    status ENUM('pending', 'processing', 'completed', 'error') NOT NULL DEFAULT 'pending',
    invoice_id INT,
    error_message TEXT,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (invoice_id) REFERENCES purchase_invoices(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Tabela de Sugestões de Compra
CREATE TABLE IF NOT EXISTS purchase_suggestions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    current_stock DECIMAL(10, 3) NOT NULL,
    min_stock DECIMAL(10, 3) NOT NULL,
    suggested_quantity DECIMAL(10, 3) NOT NULL,
    priority ENUM('low', 'medium', 'high', 'critical') NOT NULL,
    last_purchase_date DATE,
    last_purchase_price DECIMAL(10, 2),
    suggested_supplier_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN NOT NULL DEFAULT FALSE,
    purchase_order_id INT,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (suggested_supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id)
);

-- Índices para melhorar o desempenho
CREATE INDEX idx_supplier_products_supplier ON supplier_products(supplier_id);
CREATE INDEX idx_supplier_products_product ON supplier_products(product_id);
CREATE INDEX idx_price_history_supplier_product ON price_history(supplier_id, product_id);
CREATE INDEX idx_purchase_orders_supplier ON purchase_orders(supplier_id);
CREATE INDEX idx_purchase_orders_status ON purchase_orders(status);
CREATE INDEX idx_purchase_order_items_order ON purchase_order_items(purchase_order_id);
CREATE INDEX idx_purchase_order_items_product ON purchase_order_items(product_id);
CREATE INDEX idx_purchase_invoices_supplier ON purchase_invoices(supplier_id);
CREATE INDEX idx_purchase_invoices_order ON purchase_invoices(purchase_order_id);
CREATE INDEX idx_purchase_invoice_items_invoice ON purchase_invoice_items(invoice_id);
CREATE INDEX idx_purchase_invoice_items_product ON purchase_invoice_items(product_id);
CREATE INDEX idx_stock_movements_product ON stock_movements(product_id);
CREATE INDEX idx_stock_movements_type ON stock_movements(movement_type);
CREATE INDEX idx_current_stock_product ON current_stock(product_id);
CREATE INDEX idx_current_stock_location ON current_stock(location_id);
CREATE INDEX idx_purchase_suggestions_product ON purchase_suggestions(product_id);
CREATE INDEX idx_purchase_suggestions_priority ON purchase_suggestions(priority);

-- Triggers para atualizar o estoque automaticamente

-- Trigger para atualizar o estoque quando um item de nota fiscal é confirmado
DELIMITER //
CREATE TRIGGER after_invoice_item_insert
AFTER INSERT ON purchase_invoice_items
FOR EACH ROW
BEGIN
    DECLARE invoice_status VARCHAR(20);
    
    -- Verificar se a nota fiscal está confirmada
    SELECT status INTO invoice_status
    FROM purchase_invoices
    WHERE id = NEW.invoice_id;
    
    IF invoice_status = 'confirmed' THEN
        -- Inserir movimento de estoque
        INSERT INTO stock_movements (
            product_id, 
            movement_type, 
            quantity, 
            reference_id, 
            reference_type, 
            unit_cost, 
            location_id, 
            notes, 
            created_by
        )
        SELECT 
            NEW.product_id,
            'purchase',
            NEW.quantity,
            NEW.invoice_id,
            'invoice',
            NEW.unit_price,
            (SELECT id FROM stock_locations WHERE is_default = TRUE LIMIT 1),
            'Entrada por nota fiscal',
            pi.created_by
        FROM purchase_invoices pi
        WHERE pi.id = NEW.invoice_id;
        
        -- Atualizar o estoque atual
        INSERT INTO current_stock (
            product_id, 
            location_id, 
            quantity, 
            min_stock, 
            max_stock, 
            average_cost, 
            last_purchase_date
        )
        VALUES (
            NEW.product_id,
            (SELECT id FROM stock_locations WHERE is_default = TRUE LIMIT 1),
            NEW.quantity,
            0, -- min_stock padrão
            0, -- max_stock padrão
            NEW.unit_price,
            CURDATE()
        )
        ON DUPLICATE KEY UPDATE
            quantity = quantity + NEW.quantity,
            average_cost = ((average_cost * quantity) + (NEW.unit_price * NEW.quantity)) / (quantity + NEW.quantity),
            last_purchase_date = CURDATE();
        
        -- Atualizar o histórico de preços
        INSERT INTO price_history (
            supplier_id,
            product_id,
            price,
            date,
            invoice_number,
            purchase_id
        )
        SELECT 
            pi.supplier_id,
            NEW.product_id,
            NEW.unit_price,
            pi.issue_date,
            pi.invoice_number,
            pi.purchase_order_id
        FROM purchase_invoices pi
        WHERE pi.id = NEW.invoice_id;
        
        -- Atualizar o último preço no cadastro de produtos do fornecedor
        INSERT INTO supplier_products (
            supplier_id,
            product_id,
            last_price,
            last_purchase_date
        )
        SELECT 
            pi.supplier_id,
            NEW.product_id,
            NEW.unit_price,
            pi.issue_date
        FROM purchase_invoices pi
        WHERE pi.id = NEW.invoice_id
        ON DUPLICATE KEY UPDATE
            last_price = NEW.unit_price,
            last_purchase_date = pi.issue_date;
    END IF;
END //
DELIMITER ;

-- Trigger para atualizar o status do pedido de compra quando todos os itens forem recebidos
DELIMITER //
CREATE TRIGGER after_purchase_order_item_update
AFTER UPDATE ON purchase_order_items
FOR EACH ROW
BEGIN
    DECLARE total_items INT;
    DECLARE received_items INT;
    DECLARE partially_received_items INT;
    
    IF NEW.status != OLD.status THEN
        -- Contar itens do pedido
        SELECT 
            COUNT(*),
            SUM(IF(status = 'received', 1, 0)),
            SUM(IF(status = 'partially_received', 1, 0))
        INTO total_items, received_items, partially_received_items
        FROM purchase_order_items
        WHERE purchase_order_id = NEW.purchase_order_id;
        
        -- Atualizar o status do pedido
        IF received_items = total_items THEN
            UPDATE purchase_orders
            SET status = 'received'
            WHERE id = NEW.purchase_order_id;
        ELSEIF received_items > 0 OR partially_received_items > 0 THEN
            UPDATE purchase_orders
            SET status = 'partially_received'
            WHERE id = NEW.purchase_order_id;
        END IF;
    END IF;
END //
DELIMITER ;

-- Trigger para atualizar o valor total do pedido de compra quando um item é adicionado ou alterado
DELIMITER //
CREATE TRIGGER after_purchase_order_item_change
AFTER INSERT ON purchase_order_items
FOR EACH ROW
BEGIN
    UPDATE purchase_orders
    SET total_amount = (
        SELECT SUM(total_price)
        FROM purchase_order_items
        WHERE purchase_order_id = NEW.purchase_order_id
    )
    WHERE id = NEW.purchase_order_id;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER after_purchase_order_item_update_total
AFTER UPDATE ON purchase_order_items
FOR EACH ROW
BEGIN
    IF NEW.total_price != OLD.total_price THEN
        UPDATE purchase_orders
        SET total_amount = (
            SELECT SUM(total_price)
            FROM purchase_order_items
            WHERE purchase_order_id = NEW.purchase_order_id
        )
        WHERE id = NEW.purchase_order_id;
    END IF;
END //
DELIMITER ;

-- Procedure para gerar sugestões de compra
DELIMITER //
CREATE PROCEDURE generate_purchase_suggestions()
BEGIN
    -- Limpar sugestões antigas não processadas
    DELETE FROM purchase_suggestions
    WHERE processed = FALSE;
    
    -- Inserir novas sugestões
    INSERT INTO purchase_suggestions (
        product_id,
        current_stock,
        min_stock,
        suggested_quantity,
        priority,
        last_purchase_date,
        last_purchase_price,
        suggested_supplier_id
    )
    SELECT 
        cs.product_id,
        cs.quantity,
        cs.min_stock,
        GREATEST(cs.min_stock - cs.quantity, 0) AS suggested_quantity,
        CASE 
            WHEN cs.quantity = 0 THEN 'critical'
            WHEN cs.quantity < cs.min_stock * 0.5 THEN 'high'
            WHEN cs.quantity < cs.min_stock THEN 'medium'
            ELSE 'low'
        END AS priority,
        cs.last_purchase_date,
        cs.average_cost,
        (
            SELECT sp.supplier_id
            FROM supplier_products sp
            WHERE sp.product_id = cs.product_id
            ORDER BY sp.last_price ASC
            LIMIT 1
        ) AS suggested_supplier_id
    FROM current_stock cs
    WHERE cs.quantity < cs.min_stock AND cs.min_stock > 0;
END //
DELIMITER ;

-- Evento para executar a geração de sugestões de compra diariamente
DELIMITER //
CREATE EVENT IF NOT EXISTS daily_purchase_suggestions
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_DATE + INTERVAL 1 DAY
DO
BEGIN
    CALL generate_purchase_suggestions();
END //
DELIMITER ;
