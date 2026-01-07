-- =====================================================
-- SCRIPT 032 OTIMIZADO: SISTEMA DE PREVISÃO DE PRODUÇÃO
-- Data: 2025-12-27
-- Descrição: Versão otimizada usando estrutura EXISTENTE
-- 
-- IMPORTANTE: Este script NÃO cria tabelas redundantes!
-- Usa VIEWS sobre tabelas existentes do chão de fábrica.
-- =====================================================

USE supply_chain_system;

-- =====================================================
-- ÚNICA TABELA NECESSÁRIA: FERIADOS
-- (não existia no sistema)
-- =====================================================

CREATE TABLE IF NOT EXISTS config_feriados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT DEFAULT NULL COMMENT 'NULL = todas as empresas',
    data DATE NOT NULL,
    descricao VARCHAR(100) NOT NULL,
    tipo ENUM('feriado', 'folga', 'manutencao', 'outro') DEFAULT 'feriado',
    recorrente_anual TINYINT(1) DEFAULT 0 COMMENT '1 = repete todo ano',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_empresa_data (empresa_id, data),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Feriados e dias não úteis';

-- Inserir feriados nacionais (se não existirem)
INSERT INTO config_feriados (empresa_id, data, descricao, tipo, recorrente_anual)
SELECT * FROM (
    SELECT NULL AS empresa_id, '2025-01-01' AS data, 'Confraternização Universal' AS descricao, 'feriado' AS tipo, 1 AS recorrente_anual UNION ALL
    SELECT NULL, '2025-04-21', 'Tiradentes', 'feriado', 1 UNION ALL
    SELECT NULL, '2025-05-01', 'Dia do Trabalho', 'feriado', 1 UNION ALL
    SELECT NULL, '2025-09-07', 'Independência do Brasil', 'feriado', 1 UNION ALL
    SELECT NULL, '2025-10-12', 'Nossa Sra. Aparecida', 'feriado', 1 UNION ALL
    SELECT NULL, '2025-11-02', 'Finados', 'feriado', 1 UNION ALL
    SELECT NULL, '2025-11-15', 'Proclamação da República', 'feriado', 1 UNION ALL
    SELECT NULL, '2025-12-25', 'Natal', 'feriado', 1
) AS feriados_novos
WHERE NOT EXISTS (
    SELECT 1 FROM config_feriados cf 
    WHERE cf.empresa_id IS NULL AND cf.data = feriados_novos.data
);

-- =====================================================
-- VIEW 1: TEMPO MÉDIO POR PRODUTO/ETAPA
-- Usa dados do log existente (op_lotes_etapas_log)
-- Substitui a tabela produtos_tempo_etapa do script original
-- =====================================================

CREATE OR REPLACE VIEW vw_tempo_producao_etapa AS
SELECT 
    op.produto_id,
    p.name AS produto_nome,
    log.etapa_nova_id AS etapa_id,
    e.nome AS etapa_nome,
    e.ordem AS etapa_ordem,
    COUNT(DISTINCT log.id) AS qtd_amostras,
    -- Tempo médio entre entrada e saída da etapa
    ROUND(AVG(
        TIMESTAMPDIFF(MINUTE, log.created_at, 
            COALESCE(
                (SELECT MIN(log2.created_at) 
                 FROM op_lotes_etapas_log log2 
                 WHERE log2.lote_id = log.lote_id 
                   AND log2.created_at > log.created_at),
                l.data_fim_operador
            )
        )
    ), 0) AS tempo_medio_minutos,
    -- Tempo mínimo
    ROUND(MIN(
        TIMESTAMPDIFF(MINUTE, log.created_at, 
            COALESCE(
                (SELECT MIN(log2.created_at) 
                 FROM op_lotes_etapas_log log2 
                 WHERE log2.lote_id = log.lote_id 
                   AND log2.created_at > log.created_at),
                l.data_fim_operador
            )
        )
    ), 0) AS tempo_minimo_minutos,
    -- Tempo máximo
    ROUND(MAX(
        TIMESTAMPDIFF(MINUTE, log.created_at, 
            COALESCE(
                (SELECT MIN(log2.created_at) 
                 FROM op_lotes_etapas_log log2 
                 WHERE log2.lote_id = log.lote_id 
                   AND log2.created_at > log.created_at),
                l.data_fim_operador
            )
        )
    ), 0) AS tempo_maximo_minutos,
    MAX(log.created_at) AS ultima_atualizacao
FROM op_lotes_etapas_log log
INNER JOIN op_lotes l ON log.lote_id = l.id
INNER JOIN ordens_producao op ON l.ordem_producao_id = op.id
INNER JOIN producao_etapas e ON log.etapa_nova_id = e.id
INNER JOIN products p ON op.produto_id = p.id
WHERE op.status = 'concluida'
  AND op.data_conclusao >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
