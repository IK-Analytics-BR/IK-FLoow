-- Script para criar tabelas do módulo de Estoque
-- Autor: Sistema de Gestão de Suprimentos
-- Data: 2025-09-08

-- Tabela de Locais de Estoque
CREATE TABLE IF NOT EXISTS stock_locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    address TEXT,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY (name)
);

-- Inserir local de estoque padrão se não existir
INSERT INTO stock_locations (name, description, is_default, active)
SELECT 'Estoque Principal', 'Local de estoque principal da empresa', TRUE, TRUE
FROM dual
WHERE NOT EXISTS (SELECT 1 FROM stock_locations WHERE is_default = TRUE);

-- Tabela de Estoque Atual
CREATE TABLE IF NOT EXISTS current_stock (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    location_id INT NOT NULL,
    quantity DECIMAL(15, 3) NOT NULL DEFAULT 0,
    min_stock DECIMAL(15, 3) NOT NULL DEFAULT 0,
    max_stock DECIMAL(15, 3) NOT NULL DEFAULT 0,
    reorder_point DECIMAL(15, 3) NOT NULL DEFAULT 0,
    reorder_quantity DECIMAL(15, 3) NOT NULL DEFAULT 0,
    last_purchase_date DATE,
    last_sale_date DATE,
    last_count_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (location_id) REFERENCES stock_locations(id),
    UNIQUE KEY (product_id, location_id)
);

-- Tabela de Movimentações de Estoque
CREATE TABLE IF NOT EXISTS stock_movements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    movement_type ENUM('purchase', 'sale', 'adjustment_add', 'adjustment_subtract', 'transfer_in', 'transfer_out', 'return', 'loss', 'count') NOT NULL,
    quantity DECIMAL(15, 3) NOT NULL,
    reference_id INT,
    reference_type VARCHAR(50),
    unit_cost DECIMAL(15, 2),
    location_id INT NOT NULL,
    notes TEXT,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (location_id) REFERENCES stock_locations(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_product_id (product_id),
    INDEX idx_movement_type (movement_type),
    INDEX idx_created_at (created_at)
);

-- Tabela de Inventários Físicos
CREATE TABLE IF NOT EXISTS inventory_counts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    location_id INT NOT NULL,
    count_date DATE NOT NULL,
    status ENUM('draft', 'in_progress', 'completed', 'canceled') NOT NULL DEFAULT 'draft',
    notes TEXT,
    created_by INT NOT NULL,
    completed_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES stock_locations(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (completed_by) REFERENCES users(id),
    INDEX idx_count_date (count_date),
    INDEX idx_status (status)
);

-- Tabela de Itens de Inventário Físico
CREATE TABLE IF NOT EXISTS inventory_count_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inventory_count_id INT NOT NULL,
    product_id INT NOT NULL,
    expected_quantity DECIMAL(15, 3) NOT NULL DEFAULT 0,
    counted_quantity DECIMAL(15, 3),
    difference DECIMAL(15, 3),
    status ENUM('pending', 'counted', 'adjusted') NOT NULL DEFAULT 'pending',
    notes TEXT,
    counted_by INT,
    counted_at TIMESTAMP,
    FOREIGN KEY (inventory_count_id) REFERENCES inventory_counts(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (counted_by) REFERENCES users(id),
    UNIQUE KEY (inventory_count_id, product_id)
);

-- Trigger para atualizar a diferença quando a quantidade contada for inserida
DELIMITER //
CREATE TRIGGER IF NOT EXISTS update_count_difference_after_update
BEFORE UPDATE ON inventory_count_items
FOR EACH ROW
BEGIN
    IF NEW.counted_quantity IS NOT NULL THEN
        SET NEW.difference = NEW.counted_quantity - NEW.expected_quantity;
        SET NEW.status = 'counted';
    END IF;
END //
DELIMITER ;

-- Procedimento para iniciar um inventário físico
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS start_inventory_count(IN p_location_id INT, IN p_user_id INT, IN p_notes TEXT)
BEGIN
    DECLARE v_inventory_id INT;
    
    -- Inserir o cabeçalho do inventário
    INSERT INTO inventory_counts (location_id, count_date, status, notes, created_by)
    VALUES (p_location_id, CURDATE(), 'in_progress', p_notes, p_user_id);
    
    -- Obter o ID do inventário criado
    SET v_inventory_id = LAST_INSERT_ID();
    
    -- Inserir os itens do inventário com base no estoque atual
    INSERT INTO inventory_count_items (inventory_count_id, product_id, expected_quantity)
    SELECT v_inventory_id, cs.product_id, cs.quantity
    FROM current_stock cs
    WHERE cs.location_id = p_location_id AND cs.quantity > 0;
    
    -- Retornar o ID do inventário criado
    SELECT v_inventory_id;
END //
DELIMITER ;

-- Procedimento para finalizar um inventário físico e ajustar o estoque
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS complete_inventory_count(IN p_inventory_id INT, IN p_user_id INT)
BEGIN
    DECLARE v_location_id INT;
    
    -- Obter o local do inventário
    SELECT location_id INTO v_location_id
    FROM inventory_counts
    WHERE id = p_inventory_id;
    
    -- Atualizar o status do inventário
    UPDATE inventory_counts
    SET status = 'completed', completed_by = p_user_id, completed_at = NOW()
    WHERE id = p_inventory_id;
    
    -- Ajustar o estoque com base nas diferenças encontradas
    -- Inserir movimentações de estoque para cada item com diferença
    INSERT INTO stock_movements (
        product_id, movement_type, quantity, reference_id, reference_type,
        unit_cost, location_id, notes, created_by
    )
    SELECT 
        ici.product_id,
        CASE WHEN ici.difference > 0 THEN 'adjustment_add' ELSE 'adjustment_subtract' END,
        ABS(ici.difference),
        p_inventory_id,
        'inventory_count',
        0,
        v_location_id,
        CONCAT('Ajuste de inventário #', p_inventory_id),
        p_user_id
    FROM inventory_count_items ici
    WHERE ici.inventory_count_id = p_inventory_id
    AND ici.difference <> 0;
    
    -- Atualizar o estoque atual
    UPDATE current_stock cs
    JOIN inventory_count_items ici ON cs.product_id = ici.product_id
    SET cs.quantity = ici.counted_quantity,
        cs.last_count_date = CURDATE()
    WHERE ici.inventory_count_id = p_inventory_id
    AND cs.location_id = v_location_id;
    
    -- Atualizar o status dos itens do inventário
    UPDATE inventory_count_items
    SET status = 'adjusted'
    WHERE inventory_count_id = p_inventory_id
    AND status = 'counted';
END //
DELIMITER ;
