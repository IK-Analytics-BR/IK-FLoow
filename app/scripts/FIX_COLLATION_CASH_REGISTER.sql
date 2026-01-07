-- =====================================================
-- CORREÇÃO: Collation da tabela cash_register
-- =====================================================
-- Problema: utf8mb4_unicode_ci vs utf8mb4_0900_ai_ci
-- Solução: Alterar para utf8mb4_0900_ai_ci (padrão MySQL 8)
-- =====================================================

USE supply_chain_system;

-- Verificar collation atual
SELECT 
    TABLE_NAME,
    TABLE_COLLATION
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'supply_chain_system'
AND TABLE_NAME IN ('cash_register', 'sales', 'payment_methods_config', 'customers');

-- Alterar collation da tabela cash_register
ALTER TABLE cash_register 
CONVERT TO CHARACTER SET utf8mb4 
COLLATE utf8mb4_0900_ai_ci;

-- Verificar novamente
SELECT 
    TABLE_NAME,
    TABLE_COLLATION
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'supply_chain_system'
AND TABLE_NAME = 'cash_register';

SELECT 'Collation corrigida com sucesso!' AS resultado;
