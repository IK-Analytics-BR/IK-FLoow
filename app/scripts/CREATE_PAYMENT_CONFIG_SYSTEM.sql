-- =====================================================
-- SISTEMA DE CONFIGURAÇÃO DE FORMAS DE PAGAMENTO
-- =====================================================
-- Data: 23/10/2025
-- Objetivo: Criar sistema completo de regras de negócio
--           para formas de pagamento
-- =====================================================

USE supply_chain_system;

-- =====================================================
-- TABELA: payment_methods_config
-- Configuração de cada forma de pagamento
-- =====================================================

CREATE TABLE IF NOT EXISTS payment_methods_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Identificação
    name VARCHAR(100) NOT NULL UNIQUE COMMENT 'Nome da forma de pagamento',
    code VARCHAR(50) NOT NULL UNIQUE COMMENT 'Código interno (money, credit_card, etc)',
    
    -- Comportamento Financeiro
    financial_behavior ENUM('cash_flow', 'receivable', 'both') NOT NULL DEFAULT 'both'
        COMMENT 'cash_flow=só fluxo, receivable=só contas a receber, both=ambos',
    
    -- Configurações de Recebimento
    days_to_receive INT NOT NULL DEFAULT 0 
        COMMENT 'Dias até receber (D+0, D+1, D+30, etc)',
    
    receive_on_business_days BOOLEAN NOT NULL DEFAULT FALSE
        COMMENT 'Se TRUE, só conta dias úteis',
    
    -- Taxa da Operadora (para cartões)
    operator_fee_percent DECIMAL(5,2) NOT NULL DEFAULT 0.00
        COMMENT 'Taxa cobrada pela operadora (%)',
    
    operator_fee_fixed DECIMAL(10,2) NOT NULL DEFAULT 0.00
        COMMENT 'Taxa fixa cobrada pela operadora (R$)',
    
    -- Conta Bancária
    bank_account_id INT NULL
        COMMENT 'Conta bancária onde o dinheiro cai',
    
    -- Parcelamento
    allow_installments BOOLEAN NOT NULL DEFAULT FALSE
        COMMENT 'Permite parcelamento?',
    
    max_installments INT NOT NULL DEFAULT 1
        COMMENT 'Número máximo de parcelas',
    
    days_between_installments INT NOT NULL DEFAULT 30
        COMMENT 'Dias entre cada parcela',
    
    installment_fee_percent DECIMAL(5,2) NOT NULL DEFAULT 0.00
        COMMENT 'Taxa adicional por parcela (%)',
    
    -- Configurações Adicionais
    requires_approval BOOLEAN NOT NULL DEFAULT FALSE
        COMMENT 'Requer aprovação manual?',
    
    credit_analysis BOOLEAN NOT NULL DEFAULT FALSE
        COMMENT 'Requer análise de crédito?',
    
    generate_boleto BOOLEAN NOT NULL DEFAULT FALSE
        COMMENT 'Gera boleto automaticamente?',
    
    -- Status
    active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Auditoria
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Índices
    INDEX idx_code (code),
    INDEX idx_active (active),
    INDEX idx_financial_behavior (financial_behavior),
    
    -- Foreign Keys
    FOREIGN KEY (bank_account_id) REFERENCES bank_accounts(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- INSERIR CONFIGURAÇÕES PADRÃO
-- =====================================================

INSERT INTO payment_methods_config 
(name, code, financial_behavior, days_to_receive, operator_fee_percent, 
 allow_installments, max_installments, notes, active)
VALUES 
-- Dinheiro (à vista) - cai imediatamente no caixa
('Dinheiro', 'cash', 'cash_flow', 0, 0.00, FALSE, 1, 
 'Pagamento em dinheiro - recebimento imediato', TRUE),

-- PIX (à vista) - cai imediatamente
('PIX', 'pix', 'cash_flow', 0, 0.00, FALSE, 1, 
 'Pagamento via PIX - recebimento imediato', TRUE),

-- Débito - cai em D+1 com taxa de 2%
('Cartão de Débito', 'debit_card', 'cash_flow', 1, 2.00, FALSE, 1, 
 'Pagamento com cartão de débito - recebe em 1 dia útil com desconto de 2%', TRUE),

-- Crédito à Vista - cai em D+30 com taxa de 3.5%
('Cartão de Crédito (À Vista)', 'credit_card', 'cash_flow', 30, 3.50, FALSE, 1, 
 'Cartão de crédito à vista - recebe em 30 dias com desconto de 3.5%', TRUE),

-- Crédito Parcelado - parcelas com taxa de 4.5% por parcela
('Cartão de Crédito (Parcelado)', 'credit_card_installments', 'cash_flow', 30, 4.50, 
 TRUE, 12, 
 'Cartão de crédito parcelado - primeira parcela em 30 dias, demais a cada 30 dias, taxa 4.5% por parcela', TRUE),

-- Boleto - gera contas a receber com vencimento em 30 dias
('Boleto Bancário', 'boleto', 'receivable', 30, 0.00, FALSE, 1, 
 'Pagamento via boleto - gera conta a receber com vencimento em 30 dias', TRUE),

-- Crediário (carnê) - parcelas em contas a receber
('Crediário (Carnê)', 'store_credit', 'receivable', 30, 0.00, TRUE, 12, 
 'Crediário da loja - gera contas a receber parceladas', TRUE),

-- Transferência Bancária - cai em D+1
('Transferência Bancária', 'transfer', 'cash_flow', 1, 0.00, FALSE, 1, 
 'Transferência bancária - recebe em 1 dia útil', TRUE),

-- Cheque - cai na data do cheque (configurável)
('Cheque', 'check', 'receivable', 30, 0.00, FALSE, 1, 
 'Pagamento em cheque - gera conta a receber para controle', TRUE)

ON DUPLICATE KEY UPDATE 
    name = VALUES(name),
    financial_behavior = VALUES(financial_behavior),
    days_to_receive = VALUES(days_to_receive),
    operator_fee_percent = VALUES(operator_fee_percent),
    notes = VALUES(notes);

-- =====================================================
-- TABELA: receivable_installments
-- Parcelas de contas a receber
-- =====================================================

CREATE TABLE IF NOT EXISTS receivable_installments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Relacionamento
    receivable_id INT NOT NULL COMMENT 'FK para accounts_receivable',
    
    -- Dados da Parcela
    installment_number INT NOT NULL COMMENT 'Número da parcela (1, 2, 3...)',
    total_installments INT NOT NULL COMMENT 'Total de parcelas',
    
    -- Valores
    original_amount DECIMAL(10,2) NOT NULL COMMENT 'Valor original da parcela',
    fees_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT 'Valor das taxas',
    net_amount DECIMAL(10,2) NOT NULL COMMENT 'Valor líquido (original - taxas)',
    paid_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT 'Valor pago',
    
    -- Datas
    due_date DATE NOT NULL COMMENT 'Data de vencimento',
    payment_date DATE NULL COMMENT 'Data do pagamento',
    
    -- Status
    status ENUM('pending', 'paid', 'overdue', 'cancelled') NOT NULL DEFAULT 'pending',
    
    -- Auditoria
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Índices
    INDEX idx_receivable (receivable_id),
    INDEX idx_due_date (due_date),
    INDEX idx_status (status),
    
    -- Foreign Keys
    FOREIGN KEY (receivable_id) REFERENCES accounts_receivable(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- VIEW: Resumo de Formas de Pagamento
-- =====================================================

CREATE OR REPLACE VIEW vw_payment_methods_summary AS
SELECT 
    pmc.id,
    pmc.name,
    pmc.code,
    pmc.financial_behavior,
    CASE 
        WHEN pmc.financial_behavior = 'cash_flow' THEN 'Apenas Fluxo de Caixa'
        WHEN pmc.financial_behavior = 'receivable' THEN 'Apenas Contas a Receber'
        ELSE 'Ambos'
    END as comportamento_descricao,
    CONCAT('D+', pmc.days_to_receive) as prazo_recebimento,
    CONCAT(pmc.operator_fee_percent, '%') as taxa_operadora,
    ba.name as conta_bancaria,
    CASE 
        WHEN pmc.allow_installments THEN CONCAT('Sim (até ', pmc.max_installments, 'x)')
        ELSE 'Não'
    END as permite_parcelamento,
    pmc.active as ativo
FROM payment_methods_config pmc
LEFT JOIN bank_accounts ba ON pmc.bank_account_id = ba.id
ORDER BY pmc.name;

-- =====================================================
-- VERIFICAÇÃO
-- =====================================================

SELECT 'Sistema de configuração criado com sucesso!' AS resultado;

-- Ver configurações inseridas
SELECT * FROM vw_payment_methods_summary;

-- Ver estrutura
DESCRIBE payment_methods_config;
DESCRIBE receivable_installments;
