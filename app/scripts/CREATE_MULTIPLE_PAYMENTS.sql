-- =====================================================
-- SISTEMA DE MÚLTIPLOS PAGAMENTOS
-- =====================================================
-- Permite uma venda ter várias formas de pagamento
-- Exemplo: R$ 100 em dinheiro + R$ 350 em cartão
-- Calcula troco automaticamente
-- =====================================================

USE supply_chain_system;

-- =====================================================
-- TABELA: Pagamentos da Venda
-- =====================================================

CREATE TABLE IF NOT EXISTS sale_payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sale_id INT NOT NULL COMMENT 'Venda relacionada',
    payment_method_id INT NOT NULL COMMENT 'Forma de pagamento',
    amount DECIMAL(10,2) NOT NULL COMMENT 'Valor pago nesta forma',
    installments INT DEFAULT 1 COMMENT 'Número de parcelas (se aplicável)',
    notes TEXT NULL COMMENT 'Observações',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INT NULL COMMENT 'Usuário que registrou',
    
    FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
    FOREIGN KEY (payment_method_id) REFERENCES payment_methods_config(id),
    
    INDEX idx_sale (sale_id),
    INDEX idx_method (payment_method_id),
    INDEX idx_created (created_at)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
COMMENT='Registro de múltiplos pagamentos por venda';

-- =====================================================
-- ALTERAR TABELA SALES: Adicionar campos
-- =====================================================

-- Verificar e adicionar coluna de troco
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'supply_chain_system' 
    AND TABLE_NAME = 'sales' 
    AND COLUMN_NAME = 'change_amount'
);

SET @sql_add_column = IF(@col_exists = 0,
    'ALTER TABLE sales ADD COLUMN change_amount DECIMAL(10,2) DEFAULT 0 COMMENT ''Troco dado ao cliente''',
    'SELECT ''Coluna change_amount já existe'' AS info'
);

PREPARE stmt FROM @sql_add_column;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Verificar e adicionar coluna de pagamento total
SET @col_exists2 = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'supply_chain_system' 
    AND TABLE_NAME = 'sales' 
    AND COLUMN_NAME = 'total_paid'
);

SET @sql_add_column2 = IF(@col_exists2 = 0,
    'ALTER TABLE sales ADD COLUMN total_paid DECIMAL(10,2) DEFAULT 0 COMMENT ''Total pago pelo cliente''',
    'SELECT ''Coluna total_paid já existe'' AS info'
);

PREPARE stmt FROM @sql_add_column2;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =====================================================
-- VIEW: Resumo de Pagamentos por Venda
-- =====================================================

CREATE OR REPLACE VIEW vw_sale_payments_summary AS
SELECT 
    s.id as sale_id,
    s.net_total,
    s.total_paid,
    s.change_amount,
    COUNT(sp.id) as payment_methods_count,
    GROUP_CONCAT(
        CONCAT(pmc.name, ': R$ ', FORMAT(sp.amount, 2))
        SEPARATOR ' | '
    ) as payment_details,
    CASE 
        WHEN s.total_paid >= s.net_total THEN 'PAGO'
        WHEN s.total_paid > 0 THEN 'PARCIAL'
        ELSE 'PENDENTE'
    END as payment_status
FROM sales s
LEFT JOIN sale_payments sp ON sp.sale_id = s.id
LEFT JOIN payment_methods_config pmc ON pmc.id = sp.payment_method_id
GROUP BY s.id;

-- =====================================================
-- PROCEDURE: Registrar Pagamento
-- =====================================================

DROP PROCEDURE IF EXISTS sp_register_payment;

DELIMITER $$

