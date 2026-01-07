-- =====================================================
-- SCRIPT 045: TESTE COMPLETO FICHA TÉCNICA COM HISTÓRICO
-- Data: 2025-12-26
-- Descrição: Cria cenário completo de teste para validar
--            histórico de produção na ficha técnica
-- =====================================================

USE supply_chain_system;

-- =====================================================
-- PASSO 1: CRIAR TEMPLATE (FICHA TÉCNICA) PARA PRODUTO ID 1
-- =====================================================

-- Verificar se já existe template para produto 1
SET @template_existente = (SELECT id FROM produto_templates_producao WHERE produto_id = 1 LIMIT 1);

INSERT INTO produto_templates_producao (produto_id, nome_template, versao, tempo_producao_horas, custo_total_base, ativo, created_at)
SELECT 1, 'Template Correia 600 H 200 DZ', 1, 12.0, 1500.00, 1, NOW()
WHERE @template_existente IS NULL;

SET @template_id = COALESCE(@template_existente, LAST_INSERT_ID());
SELECT CONCAT('Template ID: ', @template_id) AS info;

-- Inserir itens do template (serviço de mão de obra)
INSERT INTO produto_template_itens (template_id, tipo_item, produto_id, descricao, quantidade, unidade_medida, custo_unitario_base, custo_total_base)
SELECT @template_id, 'servico', NULL, 'SERVIÇO - MÃO DE OBRA PRODUÇÃO', 12.0, 'HR', 80.00, 960.00
WHERE NOT EXISTS (SELECT 1 FROM produto_template_itens WHERE template_id = @template_id AND tipo_item = 'servico');

-- =====================================================
-- PASSO 2: CRIAR 10 ORÇAMENTOS
-- =====================================================

-- Obter próximo número de orçamento
SET @ultimo_orc = (SELECT COALESCE(MAX(CAST(SUBSTRING(numero, 5) AS UNSIGNED)), 0) FROM orcamentos WHERE numero LIKE 'ORC-%');

-- Criar orçamentos
INSERT INTO orcamentos (numero, empresa_id, cliente_id, data_orcamento, data_validade, status, valor_total, observacoes, created_at)
VALUES 
    (CONCAT('ORC-', LPAD(@ultimo_orc + 1, 6, '0')), 1, 1, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY), 'aprovado', 5000.00, 'Orçamento teste ficha técnica 1', NOW()),
    (CONCAT('ORC-', LPAD(@ultimo_orc + 2, 6, '0')), 1, 1, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY), 'aprovado', 5500.00, 'Orçamento teste ficha técnica 2', NOW()),
    (CONCAT('ORC-', LPAD(@ultimo_orc + 3, 6, '0')), 1, 1, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY), 'aprovado', 4800.00, 'Orçamento teste ficha técnica 3', NOW()),
    (CONCAT('ORC-', LPAD(@ultimo_orc + 4, 6, '0')), 1, 1, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY), 'aprovado', 5200.00, 'Orçamento teste ficha técnica 4', NOW()),
    (CONCAT('ORC-', LPAD(@ultimo_orc + 5, 6, '0')), 1, 1, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY), 'aprovado', 4900.00, 'Orçamento teste ficha técnica 5', NOW()),
    (CONCAT('ORC-', LPAD(@ultimo_orc + 6, 6, '0')), 1, 1, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY), 'aprovado', 5100.00, 'Orçamento teste ficha técnica 6', NOW()),
    (CONCAT('ORC-', LPAD(@ultimo_orc + 7, 6, '0')), 1, 1, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY), 'aprovado', 5300.00, 'Orçamento teste ficha técnica 7', NOW()),
    (CONCAT('ORC-', LPAD(@ultimo_orc + 8, 6, '0')), 1, 1, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY), 'aprovado', 4700.00, 'Orçamento teste ficha técnica 8', NOW()),
    (CONCAT('ORC-', LPAD(@ultimo_orc + 9, 6, '0')), 1, 1, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY), 'aprovado', 5400.00, 'Orçamento teste ficha técnica 9', NOW()),
    (CONCAT('ORC-', LPAD(@ultimo_orc + 10, 6, '0')), 1, 1, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY), 'aprovado', 5600.00, 'Orçamento teste ficha técnica 10', NOW());

