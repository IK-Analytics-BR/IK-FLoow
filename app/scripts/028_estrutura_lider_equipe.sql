-- =====================================================
-- ESTRUTURA DE LÍDER DE EQUIPE E VÍNCULOS
-- Script: 028_estrutura_lider_equipe.sql
-- Data: 24/12/2024
-- Descrição: Cria estrutura para líder de equipe controlar
--            operadores e atribuir OPs com prioridade
-- =====================================================

USE supply_chain_system;

-- =====================================================
-- 1. ADICIONAR CAMPO DE LÍDER NO USUÁRIO
-- =====================================================

ALTER TABLE users 
ADD COLUMN eh_lider_equipe TINYINT(1) DEFAULT 0
COMMENT 'Indica se o usuário é líder de equipe de produção';

CREATE INDEX idx_users_lider ON users(eh_lider_equipe);

-- =====================================================
-- 2. TABELA DE VÍNCULO: LÍDER -> OPERADORES (sua equipe)
-- =====================================================

CREATE TABLE IF NOT EXISTS lider_operadores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lider_id INT NOT NULL COMMENT 'ID do líder de equipe',
    operador_id INT NOT NULL COMMENT 'ID do operador da equipe',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_lider_operador (lider_id, operador_id),
    FOREIGN KEY (lider_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (operador_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Vínculo entre líder e seus operadores';

-- =====================================================
-- 3. TABELA DE VÍNCULO: LÍDER -> ETAPAS (seu setor)
-- =====================================================

CREATE TABLE IF NOT EXISTS lider_etapas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lider_id INT NOT NULL COMMENT 'ID do líder de equipe',
    etapa_id INT NOT NULL COMMENT 'ID da etapa que o líder controla',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_lider_etapa (lider_id, etapa_id),
    FOREIGN KEY (lider_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (etapa_id) REFERENCES producao_etapas(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Vínculo entre líder e as etapas que ele controla';

-- =====================================================
-- 4. TABELA DE VÍNCULO: ETAPA -> MÚLTIPLOS OPERADORES
-- =====================================================

CREATE TABLE IF NOT EXISTS etapa_operadores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    etapa_id INT NOT NULL COMMENT 'ID da etapa',
    operador_id INT NOT NULL COMMENT 'ID do operador que pode trabalhar nesta etapa',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_etapa_operador (etapa_id, operador_id),
    FOREIGN KEY (etapa_id) REFERENCES producao_etapas(id) ON DELETE CASCADE,
    FOREIGN KEY (operador_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Vínculo entre etapa e operadores que podem trabalhar nela';

-- =====================================================
-- 5. ADICIONAR CAMPOS DE ATRIBUIÇÃO EM OP_LOTES
-- =====================================================

-- Prioridade definida pelo líder (1=Urgente, 2=Alta, 3=Normal, 4=Baixa)
ALTER TABLE op_lotes 
ADD COLUMN prioridade INT DEFAULT 3
COMMENT 'Prioridade: 1=Urgente, 2=Alta, 3=Normal, 4=Baixa';

-- Operador designado pelo líder para este lote
ALTER TABLE op_lotes 
ADD COLUMN operador_designado_id INT NULL
COMMENT 'Operador designado pelo líder para realizar este lote';

-- Data que o líder atribuiu ao operador
ALTER TABLE op_lotes 
ADD COLUMN data_atribuicao DATETIME NULL
COMMENT 'Data/hora que o líder atribuiu o lote ao operador';

-- Líder que fez a atribuição
ALTER TABLE op_lotes 
ADD COLUMN atribuido_por_id INT NULL
COMMENT 'ID do líder que fez a atribuição';

-- Índices
CREATE INDEX idx_op_lotes_prioridade ON op_lotes(prioridade);
CREATE INDEX idx_op_lotes_operador_designado ON op_lotes(operador_designado_id);

-- Foreign Keys
ALTER TABLE op_lotes 
ADD CONSTRAINT fk_op_lotes_operador_designado 
FOREIGN KEY (operador_designado_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE op_lotes 
ADD CONSTRAINT fk_op_lotes_atribuido_por 
FOREIGN KEY (atribuido_por_id) REFERENCES users(id) ON DELETE SET NULL;

-- =====================================================
-- 6. VIEW: EQUIPE DO LÍDER COM ESTATÍSTICAS
-- =====================================================

CREATE OR REPLACE VIEW vw_lider_equipe AS
SELECT 
    lo.lider_id,
    u_lider.name AS lider_nome,
    lo.operador_id,
    u_op.name AS operador_nome,
    u_op.username AS operador_username,
    (SELECT COUNT(*) FROM op_lotes ol WHERE ol.operador_designado_id = lo.operador_id AND ol.status_operador = 'em_espera') AS lotes_em_espera,
    (SELECT COUNT(*) FROM op_lotes ol WHERE ol.operador_designado_id = lo.operador_id AND ol.status_operador = 'em_producao') AS lotes_em_producao,
    (SELECT COUNT(*) FROM op_lotes ol WHERE ol.operador_designado_id = lo.operador_id AND ol.status_operador = 'despachado' AND DATE(ol.data_fim_operador) = CURDATE()) AS lotes_despachados_hoje
FROM lider_operadores lo
INNER JOIN users u_lider ON u_lider.id = lo.lider_id
INNER JOIN users u_op ON u_op.id = lo.operador_id
WHERE u_op.status = 'active';

-- =====================================================
-- 7. VIEW: LOTES PENDENTES PARA O LÍDER
-- =====================================================

CREATE OR REPLACE VIEW vw_lider_lotes_pendentes AS
SELECT 
    l.id AS lote_id,
    l.sequencia,
    l.quantidade,
    l.prioridade,
    l.status_operador,
    l.operador_designado_id,
    u_op.name AS operador_designado_nome,
    l.etapa_atual_id,
    e.nome AS etapa_nome,
    e.ordem AS etapa_ordem,
    op.id AS op_id,
    op.numero_op,
    v.cliente_nome,
    v.produto_nome,
    v.data_prevista,
    le.lider_id
FROM op_lotes l
INNER JOIN ordens_producao op ON op.id = l.ordem_producao_id
INNER JOIN vw_ordens_producao_resumo v ON v.id = op.id
INNER JOIN producao_etapas e ON e.id = l.etapa_atual_id
INNER JOIN lider_etapas le ON le.etapa_id = e.id
LEFT JOIN users u_op ON u_op.id = l.operador_designado_id
WHERE v.status NOT IN ('concluida', 'cancelada')
ORDER BY l.prioridade, v.data_prevista, l.id;

-- =====================================================
-- 8. VERIFICAÇÃO
-- =====================================================

SELECT 'Estrutura de Líder de Equipe criada com sucesso!' AS status;

SHOW TABLES LIKE 'lider_%';
SHOW TABLES LIKE 'etapa_operadores';

SHOW COLUMNS FROM op_lotes WHERE Field IN ('prioridade', 'operador_designado_id', 'data_atribuicao', 'atribuido_por_id');
SHOW COLUMNS FROM users WHERE Field = 'eh_lider_equipe';