GROUP BY op.produto_id, p.name, log.etapa_nova_id, e.nome, e.ordem
HAVING tempo_medio_minutos > 0 AND tempo_medio_minutos < 1440;

-- =====================================================
-- VIEW 2: GARGALOS POR ETAPA (Fila de Produção)
-- Usa dados de op_lotes existente
-- =====================================================

CREATE OR REPLACE VIEW vw_gargalos_etapa AS
SELECT 
    e.id AS etapa_id,
    e.nome AS etapa_nome,
    e.ordem AS etapa_ordem,
    -- Contadores de status
    COUNT(CASE WHEN l.status_operador = 'em_espera' THEN 1 END) AS qtd_aguardando,
    COUNT(CASE WHEN l.status_operador = 'em_producao' THEN 1 END) AS qtd_em_producao,
    COUNT(CASE WHEN l.status_operador = 'pausado' THEN 1 END) AS qtd_pausados,
    COUNT(l.id) AS qtd_total,
    -- Tempo médio na fila (minutos)
    ROUND(AVG(CASE 
        WHEN l.status_operador = 'em_espera' 
        THEN TIMESTAMPDIFF(MINUTE, l.created_at, NOW()) 
    END), 0) AS tempo_medio_fila_minutos,
    -- Capacidade padrão (10 lotes/dia)
    10 AS capacidade_diaria,
    -- Indicador de gargalo
    CASE 
        WHEN COUNT(CASE WHEN l.status_operador = 'em_espera' THEN 1 END) > 30 THEN 'critico'
        WHEN COUNT(CASE WHEN l.status_operador = 'em_espera' THEN 1 END) > 10 THEN 'atencao'
        ELSE 'normal'
    END AS status_gargalo,
    -- Dias de espera estimados
    ROUND(COUNT(CASE WHEN l.status_operador = 'em_espera' THEN 1 END) / 10.0, 1) AS dias_espera_estimado
FROM producao_etapas e
LEFT JOIN op_lotes l ON l.etapa_atual_id = e.id 
    AND l.status NOT IN ('concluido', 'cancelado')
WHERE e.ativo = 1
GROUP BY e.id, e.nome, e.ordem
ORDER BY e.ordem;

-- =====================================================
-- VIEW 3: FILA DE PRODUÇÃO COMPLETA COM PRIORIDADE
-- =====================================================

CREATE OR REPLACE VIEW vw_fila_producao AS
SELECT 
    l.id AS lote_id,
    l.ordem_producao_id,
    op.numero_op,
    op.produto_id,
    p.name AS produto_nome,
    l.sequencia AS numero_lote,
    l.quantidade,
    l.etapa_atual_id,
    e.nome AS etapa_nome,
    e.ordem AS etapa_ordem,
    l.status_operador,
    COALESCE(l.prioridade, 5) AS prioridade,
    l.created_at AS data_chegada,
    -- Tempo na fila (minutos)
    TIMESTAMPDIFF(MINUTE, l.created_at, NOW()) AS minutos_na_fila,
    -- Cliente (para priorização)
    op.cliente_id,
    c.name AS cliente_nome,
    op.data_prevista,
    -- Posição na fila por etapa
    ROW_NUMBER() OVER (
        PARTITION BY l.etapa_atual_id 
        ORDER BY COALESCE(l.prioridade, 5) DESC, l.created_at ASC
    ) AS posicao_fila
FROM op_lotes l
INNER JOIN ordens_producao op ON l.ordem_producao_id = op.id
INNER JOIN products p ON op.produto_id = p.id
INNER JOIN producao_etapas e ON l.etapa_atual_id = e.id
LEFT JOIN customers c ON op.cliente_id = c.id
WHERE l.status NOT IN ('concluido', 'cancelado')
ORDER BY e.ordem, COALESCE(l.prioridade, 5) DESC, l.created_at;

-- =====================================================
-- VIEW 4: TEMPO TOTAL ESTIMADO POR PRODUTO
-- Soma dos tempos médios de todas as etapas
-- =====================================================

CREATE OR REPLACE VIEW vw_tempo_total_produto AS
SELECT 
    produto_id,
    produto_nome,
    COUNT(DISTINCT etapa_id) AS total_etapas,
    SUM(tempo_medio_minutos) AS tempo_total_minutos,
    ROUND(SUM(tempo_medio_minutos) / 60, 2) AS tempo_total_horas,
    SUM(qtd_amostras) AS total_amostras,
    MAX(ultima_atualizacao) AS ultima_atualizacao
FROM vw_tempo_producao_etapa
GROUP BY produto_id, produto_nome;