-- Guardar IDs dos orçamentos criados
SET @orc1 = (SELECT id FROM orcamentos WHERE numero = CONCAT('ORC-', LPAD(@ultimo_orc + 1, 6, '0')));
SET @orc2 = (SELECT id FROM orcamentos WHERE numero = CONCAT('ORC-', LPAD(@ultimo_orc + 2, 6, '0')));
SET @orc3 = (SELECT id FROM orcamentos WHERE numero = CONCAT('ORC-', LPAD(@ultimo_orc + 3, 6, '0')));
SET @orc4 = (SELECT id FROM orcamentos WHERE numero = CONCAT('ORC-', LPAD(@ultimo_orc + 4, 6, '0')));
SET @orc5 = (SELECT id FROM orcamentos WHERE numero = CONCAT('ORC-', LPAD(@ultimo_orc + 5, 6, '0')));
SET @orc6 = (SELECT id FROM orcamentos WHERE numero = CONCAT('ORC-', LPAD(@ultimo_orc + 6, 6, '0')));
SET @orc7 = (SELECT id FROM orcamentos WHERE numero = CONCAT('ORC-', LPAD(@ultimo_orc + 7, 6, '0')));
SET @orc8 = (SELECT id FROM orcamentos WHERE numero = CONCAT('ORC-', LPAD(@ultimo_orc + 8, 6, '0')));
SET @orc9 = (SELECT id FROM orcamentos WHERE numero = CONCAT('ORC-', LPAD(@ultimo_orc + 9, 6, '0')));
SET @orc10 = (SELECT id FROM orcamentos WHERE numero = CONCAT('ORC-', LPAD(@ultimo_orc + 10, 6, '0')));

SELECT 'Orçamentos criados:' AS info;
SELECT @orc1, @orc2, @orc3, @orc4, @orc5, @orc6, @orc7, @orc8, @orc9, @orc10;

-- Inserir itens nos orçamentos (produto ID 1, quantidades variadas)
INSERT INTO orcamento_itens (orcamento_id, produto_id, quantidade, preco_unitario, subtotal, created_at)
VALUES
    (@orc1, 1, 5, 1000.00, 5000.00, NOW()),
    (@orc2, 1, 8, 687.50, 5500.00, NOW()),
    (@orc3, 1, 4, 1200.00, 4800.00, NOW()),
    (@orc4, 1, 6, 866.67, 5200.00, NOW()),
    (@orc5, 1, 7, 700.00, 4900.00, NOW()),
    (@orc6, 1, 5, 1020.00, 5100.00, NOW()),
    (@orc7, 1, 10, 530.00, 5300.00, NOW()),
    (@orc8, 1, 3, 1566.67, 4700.00, NOW()),
    (@orc9, 1, 9, 600.00, 5400.00, NOW()),
    (@orc10, 1, 12, 466.67, 5600.00, NOW());

-- =====================================================
-- PASSO 3: CRIAR OPs PARA OS ORÇAMENTOS
-- =====================================================

SET @ultima_op = (SELECT COALESCE(MAX(CAST(SUBSTRING(numero_op, 9) AS UNSIGNED)), 0) FROM ordens_producao WHERE numero_op LIKE 'OP-2025-%');

-- Criar OPs com status concluida e datas variadas
INSERT INTO ordens_producao (numero_op, empresa_id, cliente_id, produto_id, quantidade, status, data_solicitacao, data_prevista, data_inicio_producao, data_conclusao, orcamento_id, created_at)
VALUES
    (CONCAT('OP-2025-', LPAD(@ultima_op + 1, 4, '0')), 1, 1, 1, 5, 'concluida', '2025-12-01', '2025-12-05', '2025-12-01 08:00:00', '2025-12-02', @orc1, NOW()),
    (CONCAT('OP-2025-', LPAD(@ultima_op + 2, 4, '0')), 1, 1, 1, 8, 'concluida', '2025-12-03', '2025-12-08', '2025-12-03 07:30:00', '2025-12-05', @orc2, NOW()),
    (CONCAT('OP-2025-', LPAD(@ultima_op + 3, 4, '0')), 1, 1, 1, 4, 'concluida', '2025-12-05', '2025-12-09', '2025-12-05 09:00:00', '2025-12-06', @orc3, NOW()),
    (CONCAT('OP-2025-', LPAD(@ultima_op + 4, 4, '0')), 1, 1, 1, 6, 'concluida', '2025-12-07', '2025-12-12', '2025-12-07 08:30:00', '2025-12-09', @orc4, NOW()),
    (CONCAT('OP-2025-', LPAD(@ultima_op + 5, 4, '0')), 1, 1, 1, 7, 'concluida', '2025-12-09', '2025-12-14', '2025-12-09 07:00:00', '2025-12-11', @orc5, NOW()),
    (CONCAT('OP-2025-', LPAD(@ultima_op + 6, 4, '0')), 1, 1, 1, 5, 'concluida', '2025-12-11', '2025-12-16', '2025-12-11 08:00:00', '2025-12-12', @orc6, NOW()),
    (CONCAT('OP-2025-', LPAD(@ultima_op + 7, 4, '0')), 1, 1, 1, 10, 'concluida', '2025-12-13', '2025-12-19', '2025-12-13 07:30:00', '2025-12-16', @orc7, NOW()),
    (CONCAT('OP-2025-', LPAD(@ultima_op + 8, 4, '0')), 1, 1, 1, 3, 'concluida', '2025-12-15', '2025-12-18', '2025-12-15 09:30:00', '2025-12-16', @orc8, NOW()),
    (CONCAT('OP-2025-', LPAD(@ultima_op + 9, 4, '0')), 1, 1, 1, 9, 'concluida', '2025-12-17', '2025-12-23', '2025-12-17 08:00:00', '2025-12-20', @orc9, NOW()),
    (CONCAT('OP-2025-', LPAD(@ultima_op + 10, 4, '0')), 1, 1, 1, 12, 'concluida', '2025-12-19', '2025-12-26', '2025-12-19 07:00:00', '2025-12-23', @orc10, NOW());

