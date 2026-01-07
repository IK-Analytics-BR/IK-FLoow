-- =====================================================
-- SISTEMA DE ABATIMENTO DE ESTOQUE POR DNA NO ORÇAMENTO
-- =====================================================
-- Permite que ao adicionar um produto no orçamento:
-- 1. Verifique se existe estoque produzido com DNA similar
-- 2. Abata do estoque se houver quantidade suficiente
-- 3. Gere OP para quantidade faltante
-- =====================================================

-- -----------------------------------------------------
-- 1. Tabela para vincular itens do orçamento com estoque/OP
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS orcamento_item_alocacao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Vínculo com orçamento
    orcamento_id INT NOT NULL,
    orcamento_item_id INT NOT NULL,
    
    -- Tipo de alocação: 'estoque' ou 'producao'
    tipo_alocacao ENUM('estoque', 'producao') NOT NULL,
    
    -- Se tipo = 'estoque': produto do estoque usado
    produto_estoque_id INT NULL COMMENT 'Produto do estoque com DNA similar',
    quantidade_estoque DECIMAL(15,4) DEFAULT 0 COMMENT 'Quantidade a usar do estoque',
    
    -- Se tipo = 'producao': OP gerada
    ordem_producao_id INT NULL COMMENT 'OP gerada para produzir',
    quantidade_producao DECIMAL(15,4) DEFAULT 0 COMMENT 'Quantidade a produzir',
    
    -- Status da alocação
    status ENUM('pendente', 'reservado', 'separado', 'consumido', 'cancelado') DEFAULT 'pendente',
    
    -- DNA usado para matching
    codigo_dna_origem VARCHAR(100) COMMENT 'DNA do produto solicitado',
    codigo_dna_estoque VARCHAR(100) COMMENT 'DNA do produto no estoque (pode ser diferente se derivável)',
    tipo_match ENUM('exato', 'derivavel', 'parcial') COMMENT 'Tipo de correspondência DNA',
    
    -- Metadados
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    created_by INT,
    
    -- Índices
    INDEX idx_orcamento (orcamento_id),
    INDEX idx_orcamento_item (orcamento_item_id),
    INDEX idx_produto_estoque (produto_estoque_id),
    INDEX idx_op (ordem_producao_id),
    INDEX idx_status (status),
    
    -- FKs
    FOREIGN KEY (orcamento_id) REFERENCES orcamentos(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_estoque_id) REFERENCES products(id),
    FOREIGN KEY (ordem_producao_id) REFERENCES ordens_producao(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- -----------------------------------------------------
-- 2. Tabela para reserva de estoque (soft lock)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS estoque_reservas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    produto_id INT NOT NULL,
    quantidade DECIMAL(15,4) NOT NULL,
    
    -- Origem da reserva
    tipo_origem ENUM('orcamento', 'pedido', 'op', 'manual') NOT NULL,
    origem_id INT NOT NULL COMMENT 'ID do orçamento, pedido ou OP',
    
    -- Status
    status ENUM('ativo', 'confirmado', 'cancelado', 'expirado') DEFAULT 'ativo',
    data_expiracao DATETIME COMMENT 'Reserva expira se orçamento não for aprovado',
    
    -- Metadados
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    created_by INT,
    observacao TEXT,
    
    INDEX idx_produto (produto_id),
    INDEX idx_origem (tipo_origem, origem_id),
    INDEX idx_status (status),
    INDEX idx_expiracao (data_expiracao),
    
    FOREIGN KEY (produto_id) REFERENCES products(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- -----------------------------------------------------
-- 3. View para estoque disponível (descontando reservas)
-- -----------------------------------------------------
CREATE OR REPLACE VIEW vw_estoque_disponivel AS
SELECT 
    p.id AS produto_id,
    p.name AS produto_nome,
    p.internal_code AS produto_codigo,
    pet.codigo_dna,
    pet.tipo_correia_id,
    pet.material_base_id,
    pet.largura_mm,
    pet.comprimento_mm,
    pet.espessura_mm,
    COALESCE(cs.quantity, p.stock_quantity, 0) AS estoque_total,
    COALESCE(
        (SELECT SUM(er.quantidade) 
         FROM estoque_reservas er 
         WHERE er.produto_id = p.id AND er.status = 'ativo'), 
        0
    ) AS estoque_reservado,
    COALESCE(cs.quantity, p.stock_quantity, 0) - COALESCE(
        (SELECT SUM(er.quantidade) 
         FROM estoque_reservas er 
         WHERE er.produto_id = p.id AND er.status = 'ativo'), 
        0
    ) AS estoque_disponivel
FROM products p
LEFT JOIN current_stock cs ON cs.product_id = p.id AND cs.location_id = 1
LEFT JOIN produto_especificacoes_tecnicas pet ON pet.produto_id = p.id
WHERE p.active = 1;

-- -----------------------------------------------------
-- 4. Função para buscar produtos com DNA similar
-- -----------------------------------------------------
DELIMITER //

CREATE FUNCTION IF NOT EXISTS fn_calcular_similaridade_dna(
    dna1 VARCHAR(100),
    dna2 VARCHAR(100)
) RETURNS INT
DETERMINISTIC
BEGIN
    -- Retorna um score de similaridade (0-100)
    -- 100 = exato, 80+ = derivável, 50+ = parcial
    DECLARE score INT DEFAULT 0;
    DECLARE partes1 VARCHAR(100);
    DECLARE partes2 VARCHAR(100);
    
    IF dna1 IS NULL OR dna2 IS NULL THEN
        RETURN 0;
    END IF;
    
    IF dna1 = dna2 THEN
        RETURN 100;
    END IF;
    
    -- Comparar tipo (primeira parte)
    IF SUBSTRING_INDEX(dna1, '-', 1) = SUBSTRING_INDEX(dna2, '-', 1) THEN
        SET score = score + 30;
    END IF;
    
    -- Comparar material (segunda parte)
    IF SUBSTRING_INDEX(SUBSTRING_INDEX(dna1, '-', 2), '-', -1) = 
       SUBSTRING_INDEX(SUBSTRING_INDEX(dna2, '-', 2), '-', -1) THEN
        SET score = score + 30;
    END IF;
    
    -- Comparar perfil (terceira parte)
    IF SUBSTRING_INDEX(SUBSTRING_INDEX(dna1, '-', 3), '-', -1) = 
       SUBSTRING_INDEX(SUBSTRING_INDEX(dna2, '-', 3), '-', -1) THEN
        SET score = score + 20;
    END IF;
    
    -- Comparar dureza (quarta parte)
    IF SUBSTRING_INDEX(SUBSTRING_INDEX(dna1, '-', 4), '-', -1) = 
       SUBSTRING_INDEX(SUBSTRING_INDEX(dna2, '-', 4), '-', -1) THEN
        SET score = score + 10;
    END IF;
    
    -- Comparar lonas (quinta parte)
    IF SUBSTRING_INDEX(SUBSTRING_INDEX(dna1, '-', 5), '-', -1) = 
       SUBSTRING_INDEX(SUBSTRING_INDEX(dna2, '-', 5), '-', -1) THEN
        SET score = score + 10;
    END IF;
    
    RETURN score;
END //

DELIMITER ;

-- -----------------------------------------------------
-- 5. Stored Procedure para buscar estoque com DNA similar
-- -----------------------------------------------------
DELIMITER //

CREATE PROCEDURE IF NOT EXISTS sp_buscar_estoque_dna_similar(
    IN p_produto_id INT,
    IN p_quantidade_necessaria DECIMAL(15,4),
    IN p_largura_mm DECIMAL(10,2),
    IN p_comprimento_mm DECIMAL(10,2)
)
BEGIN
    DECLARE v_codigo_dna VARCHAR(100);
    DECLARE v_tipo_correia_id INT;
    DECLARE v_material_id INT;
    
    -- Buscar DNA do produto solicitado
    SELECT codigo_dna, tipo_correia_id, material_base_id
    INTO v_codigo_dna, v_tipo_correia_id, v_material_id
    FROM produto_especificacoes_tecnicas
    WHERE produto_id = p_produto_id;
    
    -- Retornar produtos com DNA similar e estoque disponível
    SELECT 
        ve.produto_id,
        ve.produto_nome,
        ve.produto_codigo,
        ve.codigo_dna,
        ve.largura_mm AS largura_estoque,
        ve.comprimento_mm AS comprimento_estoque,
        ve.estoque_disponivel,
        LEAST(ve.estoque_disponivel, p_quantidade_necessaria) AS quantidade_alocar,
        CASE 
            WHEN ve.codigo_dna = v_codigo_dna 
                 AND ve.largura_mm = p_largura_mm 
                 AND ve.comprimento_mm = p_comprimento_mm THEN 'EXATO'
            WHEN ve.tipo_correia_id = v_tipo_correia_id 
                 AND ve.material_base_id = v_material_id
                 AND ve.largura_mm >= p_largura_mm 
                 AND ve.comprimento_mm >= p_comprimento_mm THEN 'DERIVAVEL'
            ELSE 'PARCIAL'
        END AS tipo_match,
        fn_calcular_similaridade_dna(v_codigo_dna, ve.codigo_dna) AS score_similaridade
    FROM vw_estoque_disponivel ve
    WHERE ve.produto_id != p_produto_id
      AND ve.estoque_disponivel > 0
      AND ve.codigo_dna IS NOT NULL
      AND (
          -- Match exato de DNA
          ve.codigo_dna = v_codigo_dna
          OR 
          -- Match por tipo e material (pode derivar)
          (ve.tipo_correia_id = v_tipo_correia_id AND ve.material_base_id = v_material_id)
      )
    ORDER BY 
        -- Prioridade: exato > derivável > parcial
        CASE 
            WHEN ve.codigo_dna = v_codigo_dna AND ve.largura_mm = p_largura_mm AND ve.comprimento_mm = p_comprimento_mm THEN 1
            WHEN ve.largura_mm >= p_largura_mm AND ve.comprimento_mm >= p_comprimento_mm THEN 2
            ELSE 3
        END,
        -- Depois por proximidade de dimensões
        ABS(ve.largura_mm - p_largura_mm) + ABS(ve.comprimento_mm - p_comprimento_mm),
        -- Depois por quantidade disponível
        ve.estoque_disponivel DESC
    LIMIT 10;
END //

DELIMITER ;

-- -----------------------------------------------------
-- 6. Adicionar campos extras na tabela orcamento_itens
-- -----------------------------------------------------
-- Verificar e adicionar coluna para status de alocação
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'orcamento_itens' AND COLUMN_NAME = 'status_alocacao');
SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE orcamento_itens ADD COLUMN status_alocacao ENUM(''pendente'', ''alocado'', ''parcial'', ''op_gerada'') DEFAULT ''pendente'' COMMENT ''Status da alocação de estoque''',
    'SELECT ''Coluna status_alocacao já existe''');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Verificar e adicionar coluna para quantidade do estoque
