-- ========================================
-- DEPLOY AWS - JORNADA DE TRABALHO
-- Data: 29/10/2025
-- ========================================

USE supply_chain_system;

SET FOREIGN_KEY_CHECKS = 0;

-- ========================================
-- 1. CRIAR TABELAS
-- ========================================

SELECT '📦 Criando tabela jornadas_trabalho...' as status;

-- Tabela: jornadas_trabalho
CREATE TABLE IF NOT EXISTS jornadas_trabalho (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    nome VARCHAR(100) NOT NULL COMMENT 'Nome da jornada (ex: Jornada Padrão 8h)',
    descricao TEXT COMMENT 'Descrição detalhada da jornada',
    ativo TINYINT(1) DEFAULT 1 COMMENT '1 = Ativo, 0 = Inativo',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT COMMENT 'ID do usuário que criou',
    updated_by INT COMMENT 'ID do último usuário que atualizou',
    
    -- Foreign Keys
    CONSTRAINT fk_jornada_empresa 
        FOREIGN KEY (empresa_id) 
        REFERENCES empresas(id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE,
    
    -- Indexes
    INDEX idx_empresa (empresa_id),
    INDEX idx_ativo (ativo),
    INDEX idx_nome (nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Jornadas de trabalho por empresa';

SELECT '✅ Tabela jornadas_trabalho criada!' as status;

-- ========================================

SELECT '📦 Criando tabela jornada_horarios...' as status;

-- Tabela: jornada_horarios
CREATE TABLE IF NOT EXISTS jornada_horarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    jornada_id INT NOT NULL COMMENT 'ID da jornada',
    dia_semana ENUM('Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo') NOT NULL,
    turno ENUM('Manhã', 'Tarde', 'Noite', 'Integral') NOT NULL,
    hora_inicio TIME NOT NULL COMMENT 'Hora de início do turno',
    hora_fim TIME NOT NULL COMMENT 'Hora de fim do turno',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_horario_jornada 
        FOREIGN KEY (jornada_id) 
        REFERENCES jornadas_trabalho(id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    
    -- Indexes
    INDEX idx_jornada (jornada_id),
    INDEX idx_dia_semana (dia_semana),
    INDEX idx_turno (turno)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Horários das jornadas de trabalho por dia e turno';

SELECT '✅ Tabela jornada_horarios criada!' as status;

-- ========================================
-- 2. CRIAR VIEWS
-- ========================================

SELECT '👁️ Criando views...' as status;

-- View: vw_jornadas_resumo
DROP VIEW IF EXISTS vw_jornadas_resumo;

CREATE VIEW vw_jornadas_resumo AS
SELECT 
    jt.id,
    jt.nome as jornada_nome,
    jt.descricao,
    e.nome_fantasia as empresa_nome,
    jt.ativo,
    COUNT(DISTINCT jh.id) as total_horarios,
    GROUP_CONCAT(DISTINCT jh.dia_semana ORDER BY 
        FIELD(jh.dia_semana, 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo')
        SEPARATOR ', ') as dias_semana,
    MIN(jh.hora_inicio) as primeira_entrada,
    MAX(jh.hora_fim) as ultima_saida,
    jt.created_at,
    jt.updated_at
FROM jornadas_trabalho jt
LEFT JOIN empresas e ON jt.empresa_id = e.id
LEFT JOIN jornada_horarios jh ON jt.id = jh.jornada_id
GROUP BY jt.id, jt.nome, jt.descricao, e.nome_fantasia, jt.ativo, jt.created_at, jt.updated_at;

SELECT '✅ View vw_jornadas_resumo criada!' as status;

-- View: vw_jornadas_horas_totais
DROP VIEW IF EXISTS vw_jornadas_horas_totais;

CREATE VIEW vw_jornadas_horas_totais AS
SELECT 
    jt.id as jornada_id,
    jt.nome as jornada_nome,
    jh.dia_semana,
    jh.turno,
    jh.hora_inicio,
    jh.hora_fim,
    TIME_FORMAT(TIMEDIFF(jh.hora_fim, jh.hora_inicio), '%H:%i') as duracao,
    HOUR(TIMEDIFF(jh.hora_fim, jh.hora_inicio)) * 60 + 
    MINUTE(TIMEDIFF(jh.hora_fim, jh.hora_inicio)) as minutos_totais
FROM jornadas_trabalho jt
INNER JOIN jornada_horarios jh ON jt.id = jh.jornada_id
ORDER BY jt.id, 
    FIELD(jh.dia_semana, 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'),
    jh.hora_inicio;

SELECT '✅ View vw_jornadas_horas_totais criada!' as status;

SET FOREIGN_KEY_CHECKS = 1;

-- ========================================
-- 3. VERIFICAÇÃO FINAL
-- ========================================

SELECT '========================================' as '';
SELECT '🔍 VERIFICAÇÃO FINAL' as '';
SELECT '========================================' as '';

-- Verificar tabelas
SELECT 'TABELAS:' as tipo, table_name as nome
FROM information_schema.TABLES
WHERE table_schema = 'supply_chain_system'
AND table_name IN ('jornadas_trabalho', 'jornada_horarios')
ORDER BY table_name;

-- Verificar views
SELECT 'VIEWS:' as tipo, table_name as nome
FROM information_schema.VIEWS
WHERE table_schema = 'supply_chain_system'
AND table_name IN ('vw_jornadas_resumo', 'vw_jornadas_horas_totais')
ORDER BY table_name;

SELECT '========================================' as '';
SELECT '✅ DEPLOY CONCLUÍDO COM SUCESSO!' as '';
SELECT 'Módulo Jornada de Trabalho pronto para uso!' as '';
SELECT '========================================' as '';
SELECT '' as '';
SELECT '💡 PRÓXIMOS PASSOS:' as '';
SELECT '1. Reiniciar Flask: sudo systemctl restart supplychain' as '';
SELECT '2. Acessar: Jornada de Trabalho' as '';
SELECT '3. Criar sua primeira jornada!' as '';
SELECT '========================================' as '';