-- Guardar IDs das OPs criadas
SET @op1 = (SELECT id FROM ordens_producao WHERE numero_op = CONCAT('OP-2025-', LPAD(@ultima_op + 1, 4, '0')));
SET @op2 = (SELECT id FROM ordens_producao WHERE numero_op = CONCAT('OP-2025-', LPAD(@ultima_op + 2, 4, '0')));
SET @op3 = (SELECT id FROM ordens_producao WHERE numero_op = CONCAT('OP-2025-', LPAD(@ultima_op + 3, 4, '0')));
SET @op4 = (SELECT id FROM ordens_producao WHERE numero_op = CONCAT('OP-2025-', LPAD(@ultima_op + 4, 4, '0')));
SET @op5 = (SELECT id FROM ordens_producao WHERE numero_op = CONCAT('OP-2025-', LPAD(@ultima_op + 5, 4, '0')));
SET @op6 = (SELECT id FROM ordens_producao WHERE numero_op = CONCAT('OP-2025-', LPAD(@ultima_op + 6, 4, '0')));
SET @op7 = (SELECT id FROM ordens_producao WHERE numero_op = CONCAT('OP-2025-', LPAD(@ultima_op + 7, 4, '0')));
SET @op8 = (SELECT id FROM ordens_producao WHERE numero_op = CONCAT('OP-2025-', LPAD(@ultima_op + 8, 4, '0')));
SET @op9 = (SELECT id FROM ordens_producao WHERE numero_op = CONCAT('OP-2025-', LPAD(@ultima_op + 9, 4, '0')));
SET @op10 = (SELECT id FROM ordens_producao WHERE numero_op = CONCAT('OP-2025-', LPAD(@ultima_op + 10, 4, '0')));

SELECT 'OPs criadas:' AS info;
SELECT @op1, @op2, @op3, @op4, @op5, @op6, @op7, @op8, @op9, @op10;

-- =====================================================
-- PASSO 4: CRIAR LOTES PARA CADA OP
-- =====================================================

INSERT INTO op_lotes (ordem_producao_id, numero_lote, quantidade, etapa_atual_id, status, status_operador, data_fim_operador, created_at)
VALUES
    (@op1, 'LOTE-001', 5, 22, 'concluido', 'despachado', '2025-12-02 16:00:00', NOW()),
    (@op2, 'LOTE-001', 8, 22, 'concluido', 'despachado', '2025-12-05 17:30:00', NOW()),
    (@op3, 'LOTE-001', 4, 22, 'concluido', 'despachado', '2025-12-06 15:00:00', NOW()),
    (@op4, 'LOTE-001', 6, 22, 'concluido', 'despachado', '2025-12-09 16:30:00', NOW()),
    (@op5, 'LOTE-001', 7, 22, 'concluido', 'despachado', '2025-12-11 18:00:00', NOW()),
    (@op6, 'LOTE-001', 5, 22, 'concluido', 'despachado', '2025-12-12 14:30:00', NOW()),
    (@op7, 'LOTE-001', 10, 22, 'concluido', 'despachado', '2025-12-16 17:00:00', NOW()),
    (@op8, 'LOTE-001', 3, 22, 'concluido', 'despachado', '2025-12-16 12:00:00', NOW()),
    (@op9, 'LOTE-001', 9, 22, 'concluido', 'despachado', '2025-12-20 16:00:00', NOW()),
    (@op10, 'LOTE-001', 12, 22, 'concluido', 'despachado', '2025-12-23 18:30:00', NOW());

