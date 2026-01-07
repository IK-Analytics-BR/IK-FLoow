-- =====================================================
-- SCRIPT 043: CRIAR ORÇAMENTOS E OPs DE TESTE
-- =====================================================
-- Cria orçamentos e ordens de produção de teste
-- para validar o sistema de previsão de produção
-- =====================================================

-- Limpar dados de teste anteriores
SET FOREIGN_KEY_CHECKS = 0;
DELETE FROM op_lotes WHERE ordem_producao_id IN (SELECT id FROM ordens_producao WHERE observacoes LIKE '%TESTE AUTOMATICO%');
DELETE FROM ordem_producao_itens WHERE ordem_producao_id IN (SELECT id FROM ordens_producao WHERE observacoes LIKE '%TESTE AUTOMATICO%');
DELETE FROM ordens_producao WHERE observacoes LIKE '%TESTE AUTOMATICO%';
DELETE FROM orcamento_itens WHERE orcamento_id IN (SELECT id FROM orcamentos WHERE observacoes LIKE '%TESTE AUTOMATICO%');
DELETE FROM orcamentos WHERE observacoes LIKE '%TESTE AUTOMATICO%';
SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================
-- VARIÁVEIS AUXILIARES
-- =====================================================
SET @empresa_id = 1;
SET @cliente_id = 1;
SET @vendedor_id = 1;

-- Buscar alguns produtos para os testes
SET @prod_cs_1 = (SELECT id FROM products WHERE category_id = 6 AND name LIKE 'CS %' ORDER BY RAND() LIMIT 1);
SET @prod_cs_2 = (SELECT id FROM products WHERE category_id = 6 AND name LIKE 'CS %' AND id != @prod_cs_1 ORDER BY RAND() LIMIT 1);
SET @prod_cs_3 = (SELECT id FROM products WHERE category_id = 6 AND name LIKE 'CS %' AND id NOT IN (@prod_cs_1, @prod_cs_2) ORDER BY RAND() LIMIT 1);
SET @prod_pv_1 = (SELECT id FROM products WHERE category_id = 6 AND name LIKE 'PV %' ORDER BY RAND() LIMIT 1);
SET @prod_pv_2 = (SELECT id FROM products WHERE category_id = 6 AND name LIKE 'PV %' AND id != @prod_pv_1 ORDER BY RAND() LIMIT 1);
SET @prod_ct_1 = (SELECT id FROM products WHERE category_id = 6 AND (name LIKE 'CT %' OR name LIKE 'CORREIA TRANSP%') ORDER BY RAND() LIMIT 1);

-- Etapa inicial para OPs
SET @etapa_inicial = (SELECT MIN(id) FROM producao_etapas WHERE ativo = 1);

-- =====================================================
-- ORÇAMENTO 1: Pequeno (1 item CS) - Urgente
-- =====================================================
INSERT INTO orcamentos (
    empresa_id, cliente_id, vendedor_id, numero,
    data_emissao, data_validade, prazo_entrega,
    valor_total, status, observacoes,
    data_previsao_producao, data_previsao_entrega, dias_transporte
) VALUES (
    @empresa_id, @cliente_id, @vendedor_id, 'ORC-TESTE-001',
    CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY), 5,
    450.00, 'aprovado', 'TESTE AUTOMATICO - Orçamento pequeno urgente',
    DATE_ADD(CURDATE(), INTERVAL 2 DAY), DATE_ADD(CURDATE(), INTERVAL 5 DAY), 3
);
SET @orc_1 = LAST_INSERT_ID();

INSERT INTO orcamento_itens (orcamento_id, produto_id, quantidade, preco_unitario, valor_total)
VALUES (@orc_1, @prod_cs_1, 1, 450.00, 450.00);

-- =====================================================
-- ORÇAMENTO 2: Médio (3 itens CS + PV) - Normal
-- =====================================================
INSERT INTO orcamentos (
    empresa_id, cliente_id, vendedor_id, numero,
    data_emissao, data_validade, prazo_entrega,
    valor_total, status, observacoes,
    data_previsao_producao, data_previsao_entrega, dias_transporte
) VALUES (
    @empresa_id, @cliente_id, @vendedor_id, 'ORC-TESTE-002',
    CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY), 15,
    1850.00, 'aprovado', 'TESTE AUTOMATICO - Orçamento médio',
    DATE_ADD(CURDATE(), INTERVAL 7 DAY), DATE_ADD(CURDATE(), INTERVAL 12 DAY), 5
);
SET @orc_2 = LAST_INSERT_ID();

INSERT INTO orcamento_itens (orcamento_id, produto_id, quantidade, preco_unitario, valor_total) VALUES
(@orc_2, @prod_cs_1, 2, 450.00, 900.00),
(@orc_2, @prod_cs_2, 1, 480.00, 480.00),
(@orc_2, @prod_pv_1, 2, 235.00, 470.00);