SET @col_exists2 = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'orcamento_itens' AND COLUMN_NAME = 'qtd_estoque_alocada');
SET @sql2 = IF(@col_exists2 = 0, 
    'ALTER TABLE orcamento_itens ADD COLUMN qtd_estoque_alocada DECIMAL(15,4) DEFAULT 0 COMMENT ''Quantidade alocada do estoque''',
    'SELECT ''Coluna qtd_estoque_alocada já existe''');
PREPARE stmt2 FROM @sql2;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;

-- Verificar e adicionar coluna para quantidade a produzir
SET @col_exists3 = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'orcamento_itens' AND COLUMN_NAME = 'qtd_a_produzir');
SET @sql3 = IF(@col_exists3 = 0, 
    'ALTER TABLE orcamento_itens ADD COLUMN qtd_a_produzir DECIMAL(15,4) DEFAULT 0 COMMENT ''Quantidade a ser produzida (OP)''',
    'SELECT ''Coluna qtd_a_produzir já existe''');
PREPARE stmt3 FROM @sql3;
EXECUTE stmt3;
DEALLOCATE PREPARE stmt3;

-- -----------------------------------------------------
-- 7. Índices adicionais para performance
-- -----------------------------------------------------
-- Índice para busca por DNA (usar DROP/CREATE pois MySQL não suporta IF NOT EXISTS em INDEX)
DROP INDEX IF EXISTS idx_pet_dna_busca ON produto_especificacoes_tecnicas;
CREATE INDEX idx_pet_dna_busca ON produto_especificacoes_tecnicas(tipo_correia_id, material_base_id, largura_mm, comprimento_mm);

-- -----------------------------------------------------
-- FIM DO SCRIPT
-- -----------------------------------------------------
SELECT 'Script 060_ORCAMENTO_DNA_ESTOQUE.sql executado com sucesso!' AS resultado;
