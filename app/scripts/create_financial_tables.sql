-- Script para criar as tabelas do Módulo Financeiro
-- Contas a Pagar, Contas a Receber e Fluxo de Caixa

-- Tabela de Contas Bancárias
CREATE TABLE IF NOT EXISTS bank_accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    agency VARCHAR(20),
    account_number VARCHAR(30),
    pix_key VARCHAR(100),
    cost_center VARCHAR(50) NOT NULL,
    status ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Tabela de Contas a Pagar
CREATE TABLE IF NOT EXISTS accounts_payable (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT NOT NULL,
    invoice_number VARCHAR(50),
    description VARCHAR(255) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    installments INT NOT NULL DEFAULT 1,
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    payment_method ENUM('boleto', 'ted', 'pix', 'credit_card', 'debit_card', 'cash', 'check', 'other') NOT NULL,
    bank_account_id INT NOT NULL,
    status ENUM('pending', 'paid', 'overdue', 'canceled') NOT NULL DEFAULT 'pending',
    payment_date DATE,
    notes TEXT,
    origin ENUM('purchase', 'manual') NOT NULL,
    purchase_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (bank_account_id) REFERENCES bank_accounts(id)
);

-- Tabela de Parcelas de Contas a Pagar
CREATE TABLE IF NOT EXISTS payable_installments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    payable_id INT NOT NULL,
    installment_number INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    due_date DATE NOT NULL,
    payment_date DATE,
    status ENUM('pending', 'paid', 'overdue', 'canceled') NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (payable_id) REFERENCES accounts_payable(id)
);

-- Tabela de Contas a Receber
CREATE TABLE IF NOT EXISTS accounts_receivable (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    invoice_number VARCHAR(50),
    description VARCHAR(255) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    installments INT NOT NULL DEFAULT 1,
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    payment_method ENUM('cash', 'credit_card', 'debit_card', 'pix', 'boleto', 'transfer', 'check', 'other') NOT NULL,
    bank_account_id INT NOT NULL,
    status ENUM('pending', 'received', 'overdue', 'canceled') NOT NULL DEFAULT 'pending',
    receipt_date DATE,
    notes TEXT,
    origin ENUM('sale', 'service', 'manual') NOT NULL,
    sale_id INT,
    service_order_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (bank_account_id) REFERENCES bank_accounts(id)
);

-- Tabela de Parcelas de Contas a Receber
CREATE TABLE IF NOT EXISTS receivable_installments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    receivable_id INT NOT NULL,
    installment_number INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    due_date DATE NOT NULL,
    receipt_date DATE,
    status ENUM('pending', 'received', 'overdue', 'canceled') NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (receivable_id) REFERENCES accounts_receivable(id)
);

-- Tabela de Fluxo de Caixa (view materializada)
CREATE TABLE IF NOT EXISTS cash_flow (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    type ENUM('income', 'expense') NOT NULL,
    description VARCHAR(255) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    bank_account_id INT NOT NULL,
    reference_id INT,
    reference_type ENUM('payable', 'receivable', 'manual') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (bank_account_id) REFERENCES bank_accounts(id)
);

-- Tabela de Alertas Financeiros
CREATE TABLE IF NOT EXISTS financial_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type ENUM('payable_due', 'receivable_due', 'payable_overdue', 'receivable_overdue', 'low_balance') NOT NULL,
    reference_id INT,
    reference_type ENUM('payable', 'receivable', 'bank_account') NOT NULL,
    message VARCHAR(255) NOT NULL,
    due_date DATE,
    status ENUM('active', 'read', 'resolved') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Índices para melhorar o desempenho
CREATE INDEX idx_accounts_payable_supplier ON accounts_payable(supplier_id);
CREATE INDEX idx_accounts_payable_status ON accounts_payable(status);
CREATE INDEX idx_accounts_payable_due_date ON accounts_payable(due_date);
CREATE INDEX idx_accounts_receivable_customer ON accounts_receivable(customer_id);
CREATE INDEX idx_accounts_receivable_status ON accounts_receivable(status);
CREATE INDEX idx_accounts_receivable_due_date ON accounts_receivable(due_date);
CREATE INDEX idx_payable_installments_payable ON payable_installments(payable_id);
CREATE INDEX idx_payable_installments_due_date ON payable_installments(due_date);
CREATE INDEX idx_receivable_installments_receivable ON receivable_installments(receivable_id);
CREATE INDEX idx_receivable_installments_due_date ON receivable_installments(due_date);
CREATE INDEX idx_cash_flow_date ON cash_flow(date);
CREATE INDEX idx_cash_flow_type ON cash_flow(type);
CREATE INDEX idx_cash_flow_bank_account ON cash_flow(bank_account_id);

