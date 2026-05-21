-- =====================================================
-- MÓDULO: LINHAS DE PRODUÇÃO + PLANEJAMENTO SEMANAL + OPs AUTOMÁTICAS
-- Script: 070_LINHAS_PRODUCAO_PLANEJAMENTO_SEMANAL.sql
-- Data: 06/02/2026
-- Descrição: Cria estrutura para linhas de produção de salgados,
--            planejamento semanal com geração automática de OPs
--            (massa, recheio, montagem/empacotamento) e cronograma
--            diário flexível por fases.
-- =====================================================

USE supply_chain_system;

-- =====================================================
-- TABELA 1: linhas_producao
-- Linhas de produção (equipamento + equipe)
-- Ex: LINHA BRALYX - 1 VIA, LINHA RISOLES - 1 VIA, LINHA ASSADOS - 1 VIA
-- =====================================================

CREATE TABLE IF NOT EXISTS linhas_producao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL COMMENT 'Nome da linha (ex: LINHA BRALYX - 1 VIA)',
    descricao TEXT COMMENT 'Descrição da linha, equipamentos, capacidade',
    ativo TINYINT(1) DEFAULT 1,
    capacidade_diaria_kg DECIMAL(10,2) COMMENT 'Capacidade diária estimada em kg',
    turno VARCHAR(50) DEFAULT '1º Turno' COMMENT 'Turno de operação',
    responsavel VARCHAR(100) COMMENT 'Líder/responsável da linha',
    cor_hex VARCHAR(7) DEFAULT '#007bff' COMMENT 'Cor para identificação visual',
    ordem INT DEFAULT 0 COMMENT 'Ordem de exibição',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ativo (ativo),
    INDEX idx_ordem (ordem)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Linhas de produção (equipamento + equipe)';


-- =====================================================
-- TABELA 2: linha_producao_produtos
-- Quais produtos cada linha pode produzir
-- =====================================================

