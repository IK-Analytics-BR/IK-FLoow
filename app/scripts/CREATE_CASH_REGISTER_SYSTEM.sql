-- =====================================================
-- COPIE ESTE SQL E EXECUTE NO MYSQL WORKBENCH!
-- =====================================================

USE supply_chain_system;

-- 1. CORRIGIR COLLATION DA TABELA cash_register
ALTER TABLE cash_register 
CONVERT TO CHARACTER SET utf8mb4 
COLLATE utf8mb4_0900_ai_ci;

-- 2. VERIFICAR SE CORRIGIU
SELECT 
    TABLE_NAME,
    TABLE_COLLATION
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'supply_chain_system'
AND TABLE_NAME = 'cash_register';

-- 3. RESULTADO ESPERADO: utf8mb4_0900_ai_ci

SELECT '✅ COLLATION CORRIGIDA COM SUCESSO!' AS resultado;
