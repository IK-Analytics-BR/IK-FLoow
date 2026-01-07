-- =====================================================
-- CRIAR TABELAS FINANCEIRAS COMPLETAS
-- =====================================================
-- Data: 22/10/2025
-- Objetivo: Criar todas as tabelas necessárias para integração financeira
-- =====================================================

-- =====================================================
-- 1. TABELA: accounts_receivable (Contas a Receber)
-- =====================================================

CREATE TABLE IF NOT EXISTS accounts_receivable (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Relacionamentos
    customer_id INT NOT NULL,
    sale_id INT NULL,
    
    -- Dados da Conta
    invoice_number VARCHAR(50) NULL,
    description TEXT NULL,
    
    -- Valores
    total_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    paid_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    discount_amount DECIMAL(10,2) NULL DEFAULT 0.00,
    interest_amount DECIMAL(10,2) NULL DEFAULT 0.00,
    
    -- Datas
    issue_date DATE NULL,
    due_date DATE NOT NULL,
    payment_date DATE NULL,
    
    -- Status
    status ENUM('pending', 'partial', 'paid', 'overdue', 'cancelled') NOT NULL DEFAULT 'pending',
    
    -- Forma de Pagamento
    payment_method VARCHAR(50) NULL,
    bank_account_id INT NULL,
    
    -- Auditoria
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Índices
    INDEX idx_customer (customer_id),
    INDEX idx_sale (sale_id),
    INDEX idx_due_date (due_date),
    INDEX idx_status (status),
    
    -- Foreign Keys
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE SET NULL,
    FOREIGN KEY (bank_account_id) REFERENCES bank_accounts(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 2. TABELA: cash_flow (Fluxo de Caixa)
-- =====================================================

CREATE TABLE IF NOT EXISTS cash_flow (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Tipo de Movimento
    flow_type ENUM('inflow', 'outflow') NOT NULL COMMENT 'Entrada ou Saída',
    category ENUM('sale', 'purchase', 'expense', 'transfer', 'adjustment', 'other') NOT NULL,
    
    -- Valores
    amount DECIMAL(10,2) NOT NULL,
    
    -- Relacionamentos
    bank_account_id INT NULL,
    reference_type VARCHAR(50) NULL COMMENT 'sale, purchase_order, expense, etc',
    reference_id INT NULL COMMENT 'ID do registro relacionado',
    
    -- Informações
    description TEXT NULL,
    transaction_date DATE NOT NULL,
    
    -- Dados Adicionais
    payment_method VARCHAR(50) NULL,
    customer_id INT NULL,
    supplier_id INT NULL,
    
    -- Auditoria
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT NULL,
    
    -- Índices
    INDEX idx_flow_type (flow_type),
    INDEX idx_category (category),
    INDEX idx_date (transaction_date),
    INDEX idx_bank_account (bank_account_id),
    INDEX idx_reference (reference_type, reference_id),
    
    -- Foreign Keys
    FOREIGN KEY (bank_account_id) REFERENCES bank_accounts(id) ON DELETE SET NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 3. ATUALIZAR: bank_accounts (adicionar empresa_id)
-- =====================================================

ALTER TABLE bank_accounts 
ADD COLUMN IF NOT EXISTS empresa_id INT NULL AFTER id,
ADD INDEX idx_empresa (empresa_id);

-- Nota: Não adiciono FK aqui porque empresas pode não ter sido criada ainda

-- =====================================================
-- 4. VERIFICAÇÃO FINAL
-- =====================================================

-- Verificar tabelas criadas
SELECT 
    'accounts_receivable' AS tabela,
    COUNT(*) AS total_registros
FROM accounts_receivable
UNION ALL
SELECT 
    'cash_flow',
    COUNT(*)
FROM cash_flow
UNION ALL
SELECT 
    'bank_accounts',
    COUNT(*)
FROM bank_accounts;

-- Ver estrutura
DESCRIBE accounts_receivable;
DESCRIBE cash_flow;
DESCRIBE bank_accounts;

-- =====================================================
-- DADOS DE EXEMPLO (OPCIONAL - COMENTADO)
-- =====================================================

-- Descomentar para inserir dados de teste:

/*
-- Exemplo: Conta a Receber
INSERT INTO accounts_receivable 
(customer_id, sale_id, total_amount, due_date, status, payment_method)
VALUES 
(1, 1, 150.00, DATE_ADD(CURDATE(), INTERVAL 30 DAY), 'pending', 'credit');

-- Exemplo: Fluxo de Caixa
INSERT INTO cash_flow
(flow_type, category, amount, transaction_date, description, reference_type, reference_id)
VALUES
('inflow', 'sale', 150.00, CURDATE(), 'Venda #1 - Teste', 'sale', 1);
*/

SELECT 'Tabelas criadas com sucesso!' AS status;