-- =====================================================
-- ORÇAMENTO 3: Grande (5 itens variados) - Longo prazo
-- =====================================================
INSERT INTO orcamentos (
    empresa_id, cliente_id, vendedor_id, numero,
    data_emissao, data_validade, prazo_entrega,
    valor_total, status, observacoes,
    data_previsao_producao, data_previsao_entrega, dias_transporte
) VALUES (
    @empresa_id, @cliente_id, @vendedor_id, 'ORC-TESTE-003',
    CURDATE(), DATE_ADD(CURDATE(), INTERVAL 45 DAY), 30,
    4200.00, 'aprovado', 'TESTE AUTOMATICO - Orçamento grande',
    DATE_ADD(CURDATE(), INTERVAL 20 DAY), DATE_ADD(CURDATE(), INTERVAL 27 DAY), 7
);
SET @orc_3 = LAST_INSERT_ID();

INSERT INTO orcamento_itens (orcamento_id, produto_id, quantidade, preco_unitario, valor_total) VALUES
(@orc_3, @prod_cs_1, 3, 450.00, 1350.00),
(@orc_3, @prod_cs_2, 2, 480.00, 960.00),
(@orc_3, @prod_cs_3, 2, 420.00, 840.00),
(@orc_3, @prod_pv_1, 3, 235.00, 705.00),
(@orc_3, @prod_pv_2, 1, 345.00, 345.00);

-- =====================================================
-- ORDENS DE PRODUÇÃO DE TESTE
-- =====================================================

-- OP 1: Urgente - Em produção (etapa 13 - Montagem)
INSERT INTO ordens_producao (
    empresa_id, cliente_id, produto_id, quantidade,
    numero_op, status, data_solicitacao, data_prevista,
    data_inicio_producao, etapa_atual_id, observacoes
) VALUES (
    @empresa_id, @cliente_id, @prod_cs_1, 2,
    'OP-TESTE-001', 'em_producao', DATE_SUB(CURDATE(), INTERVAL 2 DAY), DATE_ADD(CURDATE(), INTERVAL 1 DAY),
    DATE_SUB(CURDATE(), INTERVAL 1 DAY), 13, 'TESTE AUTOMATICO - OP urgente em montagem'
);
SET @op_1 = LAST_INSERT_ID();

INSERT INTO op_lotes (ordem_producao_id, sequencia, quantidade, etapa_atual_id, status, prioridade)
VALUES (@op_1, 1, 2, 13, 'em_producao', 10);

-- OP 2: Normal - Em produção (etapa 11 - Prep Borracha)
INSERT INTO ordens_producao (
    empresa_id, cliente_id, produto_id, quantidade,
    numero_op, status, data_solicitacao, data_prevista,
    data_inicio_producao, etapa_atual_id, observacoes
) VALUES (
    @empresa_id, @cliente_id, @prod_cs_2, 3,
    'OP-TESTE-002', 'em_producao', DATE_SUB(CURDATE(), INTERVAL 1 DAY), DATE_ADD(CURDATE(), INTERVAL 5 DAY),
    CURDATE(), 11, 'TESTE AUTOMATICO - OP normal em preparação'
);
SET @op_2 = LAST_INSERT_ID();

INSERT INTO op_lotes (ordem_producao_id, sequencia, quantidade, etapa_atual_id, status, prioridade)
VALUES (@op_2, 1, 3, 11, 'em_producao', 5);

-- OP 3: Atrasada - Em produção (etapa 16 - Vulcanização) mas já passou prazo
INSERT INTO ordens_producao (
    empresa_id, cliente_id, produto_id, quantidade,
    numero_op, status, data_solicitacao, data_prevista,
    data_inicio_producao, etapa_atual_id, observacoes
) VALUES (
    @empresa_id, @cliente_id, @prod_pv_1, 4,
    'OP-TESTE-003', 'em_producao', DATE_SUB(CURDATE(), INTERVAL 10 DAY), DATE_SUB(CURDATE(), INTERVAL 2 DAY),
    DATE_SUB(CURDATE(), INTERVAL 8 DAY), 16, 'TESTE AUTOMATICO - OP ATRASADA em vulcanização'
);
SET @op_3 = LAST_INSERT_ID();

INSERT INTO op_lotes (ordem_producao_id, sequencia, quantidade, etapa_atual_id, status, prioridade)
VALUES (@op_3, 1, 4, 16, 'em_producao', 8);

-- OP 4: Pendente (ainda não iniciou)
INSERT INTO ordens_producao (
    empresa_id, cliente_id, produto_id, quantidade,
    numero_op, status, data_solicitacao, data_prevista,
    etapa_atual_id, observacoes
) VALUES (
    @empresa_id, @cliente_id, @prod_cs_3, 1,
    'OP-TESTE-004', 'pendente', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 10 DAY),
    @etapa_inicial, 'TESTE AUTOMATICO - OP pendente aguardando'
);
SET @op_4 = LAST_INSERT_ID();

