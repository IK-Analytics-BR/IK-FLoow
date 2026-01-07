-- =====================================================
-- ATUALIZAR OPs EXISTENTES PARA APARECER NO PAINEL DO LÍDER
-- Script: 029_UPDATE_OPS_EXISTENTES_PARA_LIDER.sql
-- Data: 24/12/2024
-- Descrição: Reseta os campos de operador para que os lotes
--            apareçam em "Sem Atribuição" no painel do líder
-- =====================================================

USE supply_chain_system;

-- Verificar situação atual
SELECT 
    'ANTES' AS momento,
    COUNT(*) AS total_lotes,
    COUNT(CASE WHEN operador_id IS NOT NULL THEN 1 END) AS com_operador,
    COUNT(CASE WHEN operador_designado_id IS NOT NULL THEN 1 END) AS com_operador_designado,
    COUNT(CASE WHEN status_operador IS NOT NULL THEN 1 END) AS com_status_operador,
    COUNT(CASE WHEN status_operador IS NULL AND operador_id IS NULL THEN 1 END) AS sem_atribuicao
FROM op_lotes;

-- =====================================================
-- OPÇÃO 1: RESETAR TODOS OS LOTES (recomeçar do zero)
-- Use esta opção se quiser que TODOS os lotes voltem
-- para "Sem Atribuição" no painel do líder
-- =====================================================

-- Desabilitar safe mode temporariamente
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

-- Reabilitar safe mode
SET SQL_SAFE_UPDATES = 1;

-- =====================================================
-- OPÇÃO 2: RESETAR APENAS LOTES QUE NÃO FORAM TRABALHADOS
-- (Comentado - descomente se preferir esta opção)
-- =====================================================

/*
UPDATE op_lotes
SET 
    operador_id = NULL,
    operador_designado_id = NULL,
    status_operador = NULL
WHERE status_operador IS NULL 
   OR status_operador NOT IN ('em_producao', 'despachado');
*/

-- Verificar situação após
SELECT 
    'DEPOIS' AS momento,
    COUNT(*) AS total_lotes,
    COUNT(CASE WHEN operador_id IS NOT NULL THEN 1 END) AS com_operador,
    COUNT(CASE WHEN operador_designado_id IS NOT NULL THEN 1 END) AS com_operador_designado,
    COUNT(CASE WHEN status_operador IS NOT NULL THEN 1 END) AS com_status_operador,
    COUNT(CASE WHEN status_operador IS NULL AND operador_id IS NULL THEN 1 END) AS sem_atribuicao
FROM op_lotes;

-- Verificar lotes por etapa
SELECT 
    e.nome AS etapa,
    COUNT(l.id) AS total_lotes,
    COALESCE(l.status_operador, 'sem_atribuicao') AS status
FROM op_lotes l
LEFT JOIN producao_etapas e ON e.id = l.etapa_atual_id
GROUP BY e.nome, l.status_operador
ORDER BY e.nome, status;

-- Verificar quais etapas cada líder controla
SELECT 
    u.name AS lider,
    GROUP_CONCAT(e.nome ORDER BY e.ordem SEPARATOR ', ') AS etapas
FROM lider_etapas le
JOIN users u ON u.id = le.lider_id
JOIN producao_etapas e ON e.id = le.etapa_id
GROUP BY u.name;

-- Verificar quais operadores cada líder tem
SELECT 
    ul.name AS lider,
    GROUP_CONCAT(uo.name ORDER BY uo.name SEPARATOR ', ') AS operadores
FROM lider_operadores lo
JOIN users ul ON ul.id = lo.lider_id
JOIN users uo ON uo.id = lo.operador_id
GROUP BY ul.name;

SELECT 'Script executado com sucesso! Lotes resetados para Sem Atribuição.' AS status;