-- Guardar IDs dos lotes
SET @lote1 = (SELECT id FROM op_lotes WHERE ordem_producao_id = @op1 ORDER BY id DESC LIMIT 1);
SET @lote2 = (SELECT id FROM op_lotes WHERE ordem_producao_id = @op2 ORDER BY id DESC LIMIT 1);
SET @lote3 = (SELECT id FROM op_lotes WHERE ordem_producao_id = @op3 ORDER BY id DESC LIMIT 1);
SET @lote4 = (SELECT id FROM op_lotes WHERE ordem_producao_id = @op4 ORDER BY id DESC LIMIT 1);
SET @lote5 = (SELECT id FROM op_lotes WHERE ordem_producao_id = @op5 ORDER BY id DESC LIMIT 1);
SET @lote6 = (SELECT id FROM op_lotes WHERE ordem_producao_id = @op6 ORDER BY id DESC LIMIT 1);
SET @lote7 = (SELECT id FROM op_lotes WHERE ordem_producao_id = @op7 ORDER BY id DESC LIMIT 1);
SET @lote8 = (SELECT id FROM op_lotes WHERE ordem_producao_id = @op8 ORDER BY id DESC LIMIT 1);
SET @lote9 = (SELECT id FROM op_lotes WHERE ordem_producao_id = @op9 ORDER BY id DESC LIMIT 1);
SET @lote10 = (SELECT id FROM op_lotes WHERE ordem_producao_id = @op10 ORDER BY id DESC LIMIT 1);

SELECT 'Lotes criados:' AS info;
SELECT @lote1, @lote2, @lote3, @lote4, @lote5, @lote6, @lote7, @lote8, @lote9, @lote10;

-- =====================================================
-- PASSO 5: CRIAR HISTÓRICO DE ETAPAS COM TEMPOS VARIADOS
-- Etapas principais: 8-22 (15 etapas de produção)
-- Tempos variados para simular realidade
-- =====================================================

-- LOTE 1 (OP1 - 5 unidades - 32h total = 6.4h/un = 384 min/un)
INSERT INTO op_lotes_etapas_log (lote_id, ordem_producao_id, quantidade_movida, etapa_anterior_id, etapa_nova_id, usuario_id, created_at) VALUES
(@lote1, @op1, 5, NULL, 8, 1, '2025-12-01 08:00:00'),   -- Engenharia: 45 min
(@lote1, @op1, 5, 8, 9, 1, '2025-12-01 08:45:00'),      -- PCP: 30 min
(@lote1, @op1, 5, 9, 10, 1, '2025-12-01 09:15:00'),     -- Separação: 60 min
(@lote1, @op1, 5, 10, 11, 1, '2025-12-01 10:15:00'),    -- Prep Borracha: 90 min
(@lote1, @op1, 5, 11, 12, 1, '2025-12-01 11:45:00'),    -- Prep Lonas: 75 min
(@lote1, @op1, 5, 12, 13, 1, '2025-12-01 13:00:00'),    -- Montagem: 180 min
(@lote1, @op1, 5, 13, 14, 1, '2025-12-01 16:00:00'),    -- Pré-Compactação: 60 min
(@lote1, @op1, 5, 14, 15, 1, '2025-12-01 17:00:00'),    -- Corte: 45 min
(@lote1, @op1, 5, 15, 16, 1, '2025-12-02 08:00:00'),    -- Vulcanização: 240 min
(@lote1, @op1, 5, 16, 17, 1, '2025-12-02 12:00:00'),    -- Resfriamento: 60 min
(@lote1, @op1, 5, 17, 18, 1, '2025-12-02 13:00:00'),    -- Acabamento: 90 min
(@lote1, @op1, 5, 18, 20, 1, '2025-12-02 14:30:00'),    -- Inspeção: 45 min
(@lote1, @op1, 5, 20, 21, 1, '2025-12-02 15:15:00'),    -- Embalagem: 30 min
(@lote1, @op1, 5, 21, 22, 1, '2025-12-02 15:45:00');    -- Expedição

