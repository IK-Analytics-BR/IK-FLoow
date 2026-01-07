-- ============================================================
-- SCRIPT: Popular datas de teste para Timeline do Dashboard
-- Data: 26/12/2025
-- Objetivo: Inserir datas de inicio e previsao nas OPs para testar o Gantt
-- ============================================================

USE supplychain;

-- Verificar OPs existentes
SELECT id, numero_op, status, data_inicio_producao, data_prevista, created_at 
FROM ordens_producao 
WHERE status IN ('pendente', 'em_producao')
LIMIT 10;

-- ============================================================
-- ATUALIZAR OPs COM DATAS DE TESTE
-- ============================================================

-- OP 1: Iniciou ontem, termina amanha (em andamento)
UPDATE ordens_producao 
SET data_inicio_producao = DATE_SUB(NOW(), INTERVAL 1 DAY),
    data_prevista = DATE_ADD(NOW(), INTERVAL 1 DAY),
    status = 'em_producao'
WHERE id = (SELECT id FROM (SELECT id FROM ordens_producao WHERE status IN ('pendente', 'em_producao') ORDER BY id LIMIT 1) t);

-- OP 2: Iniciou hoje cedo, termina hoje a noite (urgente)
UPDATE ordens_producao 
SET data_inicio_producao = DATE_FORMAT(NOW(), '%Y-%m-%d 07:00:00'),
    data_prevista = DATE_FORMAT(NOW(), '%Y-%m-%d 18:00:00'),
    status = 'em_producao'
WHERE id = (SELECT id FROM (SELECT id FROM ordens_producao WHERE status IN ('pendente', 'em_producao') ORDER BY id LIMIT 1 OFFSET 1) t);

-- OP 3: Iniciou anteontem, deveria ter terminado ontem (ATRASADA)
UPDATE ordens_producao 
SET data_inicio_producao = DATE_SUB(NOW(), INTERVAL 2 DAY),
    data_prevista = DATE_SUB(NOW(), INTERVAL 1 DAY),
    status = 'em_producao'
WHERE id = (SELECT id FROM (SELECT id FROM ordens_producao WHERE status IN ('pendente', 'em_producao') ORDER BY id LIMIT 1 OFFSET 2) t);

-- OP 4: Comeca amanha, termina em 3 dias (planejada)
UPDATE ordens_producao 
SET data_inicio_producao = DATE_ADD(NOW(), INTERVAL 1 DAY),
    data_prevista = DATE_ADD(NOW(), INTERVAL 3 DAY),
    status = 'pendente'
WHERE id = (SELECT id FROM (SELECT id FROM ordens_producao WHERE status IN ('pendente', 'em_producao') ORDER BY id LIMIT 1 OFFSET 3) t);

-- OP 5: Iniciou hoje, termina em 2 dias (normal)
UPDATE ordens_producao 
SET data_inicio_producao = NOW(),
    data_prevista = DATE_ADD(NOW(), INTERVAL 2 DAY),
    status = 'em_producao'
WHERE id = (SELECT id FROM (SELECT id FROM ordens_producao WHERE status IN ('pendente', 'em_producao') ORDER BY id LIMIT 1 OFFSET 4) t);

-- ============================================================
-- OU USAR UPDATE MAIS SIMPLES (TODAS AS OPs DE UMA VEZ)
-- ============================================================

-- Atualizar TODAS as OPs pendentes/em_producao com datas de teste variadas
UPDATE ordens_producao op
JOIN (
    SELECT id, 
           @row := @row + 1 as rn,
           CASE 
               WHEN @row % 5 = 1 THEN DATE_SUB(NOW(), INTERVAL 1 DAY)  -- Ontem
               WHEN @row % 5 = 2 THEN DATE_FORMAT(NOW(), '%Y-%m-%d 07:00:00')  -- Hoje 7h
               WHEN @row % 5 = 3 THEN DATE_SUB(NOW(), INTERVAL 2 DAY)  -- Anteontem (atrasada)
               WHEN @row % 5 = 4 THEN DATE_ADD(NOW(), INTERVAL 1 DAY)  -- Amanha
               ELSE NOW()  -- Agora
           END as dt_inicio,
           CASE 
               WHEN @row % 5 = 1 THEN DATE_ADD(NOW(), INTERVAL 1 DAY)  -- Amanha
               WHEN @row % 5 = 2 THEN DATE_FORMAT(NOW(), '%Y-%m-%d 18:00:00')  -- Hoje 18h
               WHEN @row % 5 = 3 THEN DATE_SUB(NOW(), INTERVAL 6 HOUR)  -- Atrasada
               WHEN @row % 5 = 4 THEN DATE_ADD(NOW(), INTERVAL 3 DAY)  -- +3 dias
               ELSE DATE_ADD(NOW(), INTERVAL 2 DAY)  -- +2 dias
           END as dt_prevista,
           CASE 
               WHEN @row % 5 = 4 THEN 'pendente'
               ELSE 'em_producao'
           END as novo_status
    FROM ordens_producao, (SELECT @row := 0) r
    WHERE status IN ('pendente', 'em_producao')
) dados ON op.id = dados.id
SET op.data_inicio_producao = dados.dt_inicio,
    op.data_prevista = dados.dt_prevista,
    op.status = dados.novo_status;

-- ============================================================
-- VERIFICAR RESULTADO
-- ============================================================
SELECT 
    id, 
    numero_op, 
    status,
    DATE_FORMAT(data_inicio_producao, '%d/%m %H:%i') as inicio,
    DATE_FORMAT(data_prevista, '%d/%m %H:%i') as prevista,
    CASE 
        WHEN data_prevista < NOW() THEN 'ATRASADO'
        WHEN TIMESTAMPDIFF(HOUR, NOW(), data_prevista) < 8 THEN 'ATENCAO'
        ELSE 'OK'
    END as situacao
FROM ordens_producao 
WHERE status IN ('pendente', 'em_producao')
ORDER BY data_prevista;

SELECT '✅ Datas de teste populadas com sucesso!' as resultado;