-- Triggers para atualizar o fluxo de caixa automaticamente

-- Trigger para inserir no fluxo de caixa quando uma parcela de conta a pagar for paga
DELIMITER //
CREATE TRIGGER after_payable_installment_paid
AFTER UPDATE ON payable_installments
FOR EACH ROW
BEGIN
    IF NEW.status = 'paid' AND OLD.status != 'paid' THEN
        INSERT INTO cash_flow (date, type, description, amount, bank_account_id, reference_id, reference_type)
        SELECT 
            NEW.payment_date, 
            'expense', 
            CONCAT('Pagamento - ', ap.description, ' - Parcela ', NEW.installment_number, '/', ap.installments),
            NEW.amount,
            ap.bank_account_id,
            NEW.payable_id,
            'payable'
        FROM accounts_payable ap
        WHERE ap.id = NEW.payable_id;
    END IF;
END //
DELIMITER ;

-- Trigger para inserir no fluxo de caixa quando uma parcela de conta a receber for recebida
DELIMITER //
CREATE TRIGGER after_receivable_installment_received
AFTER UPDATE ON receivable_installments
FOR EACH ROW
BEGIN
    IF NEW.status = 'received' AND OLD.status != 'received' THEN
        INSERT INTO cash_flow (date, type, description, amount, bank_account_id, reference_id, reference_type)
        SELECT 
            NEW.receipt_date, 
            'income', 
            CONCAT('Recebimento - ', ar.description, ' - Parcela ', NEW.installment_number, '/', ar.installments),
            NEW.amount,
            ar.bank_account_id,
            NEW.receivable_id,
            'receivable'
        FROM accounts_receivable ar
        WHERE ar.id = NEW.receivable_id;
    END IF;
END //
DELIMITER ;

-- Trigger para atualizar o status da conta a pagar quando todas as parcelas forem pagas
DELIMITER //
CREATE TRIGGER after_payable_installment_update
AFTER UPDATE ON payable_installments
FOR EACH ROW
BEGIN
    DECLARE total_installments INT;
    DECLARE paid_installments INT;
    
    SELECT COUNT(*), SUM(IF(status = 'paid', 1, 0))
    INTO total_installments, paid_installments
    FROM payable_installments
    WHERE payable_id = NEW.payable_id;
    
    IF paid_installments = total_installments THEN
        UPDATE accounts_payable
        SET status = 'paid', payment_date = CURDATE()
        WHERE id = NEW.payable_id;
    END IF;
END //
DELIMITER ;

-- Trigger para atualizar o status da conta a receber quando todas as parcelas forem recebidas
DELIMITER //
CREATE TRIGGER after_receivable_installment_update
AFTER UPDATE ON receivable_installments
FOR EACH ROW
BEGIN
    DECLARE total_installments INT;
    DECLARE received_installments INT;
    
    SELECT COUNT(*), SUM(IF(status = 'received', 1, 0))
    INTO total_installments, received_installments
    FROM receivable_installments
    WHERE receivable_id = NEW.receivable_id;
    
    IF received_installments = total_installments THEN
        UPDATE accounts_receivable
        SET status = 'received', receipt_date = CURDATE()
        WHERE id = NEW.receivable_id;
    END IF;
END //
DELIMITER ;

-- Procedure para criar parcelas automaticamente
DELIMITER //
CREATE PROCEDURE create_installments(
    IN p_type VARCHAR(10),
    IN p_id INT,
    IN p_installments INT,
    IN p_total_amount DECIMAL(10, 2),
    IN p_first_due_date DATE,
    IN p_interval INT
)
BEGIN
    DECLARE i INT DEFAULT 1;
    DECLARE installment_amount DECIMAL(10, 2);
    DECLARE due_date DATE;
    
    -- Calcular o valor de cada parcela
    SET installment_amount = ROUND(p_total_amount / p_installments, 2);
    SET due_date = p_first_due_date;
    
    -- Criar as parcelas
    WHILE i <= p_installments DO
        IF p_type = 'payable' THEN
            INSERT INTO payable_installments (payable_id, installment_number, amount, due_date, status)
            VALUES (p_id, i, installment_amount, due_date, 'pending');
        ELSE
            INSERT INTO receivable_installments (receivable_id, installment_number, amount, due_date, status)
            VALUES (p_id, i, installment_amount, due_date, 'pending');
        END IF;
        
        -- Ajustar o valor da última parcela para compensar arredondamentos
        IF i = p_installments - 1 THEN
            SET installment_amount = p_total_amount - (installment_amount * (p_installments - 1));
        END IF;
        
        -- Calcular a próxima data de vencimento
        SET due_date = DATE_ADD(due_date, INTERVAL p_interval DAY);
        SET i = i + 1;
    END WHILE;