-- LOTE 2 (OP2 - 8 unidades - 58h total = 7.25h/un = 435 min/un)
INSERT INTO op_lotes_etapas_log (lote_id, ordem_producao_id, quantidade_movida, etapa_anterior_id, etapa_nova_id, usuario_id, created_at) VALUES
(@lote2, @op2, 8, NULL, 8, 1, '2025-12-03 07:30:00'),
(@lote2, @op2, 8, 8, 9, 1, '2025-12-03 08:30:00'),      -- 60 min
(@lote2, @op2, 8, 9, 10, 1, '2025-12-03 09:00:00'),     -- 30 min
(@lote2, @op2, 8, 10, 11, 1, '2025-12-03 10:30:00'),    -- 90 min
(@lote2, @op2, 8, 11, 12, 1, '2025-12-03 12:30:00'),    -- 120 min
(@lote2, @op2, 8, 12, 13, 1, '2025-12-03 14:00:00'),    -- 90 min
(@lote2, @op2, 8, 13, 14, 1, '2025-12-03 18:00:00'),    -- 240 min
(@lote2, @op2, 8, 14, 15, 1, '2025-12-04 08:30:00'),    -- 870 min (overnight)
(@lote2, @op2, 8, 15, 16, 1, '2025-12-04 09:30:00'),    -- 60 min
(@lote2, @op2, 8, 16, 17, 1, '2025-12-04 14:30:00'),    -- 300 min
(@lote2, @op2, 8, 17, 18, 1, '2025-12-04 16:00:00'),    -- 90 min
(@lote2, @op2, 8, 18, 20, 1, '2025-12-05 08:00:00'),    -- overnight
(@lote2, @op2, 8, 20, 21, 1, '2025-12-05 09:00:00'),    -- 60 min
(@lote2, @op2, 8, 21, 22, 1, '2025-12-05 09:30:00');    -- 30 min

-- LOTE 3 (OP3 - 4 unidades - 30h total = 7.5h/un = 450 min/un)
INSERT INTO op_lotes_etapas_log (lote_id, ordem_producao_id, quantidade_movida, etapa_anterior_id, etapa_nova_id, usuario_id, created_at) VALUES
(@lote3, @op3, 4, NULL, 8, 1, '2025-12-05 09:00:00'),
(@lote3, @op3, 4, 8, 9, 1, '2025-12-05 09:30:00'),      -- 30 min
(@lote3, @op3, 4, 9, 10, 1, '2025-12-05 10:00:00'),     -- 30 min
(@lote3, @op3, 4, 10, 11, 1, '2025-12-05 10:45:00'),    -- 45 min
(@lote3, @op3, 4, 11, 12, 1, '2025-12-05 12:00:00'),    -- 75 min
(@lote3, @op3, 4, 12, 13, 1, '2025-12-05 13:00:00'),    -- 60 min
(@lote3, @op3, 4, 13, 14, 1, '2025-12-05 15:30:00'),    -- 150 min
(@lote3, @op3, 4, 14, 15, 1, '2025-12-05 16:30:00'),    -- 60 min
(@lote3, @op3, 4, 15, 16, 1, '2025-12-05 17:00:00'),    -- 30 min
(@lote3, @op3, 4, 16, 17, 1, '2025-12-06 08:00:00'),    -- overnight + 180 min vulc
(@lote3, @op3, 4, 17, 18, 1, '2025-12-06 09:30:00'),    -- 90 min
(@lote3, @op3, 4, 18, 20, 1, '2025-12-06 11:00:00'),    -- 90 min
(@lote3, @op3, 4, 20, 21, 1, '2025-12-06 12:00:00'),    -- 60 min
(@lote3, @op3, 4, 21, 22, 1, '2025-12-06 12:30:00');    -- 30 min

-- LOTE 4 (OP4 - 6 unidades - 56h total = 9.33h/un = 560 min/un)
INSERT INTO op_lotes_etapas_log (lote_id, ordem_producao_id, quantidade_movida, etapa_anterior_id, etapa_nova_id, usuario_id, created_at) VALUES
(@lote4, @op4, 6, NULL, 8, 1, '2025-12-07 08:30:00'),
(@lote4, @op4, 6, 8, 9, 1, '2025-12-07 09:15:00'),      -- 45 min
(@lote4, @op4, 6, 9, 10, 1, '2025-12-07 10:00:00'),     -- 45 min
(@lote4, @op4, 6, 10, 11, 1, '2025-12-07 11:30:00'),    -- 90 min
(@lote4, @op4, 6, 11, 12, 1, '2025-12-07 14:00:00'),    -- 150 min
(@lote4, @op4, 6, 12, 13, 1, '2025-12-07 16:00:00'),    -- 120 min
(@lote4, @op4, 6, 13, 14, 1, '2025-12-08 08:00:00'),    -- overnight + 240 min
(@lote4, @op4, 6, 14, 15, 1, '2025-12-08 10:00:00'),    -- 120 min
(@lote4, @op4, 6, 15, 16, 1, '2025-12-08 11:00:00'),    -- 60 min
(@lote4, @op4, 6, 16, 17, 1, '2025-12-08 16:00:00'),    -- 300 min
(@lote4, @op4, 6, 17, 18, 1, '2025-12-08 18:00:00'),    -- 120 min
(@lote4, @op4, 6, 18, 20, 1, '2025-12-09 08:00:00'),    -- overnight
(@lote4, @op4, 6, 20, 21, 1, '2025-12-09 09:30:00'),    -- 90 min
(@lote4, @op4, 6, 21, 22, 1, '2025-12-09 10:00:00');    -- 30 min

