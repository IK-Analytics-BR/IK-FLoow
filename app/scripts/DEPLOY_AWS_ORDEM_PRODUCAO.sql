-- ========================================
-- DEPLOY AWS - MÓDULO ORDEM DE PRODUÇÃO
-- Data: 28/10/2025
-- Descrição: Script completo para deploy do módulo de Ordem de Produção na AWS
-- ========================================

USE supplychain;

-- Desabilitar verificações temporariamente
SET FOREIGN_KEY_CHECKS = 0;
SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';

-- ========================================
-- 1. CRIAR TABELAS
-- ========================================

-- Tabela: templates_producao
CREATE TABLE IF NOT EXISTS templates_producao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    produto_id INT NOT NULL,
    versao INT NOT NULL DEFAULT 1,
    ativo TINYINT(1) NOT NULL DEFAULT 1,
    custo_base DECIMAL(15,8) NOT NULL DEFAULT 0,
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT,
    updated_by INT,
    FOREIGN KEY (produto_id) REFERENCES products(id),
    INDEX idx_produto (produto_id),
    INDEX idx_ativo (ativo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: template_producao_itens
CREATE TABLE IF NOT EXISTS template_producao_itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_id INT NOT NULL,
    tipo_item ENUM('servico', 'materia_prima', 'consumo_interno') NOT NULL,
    produto_id INT NOT NULL,
    descricao VARCHAR(255) NOT NULL,
    quantidade DECIMAL(15,4) NOT NULL,
    unidade_medida VARCHAR(20),
    custo_unitario DECIMAL(15,8) NOT NULL,
    custo_total DECIMAL(15,8) NOT NULL,
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES templates_producao(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES products(id),
    INDEX idx_template (template_id),
    INDEX idx_tipo (tipo_item)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: ordens_producao
CREATE TABLE IF NOT EXISTS ordens_producao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_op VARCHAR(50) UNIQUE,
    empresa_id INT NOT NULL,
    cliente_id INT NOT NULL,
    produto_id INT NOT NULL,
    quantidade DECIMAL(15,4) NOT NULL,
    template_usado_id INT,
    usou_template TINYINT(1) NOT NULL DEFAULT 0,
    custo_total_template DECIMAL(15,8) DEFAULT 0,
    custo_total_atual DECIMAL(15,8) DEFAULT 0,
    variacao_custo_percentual DECIMAL(10,2) DEFAULT 0,
    data_solicitacao DATE NOT NULL,
    data_prevista DATE,
    data_inicio_producao DATETIME,
    data_conclusao DATETIME,
    status ENUM('pendente', 'em_producao', 'concluida', 'cancelada') NOT NULL DEFAULT 'pendente',
    observacoes TEXT,
    motivo_cancelamento TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT,
    updated_by INT,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (cliente_id) REFERENCES customers(id),
    FOREIGN KEY (produto_id) REFERENCES products(id),
    FOREIGN KEY (template_usado_id) REFERENCES templates_producao(id),
    INDEX idx_numero_op (numero_op),
    INDEX idx_empresa (empresa_id),
    INDEX idx_cliente (cliente_id),
    INDEX idx_produto (produto_id),
    INDEX idx_status (status),
    INDEX idx_data_solicitacao (data_solicitacao)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: ordem_producao_itens
CREATE TABLE IF NOT EXISTS ordem_producao_itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ordem_producao_id INT NOT NULL,
    tipo_item ENUM('servico', 'materia_prima', 'consumo_interno') NOT NULL,
    produto_id INT NOT NULL,
    descricao VARCHAR(255) NOT NULL,
    quantidade DECIMAL(15,4) NOT NULL,
    unidade_medida VARCHAR(20),
    custo_unitario_template DECIMAL(15,8),
    custo_unitario_atual DECIMAL(15,8) NOT NULL,
    custo_total DECIMAL(15,8) NOT NULL,
    veio_template TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ordem_producao_id) REFERENCES ordens_producao(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES products(id),
    INDEX idx_ordem (ordem_producao_id),
    INDEX idx_tipo (tipo_item)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- 2. TRIGGERS
-- ========================================

-- Trigger: Gerar número da OP automaticamente
DROP TRIGGER IF EXISTS gerar_numero_op;

DELIMITER $$
CREATE TRIGGER gerar_numero_op
BEFORE INSERT ON ordens_producao
FOR EACH ROW
BEGIN
    DECLARE ano_atual VARCHAR(4);
    DECLARE proximo_numero INT;
    
    SET ano_atual = YEAR(CURDATE());
    
    SELECT COALESCE(MAX(CAST(SUBSTRING(numero_op, 9) AS UNSIGNED)), 0) + 1
    INTO proximo_numero
    FROM ordens_producao
    WHERE numero_op LIKE CONCAT('OP-', ano_atual, '-%');
    
    SET NEW.numero_op = CONCAT('OP-', ano_atual, '-', LPAD(proximo_numero, 4, '0'));
END$$
DELIMITER ;

-- ========================================
-- 3. VIEWS
-- ========================================

-- View: vw_templates_ativos
DROP VIEW IF EXISTS vw_templates_ativos;

CREATE VIEW vw_templates_ativos AS
SELECT 
    t.id,
    t.nome,
    t.produto_id,
    p.name as produto_nome,
    t.versao,
    t.custo_base,
    t.observacoes,
    t.created_at,
    COUNT(ti.id) as total_itens
FROM templates_producao t
INNER JOIN products p ON t.produto_id = p.id
LEFT JOIN template_producao_itens ti ON t.id = ti.template_id
WHERE t.ativo = 1
GROUP BY t.id, t.nome, t.produto_id, p.name, t.versao, t.custo_base, t.observacoes, t.created_at
ORDER BY t.created_at DESC;

-- View: vw_ordens_producao_resumo
DROP VIEW IF EXISTS vw_ordens_producao_resumo;

CREATE VIEW vw_ordens_producao_resumo AS
SELECT 
    op.id,
    op.numero_op,
    e.nome_fantasia as empresa_nome,
    c.name as cliente_nome,
    p.name as produto_nome,
    op.quantidade,
    op.status,
    op.data_solicitacao,
    op.data_prevista,
    op.data_conclusao,
    op.custo_total_atual,
    op.usou_template,
    CASE 
        WHEN op.usou_template = 1 THEN CONCAT('Template v', t.versao)
        ELSE 'Manual'
    END as template_info,
    op.variacao_custo_percentual,
    op.created_at
FROM ordens_producao op
INNER JOIN empresas e ON op.empresa_id = e.id
INNER JOIN customers c ON op.cliente_id = c.id
INNER JOIN products p ON op.produto_id = p.id
LEFT JOIN templates_producao t ON op.template_usado_id = t.id
ORDER BY op.created_at DESC;

-- View: vw_ordem_producao_itens_detalhado
DROP VIEW IF EXISTS vw_ordem_producao_itens_detalhado;

CREATE VIEW vw_ordem_producao_itens_detalhado AS
SELECT 
    opi.id,
    opi.ordem_producao_id,
    op.numero_op,
    opi.tipo_item,
    CASE 
        WHEN opi.tipo_item = 'servico' THEN '🔧 Serviço'
        WHEN opi.tipo_item = 'materia_prima' THEN '📦 Matéria Prima'
        WHEN opi.tipo_item = 'consumo_interno' THEN '🧰 Consumo Interno'
    END as tipo_item_label,
    opi.produto_id,
    p.name as produto_nome,
    opi.descricao,
    opi.quantidade,
    opi.unidade_medida,
    opi.custo_unitario_template,
    opi.custo_unitario_atual,
    CASE 
        WHEN opi.custo_unitario_template > 0 THEN
            ((opi.custo_unitario_atual - opi.custo_unitario_template) / opi.custo_unitario_template * 100)
        ELSE 0
    END as variacao_custo_percentual,
    opi.custo_total,
    opi.veio_template,
    opi.created_at
FROM ordem_producao_itens opi
INNER JOIN ordens_producao op ON opi.ordem_producao_id = op.id
INNER JOIN products p ON opi.produto_id = p.id
ORDER BY opi.ordem_producao_id, opi.tipo_item, p.name;

-- ========================================
-- 4. ADICIONAR CATEGORIA FISCAL (se não existir)
-- ========================================

-- Verificar se a coluna categoria_fiscal existe
SET @dbname = DATABASE();
SET @tablename = 'products';
SET @columnname = 'categoria_fiscal';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = @columnname)
  ) > 0,
  'SELECT 1',
  CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN ', @columnname, ' ENUM(''servico'', ''materia_prima'', ''consumo_interno'', ''produto_final'') DEFAULT NULL AFTER category_id')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Adicionar índice se não existir
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (index_name = 'idx_categoria_fiscal')
  ) > 0,
  'SELECT 1',
  CONCAT('ALTER TABLE ', @tablename, ' ADD INDEX idx_categoria_fiscal (categoria_fiscal)')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- ========================================