END //
DELIMITER ;

-- Procedure para atualizar o status de contas vencidas
DELIMITER //
CREATE PROCEDURE update_overdue_accounts()
BEGIN
    -- Atualizar contas a pagar vencidas
    UPDATE payable_installments
    SET status = 'overdue'
    WHERE status = 'pending' AND due_date < CURDATE();
    
    UPDATE accounts_payable
    SET status = 'overdue'
    WHERE status = 'pending' AND due_date < CURDATE();
    
    -- Atualizar contas a receber vencidas
    UPDATE receivable_installments
    SET status = 'overdue'
    WHERE status = 'pending' AND due_date < CURDATE();
    
    UPDATE accounts_receivable
    SET status = 'overdue'
    WHERE status = 'pending' AND due_date < CURDATE();
    
    -- Criar alertas para contas vencidas
    INSERT INTO financial_alerts (type, reference_id, reference_type, message, due_date, status)
    SELECT 
        'payable_overdue',
        id,
        'payable',
        CONCAT('Conta a pagar vencida: ', description),
        due_date,
        'active'
    FROM accounts_payable
    WHERE status = 'overdue' AND id NOT IN (
        SELECT reference_id FROM financial_alerts 
        WHERE reference_type = 'payable' AND type = 'payable_overdue' AND status = 'active'
    );
    
    INSERT INTO financial_alerts (type, reference_id, reference_type, message, due_date, status)
    SELECT 
        'receivable_overdue',
        id,
        'receivable',
        CONCAT('Conta a receber vencida: ', description),
        due_date,
        'active'
    FROM accounts_receivable
    WHERE status = 'overdue' AND id NOT IN (
        SELECT reference_id FROM financial_alerts 
        WHERE reference_type = 'receivable' AND type = 'receivable_overdue' AND status = 'active'
    );
END //
DELIMITER ;

-- Procedure para criar alertas de contas a vencer
DELIMITER //
CREATE PROCEDURE create_due_alerts(IN days_ahead INT)
BEGIN
    DECLARE due_date_limit DATE;
    SET due_date_limit = DATE_ADD(CURDATE(), INTERVAL days_ahead DAY);
    
    -- Criar alertas para contas a pagar a vencer
    INSERT INTO financial_alerts (type, reference_id, reference_type, message, due_date, status)
    SELECT 
        'payable_due',
        id,
        'payable',
        CONCAT('Conta a pagar vence em ', DATEDIFF(due_date, CURDATE()), ' dias: ', description),
        due_date,
        'active'
    FROM accounts_payable
    WHERE status = 'pending' 
    AND due_date BETWEEN CURDATE() AND due_date_limit
    AND id NOT IN (
        SELECT reference_id FROM financial_alerts 
        WHERE reference_type = 'payable' AND type = 'payable_due' AND status = 'active'
    );
    
    -- Criar alertas para contas a receber a vencer
    INSERT INTO financial_alerts (type, reference_id, reference_type, message, due_date, status)
    SELECT 
        'receivable_due',
        id,
        'receivable',
        CONCAT('Conta a receber vence em ', DATEDIFF(due_date, CURDATE()), ' dias: ', description),
        due_date,
        'active'
    FROM accounts_receivable
    WHERE status = 'pending' 
    AND due_date BETWEEN CURDATE() AND due_date_limit
    AND id NOT IN (
        SELECT reference_id FROM financial_alerts 
        WHERE reference_type = 'receivable' AND type = 'receivable_due' AND status = 'active'
    );
END //
DELIMITER ;

-- Evento para executar as procedures de atualização diariamente
DELIMITER //
CREATE EVENT IF NOT EXISTS daily_financial_update
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_DATE + INTERVAL 1 DAY
DO
BEGIN
    CALL update_overdue_accounts();
    CALL create_due_alerts(7); -- Alertas para contas que vencem em 7 dias
END //
DELIMITER ;