-- LOTE 5 (OP5 - 7 unidades - 59h total = 8.43h/un = 506 min/un)
INSERT INTO op_lotes_etapas_log (lote_id, ordem_producao_id, quantidade_movida, etapa_anterior_id, etapa_nova_id, usuario_id, created_at) VALUES
(@lote5, @op5, 7, NULL, 8, 1, '2025-12-09 07:00:00'),
(@lote5, @op5, 7, 8, 9, 1, '2025-12-09 08:00:00'),      -- 60 min
(@lote5, @op5, 7, 9, 10, 1, '2025-12-09 08:30:00'),     -- 30 min
(@lote5, @op5, 7, 10, 11, 1, '2025-12-09 10:00:00'),    -- 90 min
(@lote5, @op5, 7, 11, 12, 1, '2025-12-09 12:00:00'),    -- 120 min
(@lote5, @op5, 7, 12, 13, 1, '2025-12-09 14:00:00'),    -- 120 min
(@lote5, @op5, 7, 13, 14, 1, '2025-12-09 18:00:00'),    -- 240 min
(@lote5, @op5, 7, 14, 15, 1, '2025-12-10 08:00:00'),    -- overnight
(@lote5, @op5, 7, 15, 16, 1, '2025-12-10 09:00:00'),    -- 60 min
(@lote5, @op5, 7, 16, 17, 1, '2025-12-10 14:00:00'),    -- 300 min
(@lote5, @op5, 7, 17, 18, 1, '2025-12-10 16:00:00'),    -- 120 min
(@lote5, @op5, 7, 18, 20, 1, '2025-12-11 08:00:00'),    -- overnight
(@lote5, @op5, 7, 20, 21, 1, '2025-12-11 10:00:00'),    -- 120 min
(@lote5, @op5, 7, 21, 22, 1, '2025-12-11 10:30:00');    -- 30 min

-- LOTE 6 (OP6 - 5 unidades - 30.5h total = 6.1h/un = 366 min/un)
INSERT INTO op_lotes_etapas_log (lote_id, ordem_producao_id, quantidade_movida, etapa_anterior_id, etapa_nova_id, usuario_id, created_at) VALUES
(@lote6, @op6, 5, NULL, 8, 1, '2025-12-11 08:00:00'),
(@lote6, @op6, 5, 8, 9, 1, '2025-12-11 08:30:00'),      -- 30 min
(@lote6, @op6, 5, 9, 10, 1, '2025-12-11 09:00:00'),     -- 30 min
(@lote6, @op6, 5, 10, 11, 1, '2025-12-11 09:45:00'),    -- 45 min
(@lote6, @op6, 5, 11, 12, 1, '2025-12-11 11:00:00'),    -- 75 min
(@lote6, @op6, 5, 12, 13, 1, '2025-12-11 12:00:00'),    -- 60 min
(@lote6, @op6, 5, 13, 14, 1, '2025-12-11 14:30:00'),    -- 150 min
(@lote6, @op6, 5, 14, 15, 1, '2025-12-11 15:30:00'),    -- 60 min
(@lote6, @op6, 5, 15, 16, 1, '2025-12-11 16:00:00'),    -- 30 min
(@lote6, @op6, 5, 16, 17, 1, '2025-12-12 08:00:00'),    -- overnight + vulc
(@lote6, @op6, 5, 17, 18, 1, '2025-12-12 09:00:00'),    -- 60 min
(@lote6, @op6, 5, 18, 20, 1, '2025-12-12 10:30:00'),    -- 90 min
(@lote6, @op6, 5, 20, 21, 1, '2025-12-12 11:30:00'),    -- 60 min
(@lote6, @op6, 5, 21, 22, 1, '2025-12-12 12:00:00');    -- 30 min