CREATE PROCEDURE sp_register_payment(
    IN p_sale_id INT,
    IN p_payment_method_id INT,
    IN p_amount DECIMAL(10,2),
    IN p_installments INT,
    IN p_notes TEXT,
    IN p_user_id INT
)
BEGIN
    DECLARE v_net_total DECIMAL(10,2);
    DECLARE v_total_paid DECIMAL(10,2);
    DECLARE v_change DECIMAL(10,2);
    
    -- Buscar total da venda
    SELECT net_total INTO v_net_total 
    FROM sales 
    WHERE id = p_sale_id;
    
    IF v_net_total IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Venda não encontrada';
    END IF;
    
    -- Inserir pagamento
    INSERT INTO sale_payments (
        sale_id,
        payment_method_id,
        amount,
        installments,
        notes,
        created_by
    ) VALUES (
        p_sale_id,
        p_payment_method_id,
        p_amount,
        p_installments,
        p_notes,
        p_user_id
    );
    
    -- Calcular total pago
    SELECT COALESCE(SUM(amount), 0) INTO v_total_paid
    FROM sale_payments
    WHERE sale_id = p_sale_id;
    
    -- Calcular troco (se pago a mais)
    SET v_change = GREATEST(0, v_total_paid - v_net_total);
    
    -- Atualizar venda
    UPDATE sales
    SET total_paid = v_total_paid,
        change_amount = v_change
    WHERE id = p_sale_id;
    
    -- Retornar informações
    SELECT 
        p_sale_id as sale_id,
        v_net_total as net_total,
        v_total_paid as total_paid,
        v_change as change_amount,
        (v_total_paid >= v_net_total) as is_fully_paid;
        
END$$

DELIMITER ;

-- =====================================================
-- PROCEDURE: Finalizar Venda com Múltiplos Pagamentos
-- =====================================================

DROP PROCEDURE IF EXISTS sp_finalize_sale_with_payments;

DELIMITER $$

CREATE PROCEDURE sp_finalize_sale_with_payments(
    IN p_sale_id INT,
    IN p_user_id INT
)
BEGIN
    DECLARE v_net_total DECIMAL(10,2);
    DECLARE v_total_paid DECIMAL(10,2);
    
    -- Buscar total da venda
    SELECT net_total INTO v_net_total 
    FROM sales 
    WHERE id = p_sale_id;
    
    -- Buscar total pago
    SELECT COALESCE(SUM(amount), 0) INTO v_total_paid
    FROM sale_payments
    WHERE sale_id = p_sale_id;
    
    -- Verificar se está totalmente pago
    IF v_total_paid < v_net_total THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Venda não está totalmente paga';
    END IF;
    
    -- Confirmar venda
    UPDATE sales
    SET status = 'confirmed',
        confirmed_at = NOW()
    WHERE id = p_sale_id;
    
    -- Vincular ao caixa (se houver caixa aberto)
    UPDATE sales s
    INNER JOIN cash_register cr ON cr.user_id = p_user_id AND cr.status = 'open'
    SET s.cash_register_id = cr.id
    WHERE s.id = p_sale_id;
    
    SELECT 'Venda finalizada com sucesso!' as message;
    
END$$

DELIMITER ;

-- =====================================================
-- TRIGGER: Atualizar estoque ao confirmar venda
-- =====================================================

DROP TRIGGER IF EXISTS trg_sale_confirmed_update_stock;

DELIMITER $$

CREATE TRIGGER trg_sale_confirmed_update_stock
AFTER UPDATE ON sales
FOR EACH ROW
BEGIN
    -- Se mudou para confirmed
    IF NEW.status = 'confirmed' AND OLD.status != 'confirmed' THEN
        
        -- Baixar estoque dos itens
        UPDATE stock_movements sm
        INNER JOIN sale_items si ON si.id = sm.reference_id AND sm.reference_type = 'sale_item'
        SET sm.processed = 1,
            sm.processed_at = NOW()
        WHERE si.sale_id = NEW.id;
        
    END IF;
END$$

DELIMITER ;

-- =====================================================
-- DADOS DE EXEMPLO (OPCIONAL)
-- =====================================================

-- Exemplo de venda com múltiplos pagamentos
-- INSERT INTO sale_payments (sale_id, payment_method_id, amount, created_by)
-- VALUES 
--   (1, 1, 100.00, 1),  -- R$ 100 em dinheiro
--   (1, 2, 350.50, 1);  -- R$ 350,50 em cartão de crédito

-- =====================================================
-- VERIFICAÇÕES
-- =====================================================

SELECT 'Tabela sale_payments criada!' as status;

SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    COLUMN_TYPE,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'supply_chain_system'
AND TABLE_NAME = 'sale_payments'
ORDER BY ORDINAL_POSITION;

SELECT 'Procedures criadas:' as info;
SHOW PROCEDURE STATUS WHERE Db = 'supply_chain_system' AND Name LIKE 'sp_%payment%';

SELECT 'View criada:' as info;
SELECT * FROM vw_sale_payments_summary LIMIT 0;

SELECT '✅ Sistema de múltiplos pagamentos instalado com sucesso!' as resultado;
