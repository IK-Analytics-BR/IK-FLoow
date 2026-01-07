-- =====================================================
-- SCRIPT 032: SISTEMA DE PREVISÃO DE PRODUÇÃO
-- Data: 2025-12-26
-- Descrição: Estrutura para cálculo de previsão de produção
-- NOTA: Jornada de trabalho usa tabelas existentes:
--       - jornadas_trabalho
--       - jornada_horarios
-- =====================================================

-- =====================================================
-- FASE A1: TEMPO DE PRODUÇÃO POR PRODUTO/ETAPA
-- =====================================================

CREATE TABLE IF NOT EXISTS produtos_tempo_etapa (
    id INT AUTO_INCREMENT PRIMARY KEY,
    produto_id INT NOT NULL,
    etapa_id INT NOT NULL,
    tempo_padrao_minutos INT DEFAULT 0 COMMENT 'Tempo padrão definido manualmente (minutos)',
    tempo_medio_historico INT DEFAULT 0 COMMENT 'Tempo médio calculado do histórico (minutos)',
    tempo_minimo_historico INT DEFAULT 0 COMMENT 'Menor tempo registrado (minutos)',
    tempo_maximo_historico INT DEFAULT 0 COMMENT 'Maior tempo registrado (minutos)',
    qtd_amostras INT DEFAULT 0 COMMENT 'Quantas OPs foram usadas no cálculo',
    ajuste_manual TINYINT(1) DEFAULT 0 COMMENT '1 se admin editou o tempo padrão',
    ultima_atualizacao_historico DATETIME DEFAULT NULL,
    observacao VARCHAR(255) DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_produto_etapa (produto_id, etapa_id),
    FOREIGN KEY (produto_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (etapa_id) REFERENCES producao_etapas(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Tempo de produção por produto em cada etapa';

-- =====================================================
-- FASE A3: FERIADOS E DIAS NÃO ÚTEIS
-- =====================================================

CREATE TABLE IF NOT EXISTS config_feriados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT DEFAULT NULL COMMENT 'NULL = todas as empresas',
    data DATE NOT NULL,
    descricao VARCHAR(100) NOT NULL,
    tipo ENUM('feriado', 'folga', 'manutencao', 'outro') DEFAULT 'feriado',
    recorrente_anual TINYINT(1) DEFAULT 0 COMMENT '1 = repete todo ano (ex: Natal)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_empresa_data (empresa_id, data),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Feriados e dias não úteis';

-- =====================================================
-- FASE A4: CAPACIDADE POR ETAPA
-- =====================================================

CREATE TABLE IF NOT EXISTS config_capacidade_etapa (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT DEFAULT NULL,
    etapa_id INT NOT NULL,
    capacidade_diaria_lotes INT DEFAULT 10 COMMENT 'Quantos lotes a etapa pode processar por dia',
    capacidade_simultanea INT DEFAULT 1 COMMENT 'Quantos lotes podem estar em produção ao mesmo tempo',
    tempo_setup_minutos INT DEFAULT 0 COMMENT 'Tempo de setup entre lotes',
    prioridade_gargalo INT DEFAULT 5 COMMENT '1-10, etapas com menor valor têm prioridade',
    observacao VARCHAR(255) DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_empresa_etapa (empresa_id, etapa_id),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    FOREIGN KEY (etapa_id) REFERENCES producao_etapas(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Capacidade de processamento por etapa';

-- =====================================================
-- FASE A5: LOG DE CÁLCULO DE PREVISÃO (Auditoria)
-- =====================================================

CREATE TABLE IF NOT EXISTS log_calculo_previsao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo ENUM('orcamento', 'op', 'lote') NOT NULL,
    referencia_id INT NOT NULL COMMENT 'ID do orçamento, OP ou lote',
    data_calculo DATETIME DEFAULT CURRENT_TIMESTAMP,
    previsao_producao DATE NOT NULL,
    previsao_entrega DATE DEFAULT NULL,
    tempo_total_minutos INT DEFAULT 0,
    tempo_fila_minutos INT DEFAULT 0,
    dias_transporte INT DEFAULT 0,
    parametros_json TEXT COMMENT 'JSON com parâmetros usados no cálculo',
    created_by INT DEFAULT NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Log de cálculos de previsão para auditoria';

-- =====================================================
-- INSERIR JORNADA PADRÃO (Seg-Sex 08:00-17:30)
-- =====================================================

-- NOTA: Jornada de trabalho deve ser configurada em:
-- Menu Indústria > Jornada de Trabalho (módulo existente)

-- =====================================================
-- INSERIR FERIADOS NACIONAIS 2025/2026
-- NOTA: INSERT IGNORE não funciona com NULL em UNIQUE KEY
-- Usa INSERT ... SELECT ... WHERE NOT EXISTS para evitar duplicados
-- =====================================================

INSERT INTO config_feriados (empresa_id, data, descricao, tipo, recorrente_anual)
SELECT * FROM (
    SELECT NULL AS empresa_id, '2025-01-01' AS data, 'Confraternização Universal' AS descricao, 'feriado' AS tipo, 1 AS recorrente_anual UNION ALL
    SELECT NULL, '2025-03-03', 'Carnaval', 'feriado', 0 UNION ALL
    SELECT NULL, '2025-03-04', 'Carnaval', 'feriado', 0 UNION ALL
    SELECT NULL, '2025-04-18', 'Sexta-feira Santa', 'feriado', 0 UNION ALL
    SELECT NULL, '2025-04-21', 'Tiradentes', 'feriado', 1 UNION ALL
    SELECT NULL, '2025-05-01', 'Dia do Trabalho', 'feriado', 1 UNION ALL
    SELECT NULL, '2025-06-19', 'Corpus Christi', 'feriado', 0 UNION ALL
    SELECT NULL, '2025-09-07', 'Independência do Brasil', 'feriado', 1 UNION ALL
    SELECT NULL, '2025-10-12', 'Nossa Sra. Aparecida', 'feriado', 1 UNION ALL
    SELECT NULL, '2025-11-02', 'Finados', 'feriado', 1 UNION ALL
    SELECT NULL, '2025-11-15', 'Proclamação da República', 'feriado', 1 UNION ALL
    SELECT NULL, '2025-12-25', 'Natal', 'feriado', 1 UNION ALL
    SELECT NULL, '2026-01-01', 'Confraternização Universal', 'feriado', 1 UNION ALL
    SELECT NULL, '2026-02-16', 'Carnaval', 'feriado', 0 UNION ALL
    SELECT NULL, '2026-02-17', 'Carnaval', 'feriado', 0 UNION ALL
    SELECT NULL, '2026-04-03', 'Sexta-feira Santa', 'feriado', 0 UNION ALL
    SELECT NULL, '2026-04-21', 'Tiradentes', 'feriado', 1 UNION ALL
    SELECT NULL, '2026-05-01', 'Dia do Trabalho', 'feriado', 1 UNION ALL
    SELECT NULL, '2026-06-04', 'Corpus Christi', 'feriado', 0 UNION ALL
    SELECT NULL, '2026-09-07', 'Independência do Brasil', 'feriado', 1 UNION ALL
    SELECT NULL, '2026-10-12', 'Nossa Sra. Aparecida', 'feriado', 1 UNION ALL
    SELECT NULL, '2026-11-02', 'Finados', 'feriado', 1 UNION ALL
    SELECT NULL, '2026-11-15', 'Proclamação da República', 'feriado', 1 UNION ALL
    SELECT NULL, '2026-12-25', 'Natal', 'feriado', 1
) AS feriados_novos
WHERE NOT EXISTS (
    SELECT 1 FROM config_feriados cf 
    WHERE cf.empresa_id IS NULL AND cf.data = feriados_novos.data
);

-- =====================================================
-- VIEW: FILA DE PRODUÇÃO COMPLETA
-- =====================================================

CREATE OR REPLACE VIEW vw_fila_producao_completa AS
SELECT 
    l.id AS lote_id,
    l.ordem_producao_id,
    l.sequencia AS numero_lote,
    l.quantidade,
    l.etapa_atual_id,
    l.status_operador,
    COALESCE(l.prioridade, 5) AS prioridade,
    COALESCE(l.created_at, NOW()) AS data_chegada_etapa,
    e.nome AS etapa_nome,
    e.ordem AS etapa_ordem,
    op.numero_op,
    op.produto_id,
    p.name AS produto_nome,
    op.cliente_id,
    c.name AS cliente_nome,
    op.data_prevista AS op_data_prevista,
    -- Tempo na fila (minutos)
    TIMESTAMPDIFF(MINUTE, COALESCE(l.created_at, NOW()), NOW()) AS minutos_na_fila,
    -- Posição na fila da etapa (por prioridade e data)
    ROW_NUMBER() OVER (
        PARTITION BY l.etapa_atual_id 
        ORDER BY COALESCE(l.prioridade, 5) DESC, l.created_at ASC
    ) AS posicao_fila
FROM op_lotes l
JOIN producao_etapas e ON l.etapa_atual_id = e.id
JOIN ordens_producao op ON l.ordem_producao_id = op.id
JOIN products p ON op.produto_id = p.id
LEFT JOIN customers c ON op.cliente_id = c.id
WHERE l.status NOT IN ('concluido', 'cancelado')
ORDER BY e.ordem, COALESCE(l.prioridade, 5) DESC, l.created_at;

-- =====================================================
-- VIEW: RESUMO POR ETAPA (Gargalos)
-- =====================================================

CREATE OR REPLACE VIEW vw_resumo_etapas_producao AS
SELECT 
    e.id AS etapa_id,
    e.nome AS etapa_nome,
    e.ordem,
    COUNT(CASE WHEN l.status_operador = 'em_espera' THEN 1 END) AS qtd_aguardando,
    COUNT(CASE WHEN l.status_operador = 'em_producao' THEN 1 END) AS qtd_em_producao,
    COUNT(CASE WHEN l.status_operador = 'pausado' THEN 1 END) AS qtd_pausados,
    COUNT(l.id) AS qtd_total,
    -- Tempo médio na fila (minutos) - usa created_at pois data_chegada_etapa não existe
    AVG(CASE WHEN l.status_operador = 'em_espera' 
        THEN TIMESTAMPDIFF(MINUTE, l.created_at, NOW()) 
        END) AS tempo_medio_fila_minutos,
    -- Capacidade configurada
    COALESCE(cap.capacidade_diaria_lotes, 10) AS capacidade_diaria,
    COALESCE(cap.capacidade_simultanea, 1) AS capacidade_simultanea,
    -- Indicador de gargalo
    CASE 
        WHEN COUNT(CASE WHEN l.status_operador = 'em_espera' THEN 1 END) > COALESCE(cap.capacidade_diaria_lotes, 10) * 3 THEN 'critico'
        WHEN COUNT(CASE WHEN l.status_operador = 'em_espera' THEN 1 END) > COALESCE(cap.capacidade_diaria_lotes, 10) THEN 'atencao'
        ELSE 'normal'
    END AS status_gargalo
FROM producao_etapas e
LEFT JOIN op_lotes l ON l.etapa_atual_id = e.id AND l.status NOT IN ('concluido', 'cancelado')
LEFT JOIN config_capacidade_etapa cap ON cap.etapa_id = e.id AND cap.empresa_id IS NULL
WHERE e.ativo = 1
GROUP BY e.id, e.nome, e.ordem, cap.capacidade_diaria_lotes, cap.capacidade_simultanea
ORDER BY e.ordem;

-- =====================================================
-- FUNÇÃO: Calcular minutos úteis em um dia
-- Usa tabelas existentes: jornadas_trabalho + jornada_horarios
-- =====================================================

DELIMITER //

CREATE FUNCTION IF NOT EXISTS fn_minutos_uteis_dia(
    p_empresa_id INT,
    p_dia_semana_nome VARCHAR(10)  -- 'Segunda', 'Terça', etc
) RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE v_minutos INT DEFAULT 0;
    
    -- Soma minutos de todos os turnos do dia na jornada ativa da empresa
    SELECT COALESCE(SUM(
        CASE 
            WHEN jh.hora_fim > jh.hora_inicio THEN 
                TIMESTAMPDIFF(MINUTE, jh.hora_inicio, jh.hora_fim)
            ELSE 
                -- Turno que passa da meia-noite (ex: 22:00 às 06:00)
                TIMESTAMPDIFF(MINUTE, jh.hora_inicio, '24:00:00') + 
                TIMESTAMPDIFF(MINUTE, '00:00:00', jh.hora_fim)
        END
    ), 0)
    INTO v_minutos
    FROM jornadas_trabalho jt
    JOIN jornada_horarios jh ON jt.id = jh.jornada_id
    WHERE jt.empresa_id = p_empresa_id
      AND jt.ativo = 1
      AND jh.dia_semana = p_dia_semana_nome;
    
    RETURN v_minutos;
END //

DELIMITER ;

-- =====================================================
-- FUNÇÃO: Verificar se é dia útil
-- Usa tabelas existentes: jornadas_trabalho + jornada_horarios + config_feriados
-- =====================================================

DELIMITER //

CREATE FUNCTION IF NOT EXISTS fn_is_dia_util(
    p_empresa_id INT,
    p_data DATE
) RETURNS TINYINT
DETERMINISTIC
BEGIN
    DECLARE v_dia_semana_nome VARCHAR(10);
    DECLARE v_is_feriado TINYINT DEFAULT 0;
    DECLARE v_has_jornada TINYINT DEFAULT 0;
    
    -- Converter número do dia para nome em português
    SET v_dia_semana_nome = CASE DAYOFWEEK(p_data)
        WHEN 1 THEN 'Domingo'
        WHEN 2 THEN 'Segunda'
        WHEN 3 THEN 'Terça'
        WHEN 4 THEN 'Quarta'
        WHEN 5 THEN 'Quinta'
        WHEN 6 THEN 'Sexta'
        WHEN 7 THEN 'Sábado'
    END;
    
    -- Verificar se é feriado
    SELECT COUNT(*) INTO v_is_feriado
    FROM config_feriados
    WHERE (empresa_id = p_empresa_id OR empresa_id IS NULL)
      AND (data = p_data OR (recorrente_anual = 1 AND MONTH(data) = MONTH(p_data) AND DAY(data) = DAY(p_data)));
    
    IF v_is_feriado > 0 THEN
        RETURN 0;
    END IF;
    
    -- Verificar se tem jornada configurada para o dia
    SELECT COUNT(*) INTO v_has_jornada
    FROM jornadas_trabalho jt
    JOIN jornada_horarios jh ON jt.id = jh.jornada_id
    WHERE jt.empresa_id = p_empresa_id
      AND jt.ativo = 1
      AND jh.dia_semana = v_dia_semana_nome;
    
    RETURN v_has_jornada > 0;
END //

DELIMITER ;

-- =====================================================
-- STORED PROCEDURE: Calcular tempo médio histórico
-- =====================================================

DELIMITER //

CREATE PROCEDURE IF NOT EXISTS sp_calcular_tempos_historicos()
BEGIN
    -- Atualiza tempos médios baseado no log de etapas
    INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_medio_historico, tempo_minimo_historico, tempo_maximo_historico, qtd_amostras, ultima_atualizacao_historico)
    SELECT 
        op.produto_id,
        log.etapa_id,
        AVG(TIMESTAMPDIFF(MINUTE, log.inicio_producao, log.fim_producao)) AS tempo_medio,
        MIN(TIMESTAMPDIFF(MINUTE, log.inicio_producao, log.fim_producao)) AS tempo_minimo,
        MAX(TIMESTAMPDIFF(MINUTE, log.inicio_producao, log.fim_producao)) AS tempo_maximo,
        COUNT(*) AS qtd_amostras,
        NOW()
    FROM op_lotes_etapas_log log
    JOIN op_lotes l ON log.lote_id = l.id
    JOIN ordens_producao op ON l.ordem_producao_id = op.id
    WHERE log.fim_producao IS NOT NULL
      AND log.inicio_producao IS NOT NULL
      AND TIMESTAMPDIFF(MINUTE, log.inicio_producao, log.fim_producao) > 0
      AND TIMESTAMPDIFF(MINUTE, log.inicio_producao, log.fim_producao) < 1440 -- Máximo 24h
    GROUP BY op.produto_id, log.etapa_id
    ON DUPLICATE KEY UPDATE
        tempo_medio_historico = VALUES(tempo_medio_historico),
        tempo_minimo_historico = VALUES(tempo_minimo_historico),
        tempo_maximo_historico = VALUES(tempo_maximo_historico),
        qtd_amostras = VALUES(qtd_amostras),
        ultima_atualizacao_historico = NOW();
    
    SELECT ROW_COUNT() AS registros_atualizados;
END //

DELIMITER ;

-- =====================================================
-- VERIFICAÇÃO
-- =====================================================

SELECT 'Script 032 executado com sucesso!' AS status;

-- Mostrar tabelas criadas
SELECT 'Tabelas criadas:' AS info;
SHOW TABLES LIKE 'config_%';
SHOW TABLES LIKE 'produtos_tempo%';
SHOW TABLES LIKE 'log_calculo%';

-- Mostrar jornada de trabalho (usando tabelas existentes)
SELECT 'Jornadas de trabalho cadastradas:' AS info;
SELECT 
    jt.nome AS jornada,
    jh.dia_semana,
    jh.turno,
    jh.hora_inicio, 
    jh.hora_fim
FROM jornadas_trabalho jt
JOIN jornada_horarios jh ON jt.id = jh.jornada_id
WHERE jt.ativo = 1
ORDER BY jt.id, FIELD(jh.dia_semana, 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo');
