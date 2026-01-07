-- =====================================================
-- LIMPAR DUPLICIDADES EM OP_LOTES
-- Script: 030_LIMPAR_DUPLICIDADES_LOTES.sql
-- Data: 24/12/2024
-- =====================================================

USE supply_chain_system;

-- 1. DIAGNÓSTICO: Ver lotes da OP-2025-0016
SELECT 
    l.id AS lote_id,
    l.sequencia,
    l.quantidade,
    l.status_operador,
    l.etapa_atual_id,
    e.nome AS etapa_nome,
    l.operador_id,
    l.operador_designado_id,
    l.created_at,
    op.numero_op
FROM op_lotes l
INNER JOIN ordens_producao op ON op.id = l.ordem_producao_id
LEFT JOIN producao_etapas e ON e.id = l.etapa_atual_id
WHERE op.numero_op = 'OP-2025-0016'
ORDER BY l.sequencia, l.created_at;

-- 2. DIAGNÓSTICO: Ver todas as OPs com mais de 1 lote (possíveis duplicidades)
SELECT 
    op.numero_op,
    COUNT(l.id) AS total_lotes,
    SUM(l.quantidade) AS soma_quantidades,
    op.quantidade AS quantidade_op
FROM op_lotes l
INNER JOIN ordens_producao op ON op.id = l.ordem_producao_id
GROUP BY op.id, op.numero_op, op.quantidade
HAVING COUNT(l.id) > 1
ORDER BY op.numero_op;

-- =====================================================
-- 3. LIMPEZA: Manter apenas 1 lote por OP (o mais antigo)
-- =====================================================

SET SQL_SAFE_UPDATES = 0;

-- Deletar lotes duplicados, mantendo o de menor ID (mais antigo)
DELETE l1 FROM op_lotes l1
INNER JOIN op_lotes l2 
ON l1.ordem_producao_id = l2.ordem_producao_id 
   AND l1.id > l2.id
   AND l1.sequencia = l2.sequencia;

-- OU: Deletar TODOS os lotes exceto o primeiro de cada OP
-- (descomente se precisar de limpeza mais agressiva)
/*
DELETE FROM op_lotes 
WHERE id NOT IN (
    SELECT * FROM (
        SELECT MIN(id) 
        FROM op_lotes 
        GROUP BY ordem_producao_id
    ) AS t
);
*/

SET SQL_SAFE_UPDATES = 1;

-- 4. VERIFICAR RESULTADO
SELECT 
    op.numero_op,
    COUNT(l.id) AS total_lotes,
    SUM(l.quantidade) AS soma_quantidades
FROM op_lotes l
INNER JOIN ordens_producao op ON op.id = l.ordem_producao_id
GROUP BY op.id, op.numero_op
ORDER BY op.numero_op;

-- 5. RESETAR campos de operador nos lotes restantes
SET SQL_SAFE_UPDATES = 0;

UPDATE op_lotes
SET 
    operador_id = NULL,
    operador_designado_id = NULL,
    status_operador = NULL,
    data_inicio_operador = NULL,
    data_fim_operador = NULL,
    arara = NULL
WHERE id > 0;

SET SQL_SAFE_UPDATES = 1;

SELECT 'Limpeza concluída!' AS status;
