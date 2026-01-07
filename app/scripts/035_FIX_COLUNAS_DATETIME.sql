-- ============================================================
-- FIX: Alterar colunas para DATETIME e popular dados de teste
-- ============================================================

USE supplychain;

-- 1. Alterar colunas para DATETIME (se forem DATE)
ALTER TABLE ordens_producao 
MODIFY COLUMN data_inicio_producao DATETIME NULL,
MODIFY COLUMN data_prevista DATETIME NULL;

-- 2. Popular dados de teste
UPDATE ordens_producao 
SET 
    data_inicio_producao = CASE 
        WHEN MOD(id, 5) = 0 THEN DATE_SUB(NOW(), INTERVAL 2 DAY)
        WHEN MOD(id, 5) = 1 THEN DATE_SUB(NOW(), INTERVAL 1 DAY)
        WHEN MOD(id, 5) = 2 THEN NOW()
        WHEN MOD(id, 5) = 3 THEN DATE_ADD(NOW(), INTERVAL 1 DAY)
        ELSE CONCAT(CURDATE(), ' 07:00:00')
    END,
    data_prevista = CASE 
        WHEN MOD(id, 5) = 0 THEN DATE_SUB(NOW(), INTERVAL 6 HOUR)
        WHEN MOD(id, 5) = 1 THEN DATE_ADD(NOW(), INTERVAL 1 DAY)
        WHEN MOD(id, 5) = 2 THEN DATE_ADD(NOW(), INTERVAL 2 DAY)
        WHEN MOD(id, 5) = 3 THEN DATE_ADD(NOW(), INTERVAL 4 DAY)
        ELSE CONCAT(CURDATE(), ' 18:00:00')
    END
WHERE status IN ('pendente', 'em_producao');

-- 3. Verificar
SELECT 
    numero_op, 
    status,
    data_inicio_producao as inicio,
    data_prevista as prevista
FROM ordens_producao 
WHERE status IN ('pendente', 'em_producao')
LIMIT 10;
