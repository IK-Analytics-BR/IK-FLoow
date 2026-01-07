-- =====================================================
-- SCRIPT: Criar 6 Líderes, 12 Operadores e Atribuições
-- Senha padrão: 123456
-- Usa ETAPAS JÁ EXISTENTES no banco
-- =====================================================

SET @senha = '123456';

-- =====================================================
-- 1. CRIAR 6 LÍDERES (se não existirem)
-- =====================================================
INSERT IGNORE INTO users (username, email, password, name, role, status, eh_lider_equipe) VALUES
('lider1', 'lider1@empresa.com', @senha, 'Líder 1 - Engenharia/PCP', 'user', 'active', 1),
('lider2', 'lider2@empresa.com', @senha, 'Líder 2 - Preparação', 'user', 'active', 1),
('lider3', 'lider3@empresa.com', @senha, 'Líder 3 - Montagem/Corte', 'user', 'active', 1),
('lider4', 'lider4@empresa.com', @senha, 'Líder 4 - Vulcanização', 'user', 'active', 1),
('lider5', 'lider5@empresa.com', @senha, 'Líder 5 - Acabamento/Qualidade', 'user', 'active', 1),
('lider6', 'lider6@empresa.com', @senha, 'Líder 6 - Embalagem/Expedição', 'user', 'active', 1);

-- =====================================================
-- 2. CRIAR 12 OPERADORES (se não existirem)
-- =====================================================
INSERT IGNORE INTO users (username, email, password, name, role, status, eh_operador) VALUES
('operador1', 'operador1@empresa.com', @senha, 'Operador 1', 'user', 'active', 1),
('operador2', 'operador2@empresa.com', @senha, 'Operador 2', 'user', 'active', 1),
('operador3', 'operador3@empresa.com', @senha, 'Operador 3', 'user', 'active', 1),
('operador4', 'operador4@empresa.com', @senha, 'Operador 4', 'user', 'active', 1),
('operador5', 'operador5@empresa.com', @senha, 'Operador 5', 'user', 'active', 1),
('operador6', 'operador6@empresa.com', @senha, 'Operador 6', 'user', 'active', 1),
('operador7', 'operador7@empresa.com', @senha, 'Operador 7', 'user', 'active', 1),
('operador8', 'operador8@empresa.com', @senha, 'Operador 8', 'user', 'active', 1),
('operador9', 'operador9@empresa.com', @senha, 'Operador 9', 'user', 'active', 1),
('operador10', 'operador10@empresa.com', @senha, 'Operador 10', 'user', 'active', 1),
('operador11', 'operador11@empresa.com', @senha, 'Operador 11', 'user', 'active', 1),
('operador12', 'operador12@empresa.com', @senha, 'Operador 12', 'user', 'active', 1);

-- =====================================================
-- 3. ATRIBUIR LÍDERES ÀS ETAPAS EXISTENTES
-- Etapas existentes: 8-22 (15 etapas)
-- Dividindo entre 6 líderes
-- =====================================================

-- Líder 1 → Etapas 8, 9, 10 (Engenharia, PCP, Separação MP)
INSERT IGNORE INTO lider_etapas (lider_id, etapa_id) VALUES
((SELECT id FROM users WHERE username = 'lider1'), 8),
((SELECT id FROM users WHERE username = 'lider1'), 9),
((SELECT id FROM users WHERE username = 'lider1'), 10);

-- Líder 2 → Etapas 11, 12 (Prep Borracha, Prep Lonas)
INSERT IGNORE INTO lider_etapas (lider_id, etapa_id) VALUES
((SELECT id FROM users WHERE username = 'lider2'), 11),
((SELECT id FROM users WHERE username = 'lider2'), 12);

-- Líder 3 → Etapas 13, 14, 15 (Montagem, Pré-Compactação, Corte)
INSERT IGNORE INTO lider_etapas (lider_id, etapa_id) VALUES
((SELECT id FROM users WHERE username = 'lider3'), 13),
((SELECT id FROM users WHERE username = 'lider3'), 14),
((SELECT id FROM users WHERE username = 'lider3'), 15);

-- Líder 4 → Etapas 16, 17 (Vulcanização, Resfriamento)
INSERT IGNORE INTO lider_etapas (lider_id, etapa_id) VALUES
((SELECT id FROM users WHERE username = 'lider4'), 16),
((SELECT id FROM users WHERE username = 'lider4'), 17);

