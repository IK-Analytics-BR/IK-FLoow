-- =====================================================
-- Script: 068_ESTOQUE_POR_EMPRESA.sql
-- Descrição: Implementa controle de estoque por empresa
-- Data: 2024-12-28
-- =====================================================

-- 1. Criar tabela de estoque por empresa
CREATE TABLE IF NOT EXISTS estoque_empresa (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    produto_id INT NOT NULL,
    quantidade DECIMAL(15,4) DEFAULT 0,
    quantidade_reservada DECIMAL(15,4) DEFAULT 0,
    quantidade_disponivel DECIMAL(15,4) GENERATED ALWAYS AS (quantidade - quantidade_reservada) STORED,
    custo_medio DECIMAL(15,4) DEFAULT 0,
    ultimo_custo DECIMAL(15,4) DEFAULT 0,
    local_id INT DEFAULT 1,
    estoque_minimo DECIMAL(15,4) DEFAULT 0,
    estoque_maximo DECIMAL(15,4) DEFAULT 0,
    ultima_entrada DATETIME NULL,
    ultima_saida DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_empresa_produto_local (empresa_id, produto_id, local_id),
    INDEX idx_empresa (empresa_id),
    INDEX idx_produto (produto_id),
    INDEX idx_quantidade (quantidade),
    
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Adicionar coluna empresa_id na tabela estoque_movimentacoes
ALTER TABLE estoque_movimentacoes 
ADD COLUMN IF NOT EXISTS empresa_id INT NULL AFTER id;

-- Adicionar índice para empresa_id
ALTER TABLE estoque_movimentacoes 
ADD INDEX IF NOT EXISTS idx_mov_empresa (empresa_id);

-- 3. Atualizar movimentações existentes com empresa padrão (empresa_id = 1)
UPDATE estoque_movimentacoes 
SET empresa_id = 1 
WHERE empresa_id IS NULL;

-- 4. Migrar dados existentes de current_stock para estoque_empresa
INSERT IGNORE INTO estoque_empresa (empresa_id, produto_id, quantidade, local_id, estoque_minimo, estoque_maximo)
SELECT 
    1 as empresa_id,
    cs.product_id,
    cs.quantity,
    cs.location_id,
    COALESCE(cs.min_stock, 0),
    COALESCE(cs.max_stock, 0)
FROM current_stock cs
WHERE cs.product_id IS NOT NULL;

-- 5. Migrar dados de products.stock_quantity para empresa padrão
INSERT INTO estoque_empresa (empresa_id, produto_id, quantidade, local_id)
SELECT 
    1 as empresa_id,
    p.id as produto_id,
    COALESCE(p.stock_quantity, 0) as quantidade,
    1 as local_id
FROM products p
WHERE p.active = 1
ON DUPLICATE KEY UPDATE 
    quantidade = VALUES(quantidade);

-- 6. Criar view para consulta de estoque por empresa
CREATE OR REPLACE VIEW vw_estoque_empresa AS
SELECT 
    ee.id,
    ee.empresa_id,
    e.nome_fantasia as empresa_nome,
    e.cnpj as empresa_cnpj,
    ee.produto_id,
    p.name as produto_nome,
    p.internal_code as produto_codigo,
    p.barcode as produto_ean,
    p.unit_measure as unidade,
    c.name as categoria,
    ee.quantidade,
    ee.quantidade_reservada,
    ee.quantidade_disponivel,
    ee.custo_medio,
    ee.ultimo_custo,
    ee.local_id,
    l.name as local_nome,
    ee.estoque_minimo,
    ee.estoque_maximo,
    CASE 
        WHEN ee.quantidade <= 0 THEN 'sem_estoque'
        WHEN ee.quantidade <= ee.estoque_minimo THEN 'baixo'
        WHEN ee.quantidade >= ee.estoque_maximo AND ee.estoque_maximo > 0 THEN 'alto'
        ELSE 'normal'
    END as status_estoque,
    ee.ultima_entrada,
    ee.ultima_saida,
    ee.updated_at
FROM estoque_empresa ee
JOIN empresas e ON e.id = ee.empresa_id
JOIN products p ON p.id = ee.produto_id
LEFT JOIN product_categories c ON c.id = p.category_id
LEFT JOIN stock_locations l ON l.id = ee.local_id
WHERE p.active = 1;

-- 7. Criar view para resumo de movimentações por empresa
CREATE OR REPLACE VIEW vw_kardex_empresa AS
SELECT 
    em.id,
    em.empresa_id,
    e.nome_fantasia as empresa_nome,
    em.produto_id,
    p.name as produto_nome,
    p.internal_code as produto_codigo,
    em.tipo,
    CASE em.tipo
        WHEN 'entrada' THEN 'Entrada'
        WHEN 'saida' THEN 'Saída'
        WHEN 'ajuste_positivo' THEN 'Ajuste (+)'
        WHEN 'ajuste_negativo' THEN 'Ajuste (-)'
        WHEN 'reserva' THEN 'Reserva'
        WHEN 'liberacao_reserva' THEN 'Liberação'
        WHEN 'baixa_producao' THEN 'Baixa Produção'
        WHEN 'entrada_producao' THEN 'Entrada Produção'
        WHEN 'venda' THEN 'Venda'
        WHEN 'devolucao' THEN 'Devolução'
        WHEN 'transferencia' THEN 'Transferência'
        ELSE em.tipo
    END as tipo_descricao,
    em.quantidade,
    em.estoque_anterior,
    em.estoque_posterior,
    em.origem_tela,
    em.referencia_tipo,
    em.referencia_id,
    em.referencia_codigo,
    em.observacao,
    em.usuario_nome,
    em.created_at
FROM estoque_movimentacoes em
LEFT JOIN empresas e ON e.id = em.empresa_id
JOIN products p ON p.id = em.produto_id
ORDER BY em.created_at DESC;

-- 8. Criar função/procedure para obter estoque de uma empresa
DELIMITER //

DROP PROCEDURE IF EXISTS sp_obter_estoque_empresa//
CREATE PROCEDURE sp_obter_estoque_empresa(
    IN p_empresa_id INT,
    IN p_produto_id INT
)
BEGIN
    SELECT 
        COALESCE(ee.quantidade, 0) as quantidade,
        COALESCE(ee.quantidade_reservada, 0) as quantidade_reservada,
        COALESCE(ee.quantidade, 0) - COALESCE(ee.quantidade_reservada, 0) as quantidade_disponivel
    FROM estoque_empresa ee
    WHERE ee.empresa_id = p_empresa_id 
      AND ee.produto_id = p_produto_id
      AND ee.local_id = 1;
END//

DROP PROCEDURE IF EXISTS sp_atualizar_estoque_empresa//
CREATE PROCEDURE sp_atualizar_estoque_empresa(
    IN p_empresa_id INT,
    IN p_produto_id INT,
    IN p_quantidade DECIMAL(15,4),
    IN p_operacao VARCHAR(20),
    IN p_custo DECIMAL(15,4)
)
BEGIN
    DECLARE v_qtd_atual DECIMAL(15,4) DEFAULT 0;
    DECLARE v_qtd_nova DECIMAL(15,4) DEFAULT 0;
    
    -- Buscar quantidade atual
    SELECT COALESCE(quantidade, 0) INTO v_qtd_atual
    FROM estoque_empresa 
    WHERE empresa_id = p_empresa_id AND produto_id = p_produto_id AND local_id = 1;
    
    -- Calcular nova quantidade
    IF p_operacao = 'entrada' THEN
        SET v_qtd_nova = v_qtd_atual + p_quantidade;
    ELSEIF p_operacao = 'saida' THEN
        SET v_qtd_nova = v_qtd_atual - p_quantidade;
    ELSE
        SET v_qtd_nova = p_quantidade;
    END IF;
    
    -- Inserir ou atualizar
    INSERT INTO estoque_empresa (empresa_id, produto_id, quantidade, ultimo_custo, local_id)
    VALUES (p_empresa_id, p_produto_id, v_qtd_nova, p_custo, 1)
    ON DUPLICATE KEY UPDATE 
        quantidade = v_qtd_nova,
        ultimo_custo = COALESCE(p_custo, ultimo_custo),
        updated_at = NOW();
    
    -- Atualizar data de entrada/saída
    IF p_operacao = 'entrada' THEN
        UPDATE estoque_empresa 
        SET ultima_entrada = NOW()
        WHERE empresa_id = p_empresa_id AND produto_id = p_produto_id AND local_id = 1;
    ELSEIF p_operacao = 'saida' THEN
        UPDATE estoque_empresa 
        SET ultima_saida = NOW()
        WHERE empresa_id = p_empresa_id AND produto_id = p_produto_id AND local_id = 1;
    END IF;
    
    SELECT v_qtd_nova as nova_quantidade;
END//

DELIMITER ;

-- 9. Índices adicionais para performance
ALTER TABLE estoque_empresa ADD INDEX IF NOT EXISTS idx_quantidade_disponivel (quantidade_disponivel);
ALTER TABLE estoque_movimentacoes ADD INDEX IF NOT EXISTS idx_mov_empresa_produto (empresa_id, produto_id);
ALTER TABLE estoque_movimentacoes ADD INDEX IF NOT EXISTS idx_mov_data (created_at);

-- 10. Mensagem de conclusão
SELECT 'Script 068_ESTOQUE_POR_EMPRESA.sql executado com sucesso!' as resultado;
SELECT COUNT(*) as total_registros FROM estoque_empresa;