-- =====================================================
-- VIEW 5: PREVISÃO DE PRODUÇÃO (Consolidado)
-- Combina tempo de produção + gargalos
-- =====================================================

CREATE OR REPLACE VIEW vw_previsao_producao AS
SELECT 
    tp.produto_id,
    tp.produto_nome,
    tp.tempo_total_minutos AS tempo_producao_minutos,
    tp.tempo_total_horas AS tempo_producao_horas,
    tp.total_etapas,
    tp.total_amostras,
    -- Tempo de fila (soma de todas as etapas com gargalo)
    COALESCE((
        SELECT SUM(g.dias_espera_estimado * 480) 
        FROM vw_gargalos_etapa g 
        WHERE g.qtd_aguardando > 0
    ), 0) AS tempo_fila_minutos,
    -- Tempo total estimado
    tp.tempo_total_minutos + COALESCE((
        SELECT SUM(g.dias_espera_estimado * 480) 
        FROM vw_gargalos_etapa g 
        WHERE g.qtd_aguardando > 0
    ), 0) AS tempo_total_estimado_minutos,
    -- Dias úteis necessários (8h/dia = 480min)
    ROUND((tp.tempo_total_minutos + COALESCE((
        SELECT SUM(g.dias_espera_estimado * 480) 
        FROM vw_gargalos_etapa g 
        WHERE g.qtd_aguardando > 0
    ), 0)) / 480, 1) AS dias_uteis_necessarios,
    -- Data prevista (aproximada)
    DATE_ADD(CURDATE(), INTERVAL CEIL((tp.tempo_total_minutos + COALESCE((
        SELECT SUM(g.dias_espera_estimado * 480) 
        FROM vw_gargalos_etapa g 
        WHERE g.qtd_aguardando > 0
    ), 0)) / 480) DAY) AS previsao_conclusao,
    tp.ultima_atualizacao
FROM vw_tempo_total_produto tp;

-- =====================================================
-- VIEW 6: ESTOQUE PRODUZIDO POR DNA
-- Para o botão "Verificar Estoque Produzido"
-- =====================================================

CREATE OR REPLACE VIEW vw_estoque_produzido_dna AS
SELECT 
    p.id AS produto_id,
    p.name AS produto_nome,
    p.internal_code AS codigo_interno,
    COALESCE(cs.quantity, p.stock_quantity, 0) AS estoque_atual,
    pet.codigo_dna,
    pet.tipo_correia_id,
    tc.nome AS tipo_correia_nome,
    pet.material_base_id,
    mc.nome AS material_base_nome,
    pet.largura_mm,
    pet.comprimento_mm,
    pet.espessura_mm,
    -- Última produção
    (SELECT MAX(op.data_conclusao) 
     FROM ordens_producao op 
     WHERE op.produto_id = p.id AND op.status = 'concluida') AS ultima_producao,
    -- Quantidade produzida (últimos 6 meses)
    (SELECT SUM(op.quantidade) 
     FROM ordens_producao op 
     WHERE op.produto_id = p.id 
       AND op.status = 'concluida'
       AND op.data_conclusao >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)) AS qtd_produzida_6m
FROM products p
LEFT JOIN current_stock cs ON cs.product_id = p.id AND cs.location_id = 1
LEFT JOIN produto_especificacoes_tecnicas pet ON pet.produto_id = p.id
LEFT JOIN tipos_correia tc ON tc.id = pet.tipo_correia_id
LEFT JOIN materiais_correia mc ON mc.id = pet.material_base_id
WHERE p.active = 1
  AND COALESCE(cs.quantity, p.stock_quantity, 0) > 0;

-- =====================================================
-- VERIFICAÇÃO
-- =====================================================

SELECT 'Script 032 OTIMIZADO executado com sucesso!' AS status;
SELECT 'IMPORTANTE: Este script usa VIEWS sobre tabelas existentes!' AS nota;

-- Mostrar views criadas
SELECT 'Views criadas:' AS info;
SELECT TABLE_NAME AS view_name 
FROM information_schema.VIEWS 
WHERE TABLE_SCHEMA = DATABASE() 
  AND TABLE_NAME LIKE 'vw_%producao%' OR TABLE_NAME LIKE 'vw_%gargalo%' OR TABLE_NAME LIKE 'vw_%tempo%' OR TABLE_NAME LIKE 'vw_%dna%'
ORDER BY TABLE_NAME;

-- Testar view de gargalos
SELECT 'Teste - Gargalos por etapa:' AS info;
SELECT * FROM vw_gargalos_etapa LIMIT 5;

-- Testar view de previsão
SELECT 'Teste - Previsão por produto:' AS info;
SELECT * FROM vw_previsao_producao LIMIT 5;