-- Líder 5 → Etapas 18, 19, 20 (Acabamento, Emenda, Inspeção)
INSERT IGNORE INTO lider_etapas (lider_id, etapa_id) VALUES
((SELECT id FROM users WHERE username = 'lider5'), 18),
((SELECT id FROM users WHERE username = 'lider5'), 19),
((SELECT id FROM users WHERE username = 'lider5'), 20);

-- Líder 6 → Etapas 21, 22 (Embalagem, Expedição)
INSERT IGNORE INTO lider_etapas (lider_id, etapa_id) VALUES
((SELECT id FROM users WHERE username = 'lider6'), 21),
((SELECT id FROM users WHERE username = 'lider6'), 22);

-- =====================================================
-- 4. ATRIBUIR OPERADORES AOS LÍDERES (2 por líder)
-- =====================================================

-- Líder 1 → Operadores 1 e 2
INSERT IGNORE INTO lider_operadores (lider_id, operador_id) VALUES
((SELECT id FROM users WHERE username = 'lider1'), (SELECT id FROM users WHERE username = 'operador1')),
((SELECT id FROM users WHERE username = 'lider1'), (SELECT id FROM users WHERE username = 'operador2'));

-- Líder 2 → Operadores 3 e 4
INSERT IGNORE INTO lider_operadores (lider_id, operador_id) VALUES
((SELECT id FROM users WHERE username = 'lider2'), (SELECT id FROM users WHERE username = 'operador3')),
((SELECT id FROM users WHERE username = 'lider2'), (SELECT id FROM users WHERE username = 'operador4'));

-- Líder 3 → Operadores 5 e 6
INSERT IGNORE INTO lider_operadores (lider_id, operador_id) VALUES
((SELECT id FROM users WHERE username = 'lider3'), (SELECT id FROM users WHERE username = 'operador5')),
((SELECT id FROM users WHERE username = 'lider3'), (SELECT id FROM users WHERE username = 'operador6'));

-- Líder 4 → Operadores 7 e 8
INSERT IGNORE INTO lider_operadores (lider_id, operador_id) VALUES
((SELECT id FROM users WHERE username = 'lider4'), (SELECT id FROM users WHERE username = 'operador7')),
((SELECT id FROM users WHERE username = 'lider4'), (SELECT id FROM users WHERE username = 'operador8'));

-- Líder 5 → Operadores 9 e 10
INSERT IGNORE INTO lider_operadores (lider_id, operador_id) VALUES
((SELECT id FROM users WHERE username = 'lider5'), (SELECT id FROM users WHERE username = 'operador9')),
((SELECT id FROM users WHERE username = 'lider5'), (SELECT id FROM users WHERE username = 'operador10'));

-- Líder 6 → Operadores 11 e 12
INSERT IGNORE INTO lider_operadores (lider_id, operador_id) VALUES
((SELECT id FROM users WHERE username = 'lider6'), (SELECT id FROM users WHERE username = 'operador11')),
((SELECT id FROM users WHERE username = 'lider6'), (SELECT id FROM users WHERE username = 'operador12'));

-- =====================================================
-- 5. VINCULAR USUÁRIOS À EMPRESA (obrigatório para login)
-- Vincula todos líderes e operadores à empresa ID 1
-- =====================================================

INSERT IGNORE INTO user_empresas (user_id, empresa_id) 
SELECT id, 1 FROM users WHERE username LIKE 'lider%';

INSERT IGNORE INTO user_empresas (user_id, empresa_id) 
SELECT id, 1 FROM users WHERE username LIKE 'operador%';

-- =====================================================
-- 6. VERIFICAÇÃO - Ver estrutura criada
-- =====================================================

-- Ver líderes e suas etapas
SELECT 
    u.username AS lider,
    u.name AS nome_lider,
    GROUP_CONCAT(e.nome ORDER BY e.ordem SEPARATOR ', ') AS etapas_controladas
FROM users u
INNER JOIN lider_etapas le ON le.lider_id = u.id
INNER JOIN producao_etapas e ON e.id = le.etapa_id
WHERE u.username LIKE 'lider%'
GROUP BY u.id
ORDER BY u.username;

-- Ver líderes e seus operadores
SELECT 
    u.username AS lider,
    u.name AS nome_lider,
    GROUP_CONCAT(op.username ORDER BY op.username SEPARATOR ', ') AS operadores
FROM users u
INNER JOIN lider_operadores lo ON lo.lider_id = u.id
INNER JOIN users op ON op.id = lo.operador_id
WHERE u.username LIKE 'lider%'
GROUP BY u.id
ORDER BY u.username;
