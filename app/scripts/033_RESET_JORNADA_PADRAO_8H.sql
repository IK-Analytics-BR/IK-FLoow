-- =====================================================
-- SCRIPT 033: RESET JORNADA DE TRABALHO - PADRÃO 8H
-- Data: 2025-12-26
-- Descrição: Limpa todas as jornadas e insere jornada padrão
--            Segunda a Sexta, 08:00-12:00 e 13:00-17:00
--            (8 horas diárias com 1 hora de almoço)
-- =====================================================

USE supply_chain_system;

-- =====================================================
-- ETAPA 1: LIMPAR TABELAS
-- =====================================================

-- Desabilitar verificação de chaves estrangeiras temporariamente
SET FOREIGN_KEY_CHECKS = 0;

-- Limpar horários primeiro (tem FK para jornadas)
TRUNCATE TABLE jornada_horarios;

-- Limpar jornadas
TRUNCATE TABLE jornadas_trabalho;

-- Reabilitar verificação de chaves estrangeiras
SET FOREIGN_KEY_CHECKS = 1;

SELECT 'Tabelas limpas com sucesso!' AS status;

-- =====================================================
-- ETAPA 2: CRIAR JORNADA PADRÃO
-- =====================================================

-- Inserir jornada padrão para empresa 1
INSERT INTO jornadas_trabalho (empresa_id, nome, descricao, ativo, created_at)
VALUES (1, 'Jornada Padrão 8h', 'Segunda a Sexta, 08:00-12:00 e 13:00-17:00 (1h almoço)', 1, NOW());

-- Pegar o ID da jornada criada
SET @jornada_id = LAST_INSERT_ID();

SELECT CONCAT('Jornada criada com ID: ', @jornada_id) AS status;

-- =====================================================
-- ETAPA 3: INSERIR HORÁRIOS (SEG-SEX, MANHÃ E TARDE)
-- =====================================================

-- SEGUNDA-FEIRA
INSERT INTO jornada_horarios (jornada_id, dia_semana, turno, hora_inicio, hora_fim, created_at) VALUES
(@jornada_id, 'Segunda', 'Manhã', '08:00:00', '12:00:00', NOW()),
(@jornada_id, 'Segunda', 'Tarde', '13:00:00', '17:00:00', NOW());

-- TERÇA-FEIRA
INSERT INTO jornada_horarios (jornada_id, dia_semana, turno, hora_inicio, hora_fim, created_at) VALUES
(@jornada_id, 'Terça', 'Manhã', '08:00:00', '12:00:00', NOW()),
(@jornada_id, 'Terça', 'Tarde', '13:00:00', '17:00:00', NOW());

-- QUARTA-FEIRA
INSERT INTO jornada_horarios (jornada_id, dia_semana, turno, hora_inicio, hora_fim, created_at) VALUES
(@jornada_id, 'Quarta', 'Manhã', '08:00:00', '12:00:00', NOW()),
(@jornada_id, 'Quarta', 'Tarde', '13:00:00', '17:00:00', NOW());

-- QUINTA-FEIRA
INSERT INTO jornada_horarios (jornada_id, dia_semana, turno, hora_inicio, hora_fim, created_at) VALUES
(@jornada_id, 'Quinta', 'Manhã', '08:00:00', '12:00:00', NOW()),
(@jornada_id, 'Quinta', 'Tarde', '13:00:00', '17:00:00', NOW());

-- SEXTA-FEIRA
INSERT INTO jornada_horarios (jornada_id, dia_semana, turno, hora_inicio, hora_fim, created_at) VALUES
(@jornada_id, 'Sexta', 'Manhã', '08:00:00', '12:00:00', NOW()),
(@jornada_id, 'Sexta', 'Tarde', '13:00:00', '17:00:00', NOW());

-- =====================================================
-- ETAPA 4: VERIFICAÇÃO
-- =====================================================

SELECT 'Horários inseridos:' AS info;

SELECT 
    jh.dia_semana,
    jh.turno,
    TIME_FORMAT(jh.hora_inicio, '%H:%i') AS entrada,
    TIME_FORMAT(jh.hora_fim, '%H:%i') AS saida,
    TIMESTAMPDIFF(MINUTE, jh.hora_inicio, jh.hora_fim) AS minutos
FROM jornada_horarios jh
JOIN jornadas_trabalho jt ON jh.jornada_id = jt.id
WHERE jt.ativo = 1
ORDER BY FIELD(jh.dia_semana, 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta'), jh.hora_inicio;

-- Resumo
SELECT 
    'RESUMO' AS info,
    COUNT(DISTINCT jh.dia_semana) AS dias_semana,
    SUM(TIMESTAMPDIFF(MINUTE, jh.hora_inicio, jh.hora_fim)) AS minutos_semanais,
    ROUND(SUM(TIMESTAMPDIFF(MINUTE, jh.hora_inicio, jh.hora_fim)) / 60, 1) AS horas_semanais
FROM jornada_horarios jh
JOIN jornadas_trabalho jt ON jh.jornada_id = jt.id
WHERE jt.ativo = 1;

SELECT 'Script 033 executado com sucesso!' AS status;
SELECT 'PRÓXIMO PASSO: Iniciar o sistema e acessar Menu Indústria > Dashboard Gargalos' AS proximo;
