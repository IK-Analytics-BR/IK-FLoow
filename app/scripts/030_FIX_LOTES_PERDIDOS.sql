-- =====================================================
-- Script para corrigir lotes perdidos
-- OP-2025-0014: Perdeu 3 unidades (Lote 39 deletado)
-- OP-2025-0008: Perdeu 3 unidades (lotes deletados)
-- =====================================================

-- =====================================================
-- 1. VERIFICAR ESTADO ATUAL
-- =====================================================
SELECT '=== ANTES DA CORREÇÃO ===' AS info;

SELECT 'OP-2025-0014' AS op, SUM(quantidade) AS soma_atual, 10 AS esperado, 
       10 - SUM(quantidade) AS faltando
FROM op_lotes WHERE ordem_producao_id = 14;

SELECT 'OP-2025-0008' AS op, SUM(quantidade) AS soma_atual, 10 AS esperado,
       10 - SUM(quantidade) AS faltando
FROM op_lotes WHERE ordem_producao_id = 8;

-- =====================================================
-- 2. CORRIGIR OP-2025-0014 (ID=14) - Faltam 3 unidades
-- =====================================================
-- Buscar próxima sequência disponível
SET @seq14 = (SELECT COALESCE(MAX(sequencia), 0) + 1 FROM op_lotes WHERE ordem_producao_id = 14);

INSERT INTO op_lotes (
    ordem_producao_id, sequencia, quantidade, etapa_atual_id,
    status_operador, status, align_side, created_at
) VALUES (
    14, @seq14, 3.0000, 8, NULL, 'pendente', 'full', NOW()
);

SET @lote14 = LAST_INSERT_ID();

-- Registrar no log
INSERT INTO op_lotes_etapas_log (
    lote_id, ordem_producao_id, quantidade_movida, 
    etapa_anterior_id, etapa_nova_id, status_anterior, status_novo,
    usuario_id, observacao, created_at
) VALUES (
    @lote14, 14, 3.0000, NULL, 8, NULL, 'criado',
    1, 'Lote recriado - correção de dados perdidos durante testes', NOW()
);

-- =====================================================
-- 3. CORRIGIR OP-2025-0008 (ID=8) - Faltam 3 unidades
-- =====================================================
-- Buscar próxima sequência disponível
SET @seq8 = (SELECT COALESCE(MAX(sequencia), 0) + 1 FROM op_lotes WHERE ordem_producao_id = 8);

INSERT INTO op_lotes (
    ordem_producao_id, sequencia, quantidade, etapa_atual_id,
    status_operador, status, align_side, created_at
) VALUES (
    8, @seq8, 3.0000, 8, NULL, 'pendente', 'full', NOW()
);

SET @lote8 = LAST_INSERT_ID();

-- Registrar no log
INSERT INTO op_lotes_etapas_log (
    lote_id, ordem_producao_id, quantidade_movida, 
    etapa_anterior_id, etapa_nova_id, status_anterior, status_novo,
    usuario_id, observacao, created_at
) VALUES (
    @lote8, 8, 3.0000, NULL, 8, NULL, 'criado',
    1, 'Lote recriado - correção de dados perdidos durante testes', NOW()
);

-- =====================================================
-- 4. VERIFICAR ESTADO APÓS CORREÇÃO
-- =====================================================
SELECT '=== DEPOIS DA CORREÇÃO ===' AS info;

SELECT 'OP-2025-0014' AS op, SUM(quantidade) AS soma_corrigida, 10 AS esperado,
       CASE WHEN SUM(quantidade) = 10 THEN 'OK' ELSE 'ERRO' END AS status
FROM op_lotes WHERE ordem_producao_id = 14;

SELECT 'OP-2025-0008' AS op, SUM(quantidade) AS soma_corrigida, 10 AS esperado,
       CASE WHEN SUM(quantidade) = 10 THEN 'OK' ELSE 'ERRO' END AS status
FROM op_lotes WHERE ordem_producao_id = 8;

-- Listar todos os lotes corrigidos
SELECT 'LOTES OP-2025-0014' AS info;
SELECT id, sequencia, quantidade, etapa_atual_id, status_operador 
FROM op_lotes WHERE ordem_producao_id = 14 ORDER BY id;

SELECT 'LOTES OP-2025-0008' AS info;
SELECT id, sequencia, quantidade, etapa_atual_id, status_operador 
FROM op_lotes WHERE ordem_producao_id = 8 ORDER BY id;