-- LOTE 7 (OP7 - 10 unidades - 81.5h total = 8.15h/un = 489 min/un)
INSERT INTO op_lotes_etapas_log (lote_id, ordem_producao_id, quantidade_movida, etapa_anterior_id, etapa_nova_id, usuario_id, created_at) VALUES
(@lote7, @op7, 10, NULL, 8, 1, '2025-12-13 07:30:00'),
(@lote7, @op7, 10, 8, 9, 1, '2025-12-13 09:00:00'),     -- 90 min
(@lote7, @op7, 10, 9, 10, 1, '2025-12-13 10:00:00'),    -- 60 min
(@lote7, @op7, 10, 10, 11, 1, '2025-12-13 12:00:00'),   -- 120 min
(@lote7, @op7, 10, 11, 12, 1, '2025-12-13 15:00:00'),   -- 180 min
(@lote7, @op7, 10, 12, 13, 1, '2025-12-13 18:00:00'),   -- 180 min
(@lote7, @op7, 10, 13, 14, 1, '2025-12-14 12:00:00'),   -- overnight + 300 min
(@lote7, @op7, 10, 14, 15, 1, '2025-12-14 15:00:00'),   -- 180 min
(@lote7, @op7, 10, 15, 16, 1, '2025-12-14 16:30:00'),   -- 90 min
(@lote7, @op7, 10, 16, 17, 1, '2025-12-15 12:00:00'),   -- overnight + vulc 360 min
(@lote7, @op7, 10, 17, 18, 1, '2025-12-15 14:00:00'),   -- 120 min
(@lote7, @op7, 10, 18, 20, 1, '2025-12-16 08:00:00'),   -- overnight
(@lote7, @op7, 10, 20, 21, 1, '2025-12-16 10:00:00'),   -- 120 min
(@lote7, @op7, 10, 21, 22, 1, '2025-12-16 11:00:00');   -- 60 min

-- LOTE 8 (OP8 - 3 unidades - 26.5h total = 8.83h/un = 530 min/un)
INSERT INTO op_lotes_etapas_log (lote_id, ordem_producao_id, quantidade_movida, etapa_anterior_id, etapa_nova_id, usuario_id, created_at) VALUES
(@lote8, @op8, 3, NULL, 8, 1, '2025-12-15 09:30:00'),
(@lote8, @op8, 3, 8, 9, 1, '2025-12-15 10:00:00'),      -- 30 min
(@lote8, @op8, 3, 9, 10, 1, '2025-12-15 10:20:00'),     -- 20 min
(@lote8, @op8, 3, 10, 11, 1, '2025-12-15 10:50:00'),    -- 30 min
(@lote8, @op8, 3, 11, 12, 1, '2025-12-15 11:50:00'),    -- 60 min
(@lote8, @op8, 3, 12, 13, 1, '2025-12-15 12:30:00'),    -- 40 min
(@lote8, @op8, 3, 13, 14, 1, '2025-12-15 14:30:00'),    -- 120 min
(@lote8, @op8, 3, 14, 15, 1, '2025-12-15 15:30:00'),    -- 60 min
(@lote8, @op8, 3, 15, 16, 1, '2025-12-15 16:00:00'),    -- 30 min
(@lote8, @op8, 3, 16, 17, 1, '2025-12-16 08:00:00'),    -- overnight + vulc
(@lote8, @op8, 3, 17, 18, 1, '2025-12-16 09:00:00'),    -- 60 min
(@lote8, @op8, 3, 18, 20, 1, '2025-12-16 10:00:00'),    -- 60 min
(@lote8, @op8, 3, 20, 21, 1, '2025-12-16 10:45:00'),    -- 45 min
(@lote8, @op8, 3, 21, 22, 1, '2025-12-16 11:00:00');    -- 15 min

-- LOTE 9 (OP9 - 9 unidades - 80h total = 8.89h/un = 533 min/un)
INSERT INTO op_lotes_etapas_log (lote_id, ordem_producao_id, quantidade_movida, etapa_anterior_id, etapa_nova_id, usuario_id, created_at) VALUES
(@lote9, @op9, 9, NULL, 8, 1, '2025-12-17 08:00:00'),
(@lote9, @op9, 9, 8, 9, 1, '2025-12-17 09:00:00'),      -- 60 min
(@lote9, @op9, 9, 9, 10, 1, '2025-12-17 09:45:00'),     -- 45 min
(@lote9, @op9, 9, 10, 11, 1, '2025-12-17 11:30:00'),    -- 105 min
(@lote9, @op9, 9, 11, 12, 1, '2025-12-17 14:00:00'),    -- 150 min
(@lote9, @op9, 9, 12, 13, 1, '2025-12-17 16:30:00'),    -- 150 min
(@lote9, @op9, 9, 13, 14, 1, '2025-12-18 10:00:00'),    -- overnight + 210 min
(@lote9, @op9, 9, 14, 15, 1, '2025-12-18 12:30:00'),    -- 150 min
(@lote9, @op9, 9, 15, 16, 1, '2025-12-18 14:00:00'),    -- 90 min
(@lote9, @op9, 9, 16, 17, 1, '2025-12-19 10:00:00'),    -- overnight + vulc
(@lote9, @op9, 9, 17, 18, 1, '2025-12-19 12:00:00'),    -- 120 min
(@lote9, @op9, 9, 18, 20, 1, '2025-12-19 15:00:00'),    -- 180 min
(@lote9, @op9, 9, 20, 21, 1, '2025-12-20 08:00:00'),    -- overnight
(@lote9, @op9, 9, 21, 22, 1, '2025-12-20 09:00:00');    -- 60 min