CREATE TABLE IF NOT EXISTS linha_producao_produtos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    linha_id INT NOT NULL,
    produto_id INT NOT NULL COMMENT 'Produto final que esta linha produz',
    tempo_estimado_minutos INT COMMENT 'Tempo estimado por lote/batelada em minutos',
    prioridade INT DEFAULT 0 COMMENT 'Prioridade na linha (menor = mais prioritário)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_lpp_linha FOREIGN KEY (linha_id) REFERENCES linhas_producao(id) ON DELETE CASCADE,
    CONSTRAINT fk_lpp_produto FOREIGN KEY (produto_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE KEY uk_linha_produto (linha_id, produto_id),
    INDEX idx_linha (linha_id),
    INDEX idx_produto (produto_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Produtos que cada linha de produção pode fabricar';


-- =====================================================
-- TABELA 3: planejamentos_semanais
-- Cabeçalho do planejamento semanal (snapshot do que foi planejado)
-- =====================================================

CREATE TABLE IF NOT EXISTS planejamentos_semanais (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(30) NOT NULL UNIQUE COMMENT 'Código do planejamento (ex: PL-2026-S06)',
    semana_ano INT NOT NULL COMMENT 'Número da semana ISO (1-53)',
    ano INT NOT NULL COMMENT 'Ano',
    data_inicio DATE NOT NULL COMMENT 'Segunda-feira da semana',
    data_fim DATE NOT NULL COMMENT 'Sexta-feira (ou sábado) da semana',
    status ENUM('rascunho', 'confirmado', 'em_producao', 'concluido', 'cancelado')
        NOT NULL DEFAULT 'rascunho',
    observacoes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT COMMENT 'Usuário que criou',
    confirmado_por INT COMMENT 'Usuário que confirmou',
    confirmado_em DATETIME COMMENT 'Data/hora da confirmação',
    INDEX idx_semana (ano, semana_ano),
    INDEX idx_status (status),
    INDEX idx_datas (data_inicio, data_fim)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Planejamentos semanais de produção';


-- =====================================================
-- TABELA 4: planejamento_semanal_itens
-- Itens do planejamento (1 linha por pacote planejado)
-- =====================================================

CREATE TABLE IF NOT EXISTS planejamento_semanal_itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    planejamento_id INT NOT NULL,
    pacote_id INT NOT NULL COMMENT 'ID do produto_pacote planejado',
    produto_id INT NOT NULL COMMENT 'ID do produto final',
    qtd_pacotes DECIMAL(15,4) NOT NULL COMMENT 'Quantidade em pacotes',
    qtd_unidades DECIMAL(15,4) NOT NULL COMMENT 'Quantidade convertida em unidades',
    estoque_atual_pacotes DECIMAL(15,4) DEFAULT 0 COMMENT 'Snapshot do estoque no momento do planejamento',
    previsao_vendas_pacotes DECIMAL(15,4) DEFAULT 0 COMMENT 'Snapshot da previsão de vendas',
    sugestao_pacotes DECIMAL(15,4) DEFAULT 0 COMMENT 'Snapshot da sugestão calculada',
    linha_producao_id INT COMMENT 'Linha de produção atribuída',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_psi_planejamento FOREIGN KEY (planejamento_id)
        REFERENCES planejamentos_semanais(id) ON DELETE CASCADE,
    CONSTRAINT fk_psi_produto FOREIGN KEY (produto_id)
        REFERENCES products(id) ON DELETE RESTRICT,
    CONSTRAINT fk_psi_linha FOREIGN KEY (linha_producao_id)
        REFERENCES linhas_producao(id) ON DELETE SET NULL,
    INDEX idx_planejamento (planejamento_id),
    INDEX idx_produto (produto_id),
    INDEX idx_linha (linha_producao_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Itens do planejamento semanal (pacotes planejados)';


-- =====================================================
-- TABELA 5: planejamento_semanal_ops
-- OPs geradas a partir de um planejamento semanal
-- =====================================================

CREATE TABLE IF NOT EXISTS planejamento_semanal_ops (
    id INT AUTO_INCREMENT PRIMARY KEY,
    planejamento_id INT NOT NULL,
    ordem_producao_id INT NOT NULL,
    tipo_op_planejamento ENUM('massa', 'recheio', 'montagem', 'empacotamento')
        NOT NULL COMMENT 'Tipo da OP no contexto do planejamento',
    produto_semiacabado_id INT COMMENT 'ID do semiacabado (massa/recheio) se aplicável',
    linha_producao_id INT COMMENT 'Linha de produção atribuída',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pso_planejamento FOREIGN KEY (planejamento_id)
        REFERENCES planejamentos_semanais(id) ON DELETE CASCADE,
    CONSTRAINT fk_pso_op FOREIGN KEY (ordem_producao_id)
        REFERENCES ordens_producao(id) ON DELETE CASCADE,
    CONSTRAINT fk_pso_linha FOREIGN KEY (linha_producao_id)
        REFERENCES linhas_producao(id) ON DELETE SET NULL,
    INDEX idx_planejamento (planejamento_id),
    INDEX idx_op (ordem_producao_id),
    INDEX idx_tipo (tipo_op_planejamento)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Vínculo entre planejamento semanal e OPs geradas';


-- =====================================================
-- TABELA 6: op_fases_producao
-- Fases de cada OP com atribuição flexível por dia da semana
-- Permite ao usuário distribuir a produção ao longo da semana
-- Ex: Seg=preparar massa, Ter=resfriar, Qua=montar, Qui=empacotar
-- =====================================================

CREATE TABLE IF NOT EXISTS op_fases_producao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ordem_producao_id INT NOT NULL,
    fase_nome VARCHAR(100) NOT NULL COMMENT 'Nome da fase (ex: Preparar Massa, Resfriar, Montar, Empacotar)',
    fase_tipo ENUM('preparacao', 'cozimento', 'resfriamento', 'montagem', 'empacotamento', 'outro')
        NOT NULL DEFAULT 'outro',
    sequencia INT NOT NULL DEFAULT 1 COMMENT 'Ordem da fase dentro da OP',
    dia_semana DATE COMMENT 'Dia atribuído para esta fase (flexível, editável)',
    hora_inicio TIME COMMENT 'Hora prevista de início',
    hora_fim TIME COMMENT 'Hora prevista de término',
    quantidade DECIMAL(15,4) COMMENT 'Quantidade a produzir nesta fase (pode ser parcial)',
    quantidade_realizada DECIMAL(15,4) DEFAULT 0 COMMENT 'Quantidade efetivamente produzida',
    status ENUM('pendente', 'em_andamento', 'concluida', 'cancelada')
        NOT NULL DEFAULT 'pendente',
    linha_producao_id INT COMMENT 'Linha de produção para esta fase',
    observacoes TEXT,
    dependencia_fase_id INT COMMENT 'ID da fase que precisa ser concluída antes desta',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_opf_op FOREIGN KEY (ordem_producao_id)
        REFERENCES ordens_producao(id) ON DELETE CASCADE,
    CONSTRAINT fk_opf_linha FOREIGN KEY (linha_producao_id)
        REFERENCES linhas_producao(id) ON DELETE SET NULL,
    CONSTRAINT fk_opf_dependencia FOREIGN KEY (dependencia_fase_id)
        REFERENCES op_fases_producao(id) ON DELETE SET NULL,
    INDEX idx_op (ordem_producao_id),
    INDEX idx_dia (dia_semana),
    INDEX idx_status (status),
    INDEX idx_linha (linha_producao_id),
    INDEX idx_sequencia (ordem_producao_id, sequencia)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Fases de produção por OP com cronograma diário flexível';


-- =====================================================
-- AJUSTES NA TABELA ordens_producao
-- Adicionar campos para suportar o novo fluxo de salgados
-- =====================================================

-- Permitir cliente_id NULL (produção para estoque, sem cliente específico)
SET @col_nullable = (SELECT IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ordens_producao' AND COLUMN_NAME = 'cliente_id');
SET @sql_nullable = IF(@col_nullable = 'NO',
    'ALTER TABLE ordens_producao MODIFY COLUMN cliente_id INT NULL COMMENT ''Cliente (NULL para produção para estoque)''',
    'SELECT ''cliente_id já é nullable''');
PREPARE stmt_n FROM @sql_nullable;
EXECUTE stmt_n;
DEALLOCATE PREPARE stmt_n;

-- Adicionar linha_producao_id
SET @col_exists_lp = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ordens_producao' AND COLUMN_NAME = 'linha_producao_id');
SET @sql_lp = IF(@col_exists_lp = 0,
    'ALTER TABLE ordens_producao ADD COLUMN linha_producao_id INT NULL COMMENT ''Linha de produção atribuída'' AFTER template_usado_id',
    'SELECT ''Coluna linha_producao_id já existe''');
PREPARE stmt_lp FROM @sql_lp;
EXECUTE stmt_lp;
DEALLOCATE PREPARE stmt_lp;

-- Adicionar planejamento_id (referência ao planejamento que gerou esta OP)
SET @col_exists_pl = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ordens_producao' AND COLUMN_NAME = 'planejamento_id');
SET @sql_pl = IF(@col_exists_pl = 0,
    'ALTER TABLE ordens_producao ADD COLUMN planejamento_id INT NULL COMMENT ''Planejamento semanal que originou esta OP'' AFTER linha_producao_id',
    'SELECT ''Coluna planejamento_id já existe''');
PREPARE stmt_pl FROM @sql_pl;
EXECUTE stmt_pl;
DEALLOCATE PREPARE stmt_pl;

-- Expandir ENUM tipo_op para incluir novos tipos
SET @col_exists_tipo = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ordens_producao' AND COLUMN_NAME = 'tipo_op');
SET @sql_tipo = IF(@col_exists_tipo > 0,
    'ALTER TABLE ordens_producao MODIFY COLUMN tipo_op ENUM(''producao'', ''separacao'', ''mista'', ''massa'', ''recheio'', ''montagem'', ''empacotamento'') DEFAULT ''producao'' COMMENT ''Tipo da OP''',
    'ALTER TABLE ordens_producao ADD COLUMN tipo_op ENUM(''producao'', ''separacao'', ''mista'', ''massa'', ''recheio'', ''montagem'', ''empacotamento'') DEFAULT ''producao'' COMMENT ''Tipo da OP''');
PREPARE stmt_tipo FROM @sql_tipo;
EXECUTE stmt_tipo;
DEALLOCATE PREPARE stmt_tipo;


-- =====================================================
-- DADOS INICIAIS: Linhas de Produção
-- =====================================================

INSERT IGNORE INTO linhas_producao (id, nome, descricao, ativo, cor_hex, ordem) VALUES
(1, 'LINHA BRALYX - 1 VIA',
    'Linha principal de salgados fritos e assados. Equipamento Bralyx para modelagem automática.',
    1, '#007bff', 1),
(2, 'LINHA RISOLES - 1 VIA',
    'Linha dedicada a risoles, bolinhos e espetos. Processo semi-manual.',
    1, '#28a745', 2),
(3, 'LINHA ASSADOS - 1 VIA',
    'Linha de assados (x-burguer, esfiha, bauru, etc). Forno industrial.',
    1, '#ffc107', 3);


-- =====================================================
-- DADOS INICIAIS: Produtos por Linha de Produção
-- Vincula cada produto final à sua linha correspondente
-- =====================================================

-- LINHA BRALYX (id=1): Coxinhas, Croquetes, Enroladinhos, Quibes, Churros, Bolinhas
INSERT IGNORE INTO linha_producao_produtos (linha_id, produto_id, prioridade)
SELECT 1, p.id, 0
FROM products p
WHERE p.active = 1
  AND (
    p.name LIKE 'COXINHA%CARNE%140%' OR
    p.name LIKE 'COXINHA%CARNE%70%' OR
    p.name LIKE '%MINI%COXINHA%CARNE%20%' OR
    p.name LIKE 'COXINHA%FRANGO%140%' OR
    p.name LIKE 'COXINHA%FRANGO%70%' OR
    p.name LIKE '%MINI%COXINHA%FRANGO%20%' OR
    p.name LIKE 'COXINHA%CARNE SECA%' OR
    p.name LIKE '%MINI%CROQUETE%SECA%20%' OR
    p.name LIKE 'ENROL%PRES%QUEIJO%140%' OR
    p.name LIKE '%MINI%ENROL%PRES%QUEIJO%20%' OR
    p.name LIKE 'ENROLAD%SALSICHA%140%' OR
    p.name LIKE '%MINI%ENROLAD%SALSICHA%20%' OR
    p.name LIKE 'QUIBE%CARNE%130%' OR
    p.name LIKE '%MINI%QUIBE%CARNE%20%' OR
    p.name LIKE '%MINI%CHURROS%20%' OR
    p.name LIKE '%MINI%BOLINHA%QUEIJO%20%' OR
    p.name LIKE 'CROQUETE%CARNE SECA%20%'
  )
  AND p.name NOT LIKE 'MASSA -%'
  AND p.name NOT LIKE 'RECHEIO -%';

-- LINHA RISOLES (id=2): Risoles, Bolinhos, Espetos
INSERT IGNORE INTO linha_producao_produtos (linha_id, produto_id, prioridade)
SELECT 2, p.id, 0
FROM products p
WHERE p.active = 1
  AND (
    p.name LIKE 'RISOL%CARNE%' OR
    p.name LIKE 'RISOL%FRANGO%' OR
    p.name LIKE 'RISOL%PIZZA%' OR
    p.name LIKE 'BOLINHO%CARNE%130%' OR
    p.name LIKE 'ESPETO%FRANGO%'
  )
  AND p.name NOT LIKE 'MASSA -%'
  AND p.name NOT LIKE 'RECHEIO -%';

-- LINHA ASSADOS (id=3): X-Burguer, Esfiha, Bauru, Mistinho, Italianinho
INSERT IGNORE INTO linha_producao_produtos (linha_id, produto_id, prioridade)
SELECT 3, p.id, 0
FROM products p
WHERE p.active = 1
  AND (
    p.name LIKE 'X-BURGUER%' OR
    p.name LIKE 'X- BURGUER%' OR
    p.name LIKE 'X-DUPLO%' OR
    p.name LIKE 'X- DUPLO%' OR
    p.name LIKE 'ESFIHA%' OR
    p.name LIKE 'BAURU%' OR
    p.name LIKE 'MISTINHO%' OR
    p.name LIKE 'ITALIANINHO%'
  )
  AND p.name NOT LIKE 'MASSA -%'
  AND p.name NOT LIKE 'RECHEIO -%';


-- =====================================================
-- TABELA 7: lote_consumo_insumos
-- Controle de retirada de insumos pelo operador durante produção.
-- Ex: operador pega 1 caixa de hambúrguer (100un), registra aqui.
-- Ao finalizar o lote, compara total retirado vs produzido → perda.
-- =====================================================

CREATE TABLE IF NOT EXISTS lote_consumo_insumos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lote_id INT NOT NULL COMMENT 'ID do op_lotes em produção',
    ordem_producao_id INT NOT NULL COMMENT 'ID da OP (denormalizado para consultas rápidas)',
    insumo_produto_id INT NOT NULL COMMENT 'ID do produto/insumo retirado (ex: caixa de hambúrguer)',
    quantidade_retirada DECIMAL(15,4) NOT NULL COMMENT 'Quantidade retirada (ex: 1 caixa = 100 unidades)',
    unidade_medida VARCHAR(20) COMMENT 'Unidade (UN, CX, KG, etc)',
    unidades_por_embalagem DECIMAL(15,4) DEFAULT 1 COMMENT 'Quantas unidades tem na embalagem (ex: 100 un/caixa)',
    total_unidades DECIMAL(15,4) GENERATED ALWAYS AS (quantidade_retirada * unidades_por_embalagem) STORED
        COMMENT 'Total de unidades retiradas (calculado)',
    motivo ENUM('producao', 'reposicao', 'perda_acidental', 'defeito', 'outro')
        NOT NULL DEFAULT 'producao' COMMENT 'Motivo da retirada',
    observacao TEXT COMMENT 'Observação livre (ex: caiu no chão, embalagem danificada)',
    operador_id INT NOT NULL COMMENT 'Operador que registrou a retirada',
    registrado_em DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Data/hora do registro',
    CONSTRAINT fk_lci_lote FOREIGN KEY (lote_id) REFERENCES op_lotes(id) ON DELETE CASCADE,
    CONSTRAINT fk_lci_op FOREIGN KEY (ordem_producao_id) REFERENCES ordens_producao(id) ON DELETE CASCADE,
    CONSTRAINT fk_lci_insumo FOREIGN KEY (insumo_produto_id) REFERENCES products(id) ON DELETE RESTRICT,
    CONSTRAINT fk_lci_operador FOREIGN KEY (operador_id) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_lote (lote_id),
    INDEX idx_op (ordem_producao_id),
    INDEX idx_insumo (insumo_produto_id),
    INDEX idx_operador (operador_id),
    INDEX idx_motivo (motivo),
    INDEX idx_data (registrado_em)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Registro de retirada de insumos pelo operador durante produção de um lote';


-- =====================================================
-- TABELA 8: lote_consumo_conferencia
-- Conferência final do lote: compara insumos retirados vs produzido.
-- Se não bater → registra perda. Líder pode avaliar operador.
-- =====================================================

CREATE TABLE IF NOT EXISTS lote_consumo_conferencia (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lote_id INT NOT NULL COMMENT 'ID do op_lotes finalizado',
    ordem_producao_id INT NOT NULL,

    -- Totais calculados
    total_insumos_retirados DECIMAL(15,4) NOT NULL DEFAULT 0
        COMMENT 'Total de unidades de insumo retiradas (soma de lote_consumo_insumos.total_unidades)',
    total_produzido DECIMAL(15,4) NOT NULL DEFAULT 0
        COMMENT 'Total de unidades efetivamente produzidas',
    total_perda DECIMAL(15,4) NOT NULL DEFAULT 0
        COMMENT 'Diferença: retirado - produzido (se > 0, houve perda)',
    percentual_perda DECIMAL(8,4) DEFAULT 0
        COMMENT 'Percentual de perda: (perda / retirado) * 100',

    -- Classificação da perda
    perda_aceitavel TINYINT(1) DEFAULT 1
        COMMENT '1 = dentro da tolerância, 0 = acima da tolerância',
    tolerancia_percentual DECIMAL(8,4) DEFAULT 2.0000
        COMMENT 'Tolerância configurada no momento da conferência (%)',

    -- Avaliação do líder
    avaliacao_lider ENUM('aprovado', 'atencao', 'reprovado') DEFAULT NULL
        COMMENT 'Avaliação do líder sobre o desempenho do operador neste lote',
    observacao_lider TEXT COMMENT 'Comentário do líder',

    -- Quem conferiu
    operador_id INT COMMENT 'Operador responsável pelo lote',
    conferido_por INT COMMENT 'Líder/supervisor que conferiu',
    conferido_em DATETIME COMMENT 'Data/hora da conferência',

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_lcc_lote FOREIGN KEY (lote_id) REFERENCES op_lotes(id) ON DELETE CASCADE,
    CONSTRAINT fk_lcc_op FOREIGN KEY (ordem_producao_id) REFERENCES ordens_producao(id) ON DELETE CASCADE,
    CONSTRAINT fk_lcc_operador FOREIGN KEY (operador_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_lcc_conferente FOREIGN KEY (conferido_por) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE KEY uk_lote_conferencia (lote_id),
    INDEX idx_op (ordem_producao_id),
    INDEX idx_operador (operador_id),
    INDEX idx_perda (perda_aceitavel),
    INDEX idx_avaliacao (avaliacao_lider)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Conferência final de lote: insumos retirados vs produzido, controle de perda';


-- =====================================================
-- DADOS INICIAIS: Grupos de Etapas para Salgados
-- Reutiliza producao_etapas_grupos existente
-- =====================================================

INSERT INTO producao_etapas_grupos (nome, ordem, ativo, cor_hex, descricao)
SELECT 'Preparação', 10, 1, '#6f42c1', 'Preparo de massas e recheios'
FROM DUAL WHERE NOT EXISTS (
    SELECT 1 FROM producao_etapas_grupos WHERE nome = 'Preparação'
);

INSERT INTO producao_etapas_grupos (nome, ordem, ativo, cor_hex, descricao)
SELECT 'Produção / Montagem', 20, 1, '#007bff', 'Montagem e modelagem dos salgados nas linhas'
FROM DUAL WHERE NOT EXISTS (
    SELECT 1 FROM producao_etapas_grupos WHERE nome = 'Produção / Montagem'
);

INSERT INTO producao_etapas_grupos (nome, ordem, ativo, cor_hex, descricao)
SELECT 'Empacotamento', 30, 1, '#28a745', 'Empacotamento e selagem dos produtos'
FROM DUAL WHERE NOT EXISTS (
    SELECT 1 FROM producao_etapas_grupos WHERE nome = 'Empacotamento'
);

INSERT INTO producao_etapas_grupos (nome, ordem, ativo, cor_hex, descricao)
SELECT 'Congelamento / Estoque', 40, 1, '#17a2b8', 'Congelamento e entrada no estoque'
FROM DUAL WHERE NOT EXISTS (
    SELECT 1 FROM producao_etapas_grupos WHERE nome = 'Congelamento / Estoque'
);


-- =====================================================
-- DADOS INICIAIS: Etapas para fluxo de Salgados
-- Reutiliza producao_etapas existente
-- =====================================================

-- Grupo: Preparação
INSERT INTO producao_etapas (nome, ordem, ativo, cor_hex, icone, descricao, grupo_etapas_id)
SELECT 'Preparar Massa', 11, 1, '#9b59b6', 'fa-blender', 'Mistura e preparo da massa',
       (SELECT id FROM producao_etapas_grupos WHERE nome = 'Preparação' LIMIT 1)
FROM DUAL WHERE NOT EXISTS (
    SELECT 1 FROM producao_etapas WHERE nome = 'Preparar Massa'
);

INSERT INTO producao_etapas (nome, ordem, ativo, cor_hex, icone, descricao, grupo_etapas_id)
SELECT 'Cozinhar Massa', 12, 1, '#e74c3c', 'fa-fire', 'Cozimento da massa',
       (SELECT id FROM producao_etapas_grupos WHERE nome = 'Preparação' LIMIT 1)
FROM DUAL WHERE NOT EXISTS (
    SELECT 1 FROM producao_etapas WHERE nome = 'Cozinhar Massa'
);

INSERT INTO producao_etapas (nome, ordem, ativo, cor_hex, icone, descricao, grupo_etapas_id)
SELECT 'Resfriar Massa', 13, 1, '#3498db', 'fa-snowflake', 'Resfriamento da massa antes da montagem',
       (SELECT id FROM producao_etapas_grupos WHERE nome = 'Preparação' LIMIT 1)
FROM DUAL WHERE NOT EXISTS (
    SELECT 1 FROM producao_etapas WHERE nome = 'Resfriar Massa'
);

INSERT INTO producao_etapas (nome, ordem, ativo, cor_hex, icone, descricao, grupo_etapas_id)
SELECT 'Preparar Recheio', 14, 1, '#e67e22', 'fa-mortar-pestle', 'Preparo e cozimento do recheio',
       (SELECT id FROM producao_etapas_grupos WHERE nome = 'Preparação' LIMIT 1)
FROM DUAL WHERE NOT EXISTS (
    SELECT 1 FROM producao_etapas WHERE nome = 'Preparar Recheio'
);

-- Grupo: Produção / Montagem
INSERT INTO producao_etapas (nome, ordem, ativo, cor_hex, icone, descricao, grupo_etapas_id)
SELECT 'Montagem / Modelagem', 21, 1, '#2980b9', 'fa-hands', 'Montagem dos salgados na linha de produção',
       (SELECT id FROM producao_etapas_grupos WHERE nome = 'Produção / Montagem' LIMIT 1)
FROM DUAL WHERE NOT EXISTS (
    SELECT 1 FROM producao_etapas WHERE nome = 'Montagem / Modelagem'
);

INSERT INTO producao_etapas (nome, ordem, ativo, cor_hex, icone, descricao, grupo_etapas_id)
SELECT 'Pré-fritura / Forno', 22, 1, '#d35400', 'fa-temperature-high', 'Pré-fritura ou assamento conforme tipo do produto',
       (SELECT id FROM producao_etapas_grupos WHERE nome = 'Produção / Montagem' LIMIT 1)
FROM DUAL WHERE NOT EXISTS (
    SELECT 1 FROM producao_etapas WHERE nome = 'Pré-fritura / Forno'
);

-- Grupo: Empacotamento
INSERT INTO producao_etapas (nome, ordem, ativo, cor_hex, icone, descricao, grupo_etapas_id)
SELECT 'Empacotamento', 31, 1, '#27ae60', 'fa-box', 'Empacotamento e selagem',
       (SELECT id FROM producao_etapas_grupos WHERE nome = 'Empacotamento' LIMIT 1)
FROM DUAL WHERE NOT EXISTS (
    SELECT 1 FROM producao_etapas WHERE nome = 'Empacotamento'
);

-- Grupo: Congelamento / Estoque
INSERT INTO producao_etapas (nome, ordem, ativo, cor_hex, icone, descricao, grupo_etapas_id)
SELECT 'Congelamento', 41, 1, '#2c3e50', 'fa-temperature-low', 'Congelamento do produto final',
       (SELECT id FROM producao_etapas_grupos WHERE nome = 'Congelamento / Estoque' LIMIT 1)
FROM DUAL WHERE NOT EXISTS (
    SELECT 1 FROM producao_etapas WHERE nome = 'Congelamento'
);

INSERT INTO producao_etapas (nome, ordem, ativo, cor_hex, icone, descricao, grupo_etapas_id)
SELECT 'Entrada Estoque', 42, 1, '#16a085', 'fa-warehouse', 'Produto pronto para inclusão no estoque',
       (SELECT id FROM producao_etapas_grupos WHERE nome = 'Congelamento / Estoque' LIMIT 1)
FROM DUAL WHERE NOT EXISTS (
    SELECT 1 FROM producao_etapas WHERE nome = 'Entrada Estoque'
);


-- =====================================================
-- VIEW: Resumo do planejamento semanal
-- =====================================================

CREATE OR REPLACE VIEW vw_planejamento_semanal_resumo AS
SELECT
    ps.id,
    ps.codigo,
    ps.semana_ano,
    ps.ano,
    ps.data_inicio,
    ps.data_fim,
    ps.status,
    ps.created_at,
    ps.confirmado_em,
    COUNT(DISTINCT psi.id) AS total_itens,
    COUNT(DISTINCT pso.id) AS total_ops,
    COALESCE(SUM(psi.qtd_pacotes), 0) AS total_pacotes,
    COALESCE(SUM(psi.qtd_unidades), 0) AS total_unidades
FROM planejamentos_semanais ps
LEFT JOIN planejamento_semanal_itens psi ON psi.planejamento_id = ps.id
LEFT JOIN planejamento_semanal_ops pso ON pso.planejamento_id = ps.id
GROUP BY ps.id
ORDER BY ps.ano DESC, ps.semana_ano DESC;


-- =====================================================
-- VIEW: Cronograma semanal (fases por dia)
-- =====================================================

CREATE OR REPLACE VIEW vw_cronograma_semanal AS
SELECT
    f.id AS fase_id,
    f.ordem_producao_id,
    op.numero_op,
    op.tipo_op,
    p.name AS produto_nome,
    f.fase_nome,
    f.fase_tipo,
    f.sequencia,
    f.dia_semana,
    f.hora_inicio,
    f.hora_fim,
    f.quantidade,
    f.quantidade_realizada,
    f.status AS fase_status,
    f.linha_producao_id,
    lp.nome AS linha_nome,
    lp.cor_hex AS linha_cor,
    op.status AS op_status,
    op.planejamento_id,
    ps.codigo AS planejamento_codigo
FROM op_fases_producao f
INNER JOIN ordens_producao op ON op.id = f.ordem_producao_id
INNER JOIN products p ON p.id = op.produto_id
LEFT JOIN linhas_producao lp ON lp.id = f.linha_producao_id
LEFT JOIN planejamentos_semanais ps ON ps.id = op.planejamento_id
ORDER BY f.dia_semana, f.hora_inicio, f.sequencia;


-- =====================================================
-- ADICIONAR COLUNA prioridade em ordens_producao
-- Para marcar urgência ao gerar OPs do planejamento
-- =====================================================

ALTER TABLE ordens_producao
    ADD COLUMN IF NOT EXISTS prioridade ENUM('normal','urgente','atencao') DEFAULT 'normal'
    COMMENT 'Prioridade da OP (urgente = estoque crítico, atencao = estoque baixo)';


-- =====================================================
-- CORRIGIR VIEW: vw_ordens_producao_resumo
-- A view original usa INNER JOIN customers, o que exclui
-- OPs de produção para estoque (sem cliente_id).
-- Alteramos para LEFT JOIN para que todas as OPs apareçam.
-- =====================================================

CREATE OR REPLACE VIEW vw_ordens_producao_resumo AS
SELECT 
    op.id,
    op.numero_op,
    e.nome_fantasia AS empresa_nome,
    COALESCE(c.name, '(Produção p/ Estoque)') AS cliente_nome,
    p.name AS produto_nome,
    op.quantidade,
    op.status,
    op.data_solicitacao,
    op.data_prevista,
    op.data_conclusao,
    op.custo_total_atual,
    op.usou_template,
    CASE 
        WHEN op.usou_template = 1 THEN CONCAT('v', t.versao)
        ELSE 'Manual'
    END AS template_info,
    op.variacao_custo_percentual,
    op.created_at
FROM ordens_producao op
INNER JOIN empresas e ON op.empresa_id = e.id
LEFT JOIN customers c ON op.cliente_id = c.id
INNER JOIN products p ON op.produto_id = p.id
LEFT JOIN produto_templates_producao t ON op.template_usado_id = t.id
ORDER BY op.created_at DESC;


-- =====================================================
-- FIM DO SCRIPT
-- =====================================================
