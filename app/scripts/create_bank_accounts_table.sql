-- Script para criar apenas a tabela bank_accounts
-- Autor: Sistema de Gestão de Suprimentos
-- Data: 2025-09-08

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

-- Inserir uma conta bancária padrão para teste
INSERT INTO bank_accounts (name, agency, account_number, pix_key, cost_center, status, active)
VALUES ('Conta Principal', '0001', '12345-6', 'exemplo@pix.com', 'Administrativo', 'active', TRUE);
