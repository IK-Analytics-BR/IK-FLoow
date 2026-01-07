-- =====================================================
-- ADICIONAR CAMPOS VENDEDOR E OPERADOR NA TABELA USERS
-- =====================================================
-- Data: 24/12/2025
-- Objetivo: Adicionar flags para identificar se usuário
--           é vendedor e/ou operador de chão de fábrica
-- =====================================================

USE supply_chain_system;

-- Adicionar campo "é vendedor"
ALTER TABLE users ADD COLUMN eh_vendedor TINYINT(1) NOT NULL DEFAULT 0 
    COMMENT 'Indica se o usuário é vendedor (aparece em comissões)';

-- Adicionar campo "é operador" (chão de fábrica)
ALTER TABLE users ADD COLUMN eh_operador TINYINT(1) NOT NULL DEFAULT 0 
    COMMENT 'Indica se o usuário é operador de chão de fábrica (aparece no Gantt e OPs)';

-- Adicionar campo de comissão padrão para vendedores
ALTER TABLE users ADD COLUMN comissao_padrao DECIMAL(5,2) DEFAULT 0.00 
    COMMENT 'Percentual de comissão padrão do vendedor';

-- Índices para consultas
CREATE INDEX idx_users_eh_vendedor ON users(eh_vendedor);
CREATE INDEX idx_users_eh_operador ON users(eh_operador);

-- =====================================================
-- VERIFICAÇÃO
-- =====================================================
SELECT 'Campos adicionados com sucesso!' AS status;

DESCRIBE users;
