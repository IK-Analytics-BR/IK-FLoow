-- =====================================================
-- SCRIPT: Tabelas de Pausas/Paralizações de Produção
-- Data: 24/12/2025
-- =====================================================

-- =====================================================
-- TABELA: producao_pausas_motivos
-- Cadastro de motivos de pausa (produtivo/improdutivo)
-- =====================================================
CREATE TABLE IF NOT EXISTS producao_pausas_motivos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL COMMENT 'Nome do motivo (ex: Almoço, Setup, Banheiro)',
    descricao TEXT COMMENT 'Descrição detalhada',
    tipo ENUM('produtivo', 'improdutivo') NOT NULL DEFAULT 'improdutivo' COMMENT 'Tipo da pausa',
    icone VARCHAR(50) DEFAULT 'bi-pause-circle' COMMENT 'Ícone Bootstrap Icons',
    cor_hex VARCHAR(7) DEFAULT '#6c757d' COMMENT 'Cor para identificação visual',
    ativo TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_tipo (tipo),
    INDEX idx_ativo (ativo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Motivos de pausa/paralização da produção';

-- =====================================================
-- TABELA: producao_pausas
-- Registro de cada pausa do operador
-- =====================================================
CREATE TABLE IF NOT EXISTS producao_pausas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lote_id INT NOT NULL COMMENT 'Lote que foi pausado',
    ordem_producao_id INT NOT NULL COMMENT 'OP do lote',
    operador_id INT NOT NULL COMMENT 'Operador que pausou',
    motivo_id INT NOT NULL COMMENT 'Motivo da pausa',
    etapa_id INT COMMENT 'Etapa em que estava quando pausou',
    inicio DATETIME NOT NULL COMMENT 'Momento que iniciou a pausa',
    fim DATETIME COMMENT 'Momento que retomou (NULL = ainda pausado)',
    duracao_minutos INT COMMENT 'Duração em minutos (calculado ao retomar)',
    observacao TEXT COMMENT 'Observação opcional',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_pausa_lote FOREIGN KEY (lote_id) REFERENCES op_lotes(id) ON DELETE CASCADE,
    CONSTRAINT fk_pausa_op FOREIGN KEY (ordem_producao_id) REFERENCES ordens_producao(id) ON DELETE CASCADE,
    CONSTRAINT fk_pausa_operador FOREIGN KEY (operador_id) REFERENCES users(id),
    CONSTRAINT fk_pausa_motivo FOREIGN KEY (motivo_id) REFERENCES producao_pausas_motivos(id),
    CONSTRAINT fk_pausa_etapa FOREIGN KEY (etapa_id) REFERENCES producao_etapas(id),
    
    INDEX idx_lote (lote_id),
    INDEX idx_operador (operador_id),
    INDEX idx_motivo (motivo_id),
    INDEX idx_inicio (inicio),
    INDEX idx_fim (fim)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Registro de pausas/paralizações por lote';

-- =====================================================
-- DADOS INICIAIS: Motivos comuns
-- =====================================================
INSERT INTO producao_pausas_motivos (nome, descricao, tipo, icone, cor_hex) VALUES
-- Improdutivos
('Início de Jornada', 'Início do expediente de trabalho', 'produtivo', 'bi-sunrise', '#28a745'),
('Fim de Jornada', 'Encerramento do expediente', 'improdutivo', 'bi-sunset', '#dc3545'),
('Almoço', 'Intervalo para almoço', 'improdutivo', 'bi-cup-hot', '#fd7e14'),
('Lanche/Café', 'Intervalo para lanche ou café', 'improdutivo', 'bi-cup', '#ffc107'),
('Banheiro', 'Necessidade pessoal', 'improdutivo', 'bi-door-open', '#6c757d'),
('Aguardando Material', 'Esperando material para continuar', 'improdutivo', 'bi-box-seam', '#17a2b8'),
('Falta de Energia', 'Queda ou falta de energia elétrica', 'improdutivo', 'bi-lightning', '#343a40'),
-- Produtivos
('Setup de Máquina', 'Configuração/preparação da máquina', 'produtivo', 'bi-gear', '#0d6efd'),
('Troca de Ferramenta', 'Troca de ferramenta ou molde', 'produtivo', 'bi-tools', '#6610f2'),
('Manutenção Preventiva', 'Manutenção programada', 'produtivo', 'bi-wrench', '#20c997'),
('Manutenção Corretiva', 'Correção de problema na máquina', 'produtivo', 'bi-exclamation-triangle', '#e83e8c'),
('Correção de Qualidade', 'Ajuste para corrigir problema de qualidade', 'produtivo', 'bi-check2-square', '#6f42c1'),
('Limpeza de Máquina', 'Limpeza necessária do equipamento', 'produtivo', 'bi-droplet', '#0dcaf0');

-- =====================================================
-- VIEW: Resumo de pausas por operador
-- =====================================================
CREATE OR REPLACE VIEW vw_producao_pausas_resumo AS
SELECT 
    pp.operador_id,
    u.name AS operador_nome,
    DATE(pp.inicio) AS data,
    COUNT(*) AS total_pausas,
    SUM(CASE WHEN m.tipo = 'produtivo' THEN pp.duracao_minutos ELSE 0 END) AS minutos_produtivos,
    SUM(CASE WHEN m.tipo = 'improdutivo' THEN pp.duracao_minutos ELSE 0 END) AS minutos_improdutivos,
    SUM(pp.duracao_minutos) AS minutos_totais
FROM producao_pausas pp
INNER JOIN users u ON u.id = pp.operador_id
INNER JOIN producao_pausas_motivos m ON m.id = pp.motivo_id
WHERE pp.fim IS NOT NULL
GROUP BY pp.operador_id, DATE(pp.inicio);

-- =====================================================
-- VIEW: Tempo produtivo por lote
-- =====================================================
CREATE OR REPLACE VIEW vw_lote_tempo_producao AS
SELECT 
    l.id AS lote_id,
    l.ordem_producao_id,
    op.numero_op,
    l.quantidade,
    l.data_inicio_operador,
    l.data_fim_operador,
    TIMESTAMPDIFF(MINUTE, l.data_inicio_operador, COALESCE(l.data_fim_operador, NOW())) AS tempo_bruto_min,
    COALESCE((
        SELECT SUM(pp.duracao_minutos) 
        FROM producao_pausas pp 
        INNER JOIN producao_pausas_motivos m ON m.id = pp.motivo_id
        WHERE pp.lote_id = l.id AND m.tipo = 'improdutivo' AND pp.fim IS NOT NULL
    ), 0) AS pausas_improdutivas_min,
    COALESCE((
        SELECT SUM(pp.duracao_minutos) 
        FROM producao_pausas pp 
        INNER JOIN producao_pausas_motivos m ON m.id = pp.motivo_id
        WHERE pp.lote_id = l.id AND m.tipo = 'produtivo' AND pp.fim IS NOT NULL
    ), 0) AS pausas_produtivas_min,
    TIMESTAMPDIFF(MINUTE, l.data_inicio_operador, COALESCE(l.data_fim_operador, NOW())) 
        - COALESCE((
            SELECT SUM(pp.duracao_minutos) 
            FROM producao_pausas pp 
            INNER JOIN producao_pausas_motivos m ON m.id = pp.motivo_id
            WHERE pp.lote_id = l.id AND m.tipo = 'improdutivo' AND pp.fim IS NOT NULL
        ), 0) AS tempo_produtivo_min
FROM op_lotes l
INNER JOIN ordens_producao op ON op.id = l.ordem_producao_id
WHERE l.data_inicio_operador IS NOT NULL;

-- =====================================================
-- VIEW: Tempo médio por produto/etapa
-- =====================================================
CREATE OR REPLACE VIEW vw_tempo_medio_produto_etapa AS
SELECT 
    op.produto_id,
    p.name AS produto_nome,
    log.etapa_nova_id AS etapa_id,
    e.nome AS etapa_nome,
    COUNT(DISTINCT l.id) AS total_lotes,
    SUM(l.quantidade) AS total_unidades,
    AVG(vt.tempo_produtivo_min) AS tempo_medio_lote_min,
    CASE 
        WHEN SUM(l.quantidade) > 0 
        THEN SUM(vt.tempo_produtivo_min) / SUM(l.quantidade)
        ELSE 0 
    END AS tempo_medio_unitario_min
FROM op_lotes l
INNER JOIN ordens_producao op ON op.id = l.ordem_producao_id
INNER JOIN products p ON p.id = op.produto_id
INNER JOIN op_lotes_etapas_log log ON log.lote_id = l.id
INNER JOIN producao_etapas e ON e.id = log.etapa_nova_id
LEFT JOIN vw_lote_tempo_producao vt ON vt.lote_id = l.id
WHERE l.data_fim_operador IS NOT NULL
GROUP BY op.produto_id, log.etapa_nova_id;

-- =====================================================
-- FIM DO SCRIPT
-- =====================================================
