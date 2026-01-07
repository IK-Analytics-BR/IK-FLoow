-- =====================================================
-- SCRIPT DE CRIAÇÃO DE TABELAS - JORNADA DE TRABALHO
-- Módulo: Indústria
-- Data: 28/10/2025
-- =====================================================

USE supply_chain_system;

-- =====================================================
-- TABELA: jornadas_trabalho
-- Armazena as jornadas de trabalho por empresa
-- =====================================================

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


-- =====================================================
-- TABELA: jornada_horarios
-- Armazena os horários de cada jornada (por dia e turno)
-- =====================================================

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


-- =====================================================
-- DADOS DE EXEMPLO (OPCIONAL)
-- =====================================================

-- Inserir jornadas de exemplo para empresa ID 1
INSERT INTO jornadas_trabalho (empresa_id, nome, descricao, ativo, created_at) 
VALUES 
(1, 'Jornada Administrativa - 8h', 'Jornada comercial de 8 horas, Segunda a Sexta', 1, NOW()),
(1, 'Jornada 12x36 - Portaria', 'Jornada de 12 horas com 36 horas de descanso', 1, NOW()),
(1, 'Operação 24h - Turno Manhã', 'Primeiro turno de operação contínua (06h às 14h)', 1, NOW()),
(1, 'Operação 24h - Turno Tarde', 'Segundo turno de operação contínua (14h às 22h)', 1, NOW()),
(1, 'Operação 24h - Turno Noite', 'Terceiro turno de operação contínua (22h às 06h)', 1, NOW());

-- ========================================
-- JORNADA 1: Administrativa 8h (ID 1)
-- Segunda a Sexta, 08:00 às 17:00
-- ========================================
INSERT INTO jornada_horarios (jornada_id, dia_semana, turno, hora_inicio, hora_fim, created_at) 
VALUES 
(1, 'Segunda', 'Integral', '08:00:00', '17:00:00', NOW()),
(1, 'Terça', 'Integral', '08:00:00', '17:00:00', NOW()),
(1, 'Quarta', 'Integral', '08:00:00', '17:00:00', NOW()),
(1, 'Quinta', 'Integral', '08:00:00', '17:00:00', NOW()),
(1, 'Sexta', 'Integral', '08:00:00', '17:00:00', NOW());

-- ========================================
-- JORNADA 2: 12x36 (ID 2)
-- Dia sim, dia não
-- ========================================
INSERT INTO jornada_horarios (jornada_id, dia_semana, turno, hora_inicio, hora_fim, created_at) 
VALUES 
(2, 'Segunda', 'Integral', '07:00:00', '19:00:00', NOW()),
(2, 'Quarta', 'Integral', '07:00:00', '19:00:00', NOW()),
(2, 'Sexta', 'Integral', '07:00:00', '19:00:00', NOW()),
(2, 'Domingo', 'Integral', '07:00:00', '19:00:00', NOW());

-- ========================================
-- JORNADA 3: Operação 24h - TURNO MANHÃ (ID 3)
-- 3 turnos de 8h cobrindo 24h, 7 dias por semana
-- Turno 1: 06:00 às 14:00
-- ========================================
INSERT INTO jornada_horarios (jornada_id, dia_semana, turno, hora_inicio, hora_fim, created_at) 
VALUES 
(3, 'Segunda', 'Manhã', '06:00:00', '14:00:00', NOW()),
(3, 'Terça', 'Manhã', '06:00:00', '14:00:00', NOW()),
(3, 'Quarta', 'Manhã', '06:00:00', '14:00:00', NOW()),
(3, 'Quinta', 'Manhã', '06:00:00', '14:00:00', NOW()),
(3, 'Sexta', 'Manhã', '06:00:00', '14:00:00', NOW()),
(3, 'Sábado', 'Manhã', '06:00:00', '14:00:00', NOW()),
(3, 'Domingo', 'Manhã', '06:00:00', '14:00:00', NOW());

-- ========================================
-- JORNADA 4: Operação 24h - TURNO TARDE (ID 4)
-- Turno 2: 14:00 às 22:00
-- ========================================
INSERT INTO jornada_horarios (jornada_id, dia_semana, turno, hora_inicio, hora_fim, created_at) 
VALUES 
(4, 'Segunda', 'Tarde', '14:00:00', '22:00:00', NOW()),
(4, 'Terça', 'Tarde', '14:00:00', '22:00:00', NOW()),
(4, 'Quarta', 'Tarde', '14:00:00', '22:00:00', NOW()),
(4, 'Quinta', 'Tarde', '14:00:00', '22:00:00', NOW()),
(4, 'Sexta', 'Tarde', '14:00:00', '22:00:00', NOW()),
(4, 'Sábado', 'Tarde', '14:00:00', '22:00:00', NOW()),
(4, 'Domingo', 'Tarde', '14:00:00', '22:00:00', NOW());

-- ========================================
-- JORNADA 5: Operação 24h - TURNO NOITE (ID 5)
-- Turno 3: 22:00 às 06:00 (passa da meia-noite)
-- ========================================
INSERT INTO jornada_horarios (jornada_id, dia_semana, turno, hora_inicio, hora_fim, created_at) 
VALUES 
(5, 'Segunda', 'Noite', '22:00:00', '06:00:00', NOW()),
(5, 'Terça', 'Noite', '22:00:00', '06:00:00', NOW()),
(5, 'Quarta', 'Noite', '22:00:00', '06:00:00', NOW()),
(5, 'Quinta', 'Noite', '22:00:00', '06:00:00', NOW()),
(5, 'Sexta', 'Noite', '22:00:00', '06:00:00', NOW()),
(5, 'Sábado', 'Noite', '22:00:00', '06:00:00', NOW()),
(5, 'Domingo', 'Noite', '22:00:00', '06:00:00', NOW());


-- =====================================================
-- VIEWS ÚTEIS
-- =====================================================

-- View com resumo completo das jornadas
CREATE OR REPLACE VIEW vw_jornadas_resumo AS
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
GROUP BY jt.id;


-- View com cálculo de horas por jornada
CREATE OR REPLACE VIEW vw_jornadas_horas_totais AS
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


-- =====================================================
-- CONSULTAS ÚTEIS
-- =====================================================

-- Listar todas as jornadas com total de horas semanais
SELECT 
    jornada_id,
    jornada_nome,
    SUM(minutos_totais) / 60 as horas_semanais
FROM vw_jornadas_horas_totais
GROUP BY jornada_id, jornada_nome;

-- Verificar jornadas sem horários cadastrados
SELECT jt.*
FROM jornadas_trabalho jt
LEFT JOIN jornada_horarios jh ON jt.id = jh.jornada_id
WHERE jh.id IS NULL AND jt.ativo = 1;

-- Listar horários de uma jornada específica
SELECT 
    dia_semana,
    turno,
    hora_inicio,
    hora_fim,
    duracao
FROM vw_jornadas_horas_totais
WHERE jornada_id = 1
ORDER BY FIELD(dia_semana, 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo');


-- =====================================================
-- PERMISSÕES
-- =====================================================

-- Garantir que usuário da aplicação tenha permissões
GRANT SELECT, INSERT, UPDATE, DELETE ON supply_chain_system.jornadas_trabalho TO 'your_user'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON supply_chain_system.jornada_horarios TO 'your_user'@'localhost';

-- =====================================================
-- FIM DO SCRIPT
-- =====================================================