INSERT INTO op_lotes (ordem_producao_id, sequencia, quantidade, etapa_atual_id, status, prioridade)
VALUES (@op_4, 1, 1, @etapa_inicial, 'pendente', 3);

-- OP 5: Transportadora - Em produção (processo longo)
INSERT INTO ordens_producao (
    empresa_id, cliente_id, produto_id, quantidade,
    numero_op, status, data_solicitacao, data_prevista,
    data_inicio_producao, etapa_atual_id, observacoes
) VALUES (
    @empresa_id, @cliente_id, @prod_ct_1, 1,
    'OP-TESTE-005', 'em_producao', DATE_SUB(CURDATE(), INTERVAL 5 DAY), DATE_ADD(CURDATE(), INTERVAL 10 DAY),
    DATE_SUB(CURDATE(), INTERVAL 4 DAY), 12, 'TESTE AUTOMATICO - OP Transportadora (longa)'
);
SET @op_5 = LAST_INSERT_ID();

INSERT INTO op_lotes (ordem_producao_id, sequencia, quantidade, etapa_atual_id, status, prioridade)
VALUES (@op_5, 1, 1, 12, 'em_producao', 5);

-- OP 6: Concluída recentemente
INSERT INTO ordens_producao (
    empresa_id, cliente_id, produto_id, quantidade,
    numero_op, status, data_solicitacao, data_prevista,
    data_inicio_producao, data_conclusao, etapa_atual_id, observacoes
) VALUES (
    @empresa_id, @cliente_id, @prod_pv_2, 2,
    'OP-TESTE-006', 'concluida', DATE_SUB(CURDATE(), INTERVAL 7 DAY), DATE_SUB(CURDATE(), INTERVAL 1 DAY),
    DATE_SUB(CURDATE(), INTERVAL 6 DAY), CURDATE(), 22, 'TESTE AUTOMATICO - OP concluída'
);
SET @op_6 = LAST_INSERT_ID();

INSERT INTO op_lotes (ordem_producao_id, sequencia, quantidade, etapa_atual_id, status, prioridade)
VALUES (@op_6, 1, 2, 22, 'concluido', 5);

-- OP 7: Pendente na fila
INSERT INTO ordens_producao (
    empresa_id, cliente_id, produto_id, quantidade,
    numero_op, status, data_solicitacao, data_prevista,
    etapa_atual_id, observacoes
) VALUES (
    @empresa_id, @cliente_id, @prod_cs_1, 2, 
    'OP-TESTE-007', 'pendente', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 12 DAY), 
    @etapa_inicial, 'TESTE AUTOMATICO - OP fila 1'
);
SET @op_7 = LAST_INSERT_ID();

INSERT INTO op_lotes (ordem_producao_id, sequencia, quantidade, etapa_atual_id, status, prioridade)
VALUES (@op_7, 1, 2, @etapa_inicial, 'pendente', 2);

-- OP 8: Pendente na fila
INSERT INTO ordens_producao (
    empresa_id, cliente_id, produto_id, quantidade,
    numero_op, status, data_solicitacao, data_prevista,
    etapa_atual_id, observacoes
) VALUES (
    @empresa_id, @cliente_id, @prod_cs_2, 1, 
    'OP-TESTE-008', 'pendente', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY), 
    @etapa_inicial, 'TESTE AUTOMATICO - OP fila 2'
);
SET @op_8 = LAST_INSERT_ID();

INSERT INTO op_lotes (ordem_producao_id, sequencia, quantidade, etapa_atual_id, status, prioridade)
VALUES (@op_8, 1, 1, @etapa_inicial, 'pendente', 1);

-- =====================================================
-- VERIFICAÇÃO FINAL
-- =====================================================
SELECT 'ORÇAMENTOS CRIADOS' as info;
SELECT id, numero, status, valor_total, DATE(data_previsao_producao) as prev_prod, DATE(data_previsao_entrega) as prev_entrega
FROM orcamentos WHERE observacoes LIKE '%TESTE AUTOMATICO%';

SELECT 'ORDENS DE PRODUÇÃO CRIADAS' as info;
SELECT op.id, op.numero_op, op.status, op.quantidade, 
       DATE(op.data_prevista) as prev,
       e.nome as etapa_atual
FROM ordens_producao op
LEFT JOIN producao_etapas e ON op.etapa_atual_id = e.id
WHERE op.observacoes LIKE '%TESTE AUTOMATICO%'
ORDER BY op.id;

SELECT 'LOTES CRIADOS' as info;
SELECT l.id, op.numero_op, l.quantidade, l.status, e.nome as etapa
FROM op_lotes l
JOIN ordens_producao op ON l.ordem_producao_id = op.id
LEFT JOIN producao_etapas e ON l.etapa_atual_id = e.id
WHERE op.observacoes LIKE '%TESTE AUTOMATICO%';
