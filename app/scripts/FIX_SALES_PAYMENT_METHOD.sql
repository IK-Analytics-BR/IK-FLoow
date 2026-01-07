-- =====================================================
-- CORREÇÃO: Coluna payment_method na tabela sales
-- =====================================================
-- Problema: ENUM antigo não aceita novos códigos
-- Solução: Mudar para VARCHAR(50)
-- =====================================================

USE supply_chain_system;

-- Desabilitar safe update mode temporariamente
SET SQL_SAFE_UPDATES = 0;

-- 1. Ver estrutura atual
DESCRIBE sales;

-- 2. Alterar coluna payment_method de ENUM para VARCHAR
ALTER TABLE sales 
MODIFY COLUMN payment_method VARCHAR(50) NULL;

-- 3. Atualizar valores antigos para novos códigos (se houver)
UPDATE sales SET payment_method = 'cash' WHERE payment_method = 'money';
UPDATE sales SET payment_method = 'credit_card' WHERE payment_method = 'credit';
UPDATE sales SET payment_method = 'debit_card' WHERE payment_method = 'debit';
-- PIX e boleto já estão corretos

-- 4. Verificar
SELECT 
    payment_method, 
    COUNT(*) as total 
FROM sales 
GROUP BY payment_method
ORDER BY total DESC;

-- Reabilitar safe update mode
SET SQL_SAFE_UPDATES = 1;

SELECT 'Coluna payment_method corrigida com sucesso!' AS resultado;