-- 5. REABILITAR VERIFICAÇÕES
-- ========================================

SET FOREIGN_KEY_CHECKS = 1;

-- ========================================
-- 6. VERIFICAÇÃO FINAL
-- ========================================

SELECT 'DEPLOY CONCLUÍDO COM SUCESSO!' as status;

-- Verificar tabelas criadas
SELECT 
    'Tabelas criadas:' as info,
    COUNT(*) as total
FROM information_schema.TABLES
WHERE table_schema = DATABASE()
AND table_name IN ('templates_producao', 'template_producao_itens', 'ordens_producao', 'ordem_producao_itens');

-- Verificar views criadas
SELECT 
    'Views criadas:' as info,
    COUNT(*) as total
FROM information_schema.VIEWS
WHERE table_schema = DATABASE()
AND table_name IN ('vw_templates_ativos', 'vw_ordens_producao_resumo', 'vw_ordem_producao_itens_detalhado');

-- Verificar triggers criados
SELECT 
    'Triggers criados:' as info,
    COUNT(*) as total
FROM information_schema.TRIGGERS
WHERE trigger_schema = DATABASE()
AND trigger_name = 'gerar_numero_op';

-- Verificar coluna categoria_fiscal
SELECT 
    'Coluna categoria_fiscal:' as info,
    IF(COUNT(*) > 0, 'Existe', 'Não existe') as status
FROM information_schema.COLUMNS
WHERE table_schema = DATABASE()
AND table_name = 'products'
AND column_name = 'categoria_fiscal';

SELECT '========================================' as '';
SELECT 'PRÓXIMOS PASSOS:' as '';
SELECT '1. Enviar arquivos Python para AWS' as '';
SELECT '2. Enviar arquivos JavaScript para AWS' as '';
SELECT '3. Enviar templates HTML para AWS' as '';
SELECT '4. Reiniciar aplicação Flask' as '';
SELECT '========================================' as '';
