-- Script para criar tabelas do módulo de Notas Fiscais
-- Autor: Sistema de Gestão de Suprimentos
-- Data: 2025-09-08

-- Tabela de Notas Fiscais
CREATE TABLE IF NOT EXISTS invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT NOT NULL,
    invoice_number VARCHAR(50) NOT NULL,
    invoice_series VARCHAR(10),
    issue_date DATE NOT NULL,
    total_amount DECIMAL(15, 2) NOT NULL DEFAULT 0,
    tax_amount DECIMAL(15, 2) NOT NULL DEFAULT 0,
    notes TEXT,
    purchase_order_id INT,
    status ENUM('pending', 'verified', 'processed', 'canceled') NOT NULL DEFAULT 'pending',
    verified_date DATE,
    processed_date DATE,
    xml_path VARCHAR(255),
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_invoice_number (invoice_number),
    INDEX idx_status (status),
    INDEX idx_issue_date (issue_date)
);

-- Tabela de Itens da Nota Fiscal
CREATE TABLE IF NOT EXISTS invoice_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity DECIMAL(15, 3) NOT NULL DEFAULT 0,
    unit_price DECIMAL(15, 2) NOT NULL DEFAULT 0,
    total_price DECIMAL(15, 2) NOT NULL DEFAULT 0,
    tax_percentage DECIMAL(10, 2) NOT NULL DEFAULT 0,
    tax_amount DECIMAL(15, 2) NOT NULL DEFAULT 0,
    status ENUM('active', 'processed', 'canceled') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    INDEX idx_invoice_id (invoice_id),
    INDEX idx_product_id (product_id)
);

-- Trigger para atualizar o valor total da nota fiscal quando um item é adicionado
DELIMITER //
CREATE TRIGGER IF NOT EXISTS update_invoice_total_after_insert
AFTER INSERT ON invoice_items
FOR EACH ROW
BEGIN
    UPDATE invoices
    SET total_amount = (SELECT COALESCE(SUM(total_price), 0) FROM invoice_items WHERE invoice_id = NEW.invoice_id),
        tax_amount = (SELECT COALESCE(SUM(tax_amount), 0) FROM invoice_items WHERE invoice_id = NEW.invoice_id)
    WHERE id = NEW.invoice_id;
END //
DELIMITER ;

-- Trigger para atualizar o valor total da nota fiscal quando um item é atualizado
DELIMITER //
CREATE TRIGGER IF NOT EXISTS update_invoice_total_after_update
AFTER UPDATE ON invoice_items
FOR EACH ROW
BEGIN
    UPDATE invoices
    SET total_amount = (SELECT COALESCE(SUM(total_price), 0) FROM invoice_items WHERE invoice_id = NEW.invoice_id),
        tax_amount = (SELECT COALESCE(SUM(tax_amount), 0) FROM invoice_items WHERE invoice_id = NEW.invoice_id)
    WHERE id = NEW.invoice_id;
END //
DELIMITER ;

-- Trigger para atualizar o valor total da nota fiscal quando um item é removido
DELIMITER //
CREATE TRIGGER IF NOT EXISTS update_invoice_total_after_delete
AFTER DELETE ON invoice_items
FOR EACH ROW
BEGIN
    UPDATE invoices
    SET total_amount = (SELECT COALESCE(SUM(total_price), 0) FROM invoice_items WHERE invoice_id = OLD.invoice_id),
        tax_amount = (SELECT COALESCE(SUM(tax_amount), 0) FROM invoice_items WHERE invoice_id = OLD.invoice_id)
    WHERE id = OLD.invoice_id;
END //
DELIMITER ;

-- Procedimento para processar uma nota fiscal
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS process_invoice(IN p_invoice_id INT)
BEGIN
    DECLARE v_status VARCHAR(20);
    
    -- Verificar o status atual da nota fiscal
    SELECT status INTO v_status FROM invoices WHERE id = p_invoice_id;
    
    -- Apenas notas fiscais verificadas podem ser processadas
    IF v_status = 'verified' THEN
        -- Atualizar o status da nota fiscal
        UPDATE invoices
        SET status = 'processed', processed_date = CURDATE()
        WHERE id = p_invoice_id;
        
        -- Atualizar o status dos itens
        UPDATE invoice_items
        SET status = 'processed'
        WHERE invoice_id = p_invoice_id;
        
        -- Registrar movimentações de estoque para cada item
        INSERT INTO stock_movements (
            product_id, movement_type, quantity, reference_id, reference_type,
            unit_cost, location_id, notes, created_by
        )
        SELECT 
            ii.product_id, 'purchase', ii.quantity, i.id, 'invoice',
            ii.unit_price, 1, CONCAT('Recebimento da NF ', i.invoice_number), i.created_by
        FROM invoice_items ii
        JOIN invoices i ON ii.invoice_id = i.id
        WHERE ii.invoice_id = p_invoice_id;
        
        -- Atualizar o estoque atual
        UPDATE current_stock cs
        JOIN invoice_items ii ON cs.product_id = ii.product_id
        SET cs.quantity = cs.quantity + ii.quantity,
            cs.last_purchase_date = CURDATE()
        WHERE ii.invoice_id = p_invoice_id
        AND cs.location_id = 1;
        
        -- Inserir no estoque produtos que não existem ainda
        INSERT INTO current_stock (product_id, location_id, quantity, min_stock, max_stock, last_purchase_date)
        SELECT 
            ii.product_id, 1, ii.quantity, 0, 0, CURDATE()
        FROM invoice_items ii
        LEFT JOIN current_stock cs ON ii.product_id = cs.product_id AND cs.location_id = 1
        WHERE ii.invoice_id = p_invoice_id
        AND cs.id IS NULL;
    END IF;
END //
DELIMITER ;

-- Procedimento para cancelar uma nota fiscal
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS cancel_invoice(IN p_invoice_id INT)
BEGIN
    DECLARE v_status VARCHAR(20);
    
    -- Verificar o status atual da nota fiscal
    SELECT status INTO v_status FROM invoices WHERE id = p_invoice_id;
    
    -- Apenas notas fiscais pendentes ou verificadas podem ser canceladas
    IF v_status IN ('pending', 'verified') THEN
        -- Atualizar o status da nota fiscal
        UPDATE invoices
        SET status = 'canceled', active = FALSE
        WHERE id = p_invoice_id;
        
        -- Atualizar o status dos itens
        UPDATE invoice_items
        SET status = 'canceled'
        WHERE invoice_id = p_invoice_id;
    END IF;
END //
DELIMITER ;