-- LOTE 10 (OP10 - 12 unidades - 107.5h total = 8.96h/un = 538 min/un)
INSERT INTO op_lotes_etapas_log (lote_id, ordem_producao_id, quantidade_movida, etapa_anterior_id, etapa_nova_id, usuario_id, created_at) VALUES
(@lote10, @op10, 12, NULL, 8, 1, '2025-12-19 07:00:00'),
(@lote10, @op10, 12, 8, 9, 1, '2025-12-19 09:00:00'),    -- 120 min
(@lote10, @op10, 12, 9, 10, 1, '2025-12-19 10:00:00'),   -- 60 min
(@lote10, @op10, 12, 10, 11, 1, '2025-12-19 12:30:00'),  -- 150 min
(@lote10, @op10, 12, 11, 12, 1, '2025-12-19 16:00:00'),  -- 210 min
(@lote10, @op10, 12, 12, 13, 1, '2025-12-20 08:00:00'),  -- overnight
(@lote10, @op10, 12, 13, 14, 1, '2025-12-20 14:00:00'),  -- 360 min
(@lote10, @op10, 12, 14, 15, 1, '2025-12-20 18:00:00'),  -- 240 min
(@lote10, @op10, 12, 15, 16, 1, '2025-12-21 08:00:00'),  -- overnight
(@lote10, @op10, 12, 16, 17, 1, '2025-12-22 08:00:00'),  -- overnight + vulc longa
(@lote10, @op10, 12, 17, 18, 1, '2025-12-22 11:00:00'),  -- 180 min
(@lote10, @op10, 12, 18, 20, 1, '2025-12-22 15:00:00'),  -- 240 min
(@lote10, @op10, 12, 20, 21, 1, '2025-12-23 08:00:00'),  -- overnight
(@lote10, @op10, 12, 21, 22, 1, '2025-12-23 10:00:00');  -- 120 min

-- =====================================================
-- VERIFICAÇÃO FINAL
-- =====================================================

SELECT '===== RESUMO DOS DADOS CRIADOS =====' AS info;

SELECT 'Template criado:' AS info;
SELECT id, produto_id, nome_template, tempo_producao_horas FROM produto_templates_producao WHERE produto_id = 1;

SELECT 'Orçamentos criados:' AS info;
SELECT id, numero, valor_total, status FROM orcamentos WHERE observacoes LIKE '%teste ficha técnica%';

SELECT 'OPs criadas:' AS info;
SELECT id, numero_op, quantidade, status, data_inicio_producao, data_conclusao,
       TIMESTAMPDIFF(MINUTE, data_inicio_producao, data_conclusao) as tempo_minutos
FROM ordens_producao WHERE produto_id = 1 AND status = 'concluida' ORDER BY data_conclusao DESC LIMIT 10;

SELECT 'Logs de etapas criados por OP:' AS info;
SELECT op.numero_op, COUNT(log.id) as total_logs
FROM ordens_producao op
INNER JOIN op_lotes l ON l.ordem_producao_id = op.id
INNER JOIN op_lotes_etapas_log log ON log.lote_id = l.id
WHERE op.produto_id = 1 AND op.status = 'concluida'
GROUP BY op.id, op.numero_op;

SELECT 'CÁLCULO ESPERADO:' AS info;
SELECT 
    SUM(quantidade) as total_unidades,
    SUM(TIMESTAMPDIFF(MINUTE, data_inicio_producao, data_conclusao)) as tempo_total_minutos,
    ROUND(SUM(TIMESTAMPDIFF(MINUTE, data_inicio_producao, data_conclusao)) / SUM(quantidade), 2) as tempo_por_unidade_minutos,
    ROUND(SUM(TIMESTAMPDIFF(MINUTE, data_inicio_producao, data_conclusao)) / SUM(quantidade) / 60, 4) as tempo_por_unidade_horas
FROM ordens_producao 
WHERE produto_id = 1 AND status = 'concluida' 
AND data_inicio_producao IS NOT NULL AND data_conclusao IS NOT NULL;

SELECT '===== FIM DO SCRIPT =====' AS info;
SELECT CONCAT('Acesse a Ficha Técnica: http://localhost:8080/produtos/fichas-tecnicas/', 
    (SELECT id FROM produto_templates_producao WHERE produto_id = 1 LIMIT 1)) AS url;
