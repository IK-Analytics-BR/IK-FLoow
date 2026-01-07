-- =====================================================
-- FASE 1: Sistema DNA de Produto - Especificações Técnicas
-- Data: 27/12/2025
-- =====================================================

-- -----------------------------------------------------
-- 1. Tabela de Tipos de Correia (lookup)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS tipos_correia (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(10) NOT NULL UNIQUE COMMENT 'Código para DNA: SIN, PV, TRA, etc',
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    ativo TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO tipos_correia (codigo, nome, descricao) VALUES
('SIN', 'Sincronizada', 'Correias sincronizadas com dentes'),
('PV', 'PV/Poly-V', 'Correias em V múltiplo'),
('TRA', 'Transportadora', 'Correias para transporte de materiais'),
('PLA', 'Plana', 'Correias planas sem dentes'),
('MOD', 'Modular', 'Correias modulares plásticas'),
('DEN', 'Dentada', 'Correias dentadas gerais'),
('RED', 'Redonda', 'Correias de seção redonda'),
('TRA', 'Trapezoidal', 'Correias trapezoidais em V')
ON DUPLICATE KEY UPDATE nome = VALUES(nome);

-- -----------------------------------------------------
-- 2. Tabela de Materiais Base (lookup)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS materiais_correia (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(10) NOT NULL UNIQUE COMMENT 'Código para DNA: PU, PVC, BOR, etc',
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    ativo TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO materiais_correia (codigo, nome, descricao) VALUES
('PU', 'Poliuretano', 'Poliuretano termoplástico'),
('PVC', 'PVC', 'Policloreto de vinila'),
('BOR', 'Borracha', 'Borracha natural ou sintética'),
('NBR', 'Nitrílica', 'Borracha nitrílica'),
('SIL', 'Silicone', 'Silicone'),
('NEO', 'Neoprene', 'Borracha de cloropreno'),
('EPD', 'EPDM', 'Etileno-propileno-dieno'),
('TFL', 'Teflon/PTFE', 'Politetrafluoretileno'),
('FIB', 'Fibra', 'Fibra de vidro ou aramida')
ON DUPLICATE KEY UPDATE nome = VALUES(nome);

-- -----------------------------------------------------
-- 3. Tabela de Perfis de Correia (lookup)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS perfis_correia (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE COMMENT 'Código para DNA',
    tipo_correia_codigo VARCHAR(10) COMMENT 'Tipo de correia compatível',
    nome VARCHAR(100) NOT NULL,
    passo_padrao_mm DECIMAL(10,2) COMMENT 'Passo padrão em mm',
    descricao TEXT,
    ativo TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO perfis_correia (codigo, tipo_correia_codigo, nome, passo_padrao_mm) VALUES
-- Sincronizadas métricas
('T2.5', 'SIN', 'T2.5', 2.5),
('T5', 'SIN', 'T5', 5.0),
('T10', 'SIN', 'T10', 10.0),
('T20', 'SIN', 'T20', 20.0),
('AT5', 'SIN', 'AT5', 5.0),
('AT10', 'SIN', 'AT10', 10.0),
('AT20', 'SIN', 'AT20', 20.0),
('HTD3M', 'SIN', 'HTD 3M', 3.0),
('HTD5M', 'SIN', 'HTD 5M', 5.0),
('HTD8M', 'SIN', 'HTD 8M', 8.0),
('HTD14M', 'SIN', 'HTD 14M', 14.0),
-- Sincronizadas polegadas
('MXL', 'SIN', 'MXL', 2.032),
('XL', 'SIN', 'XL', 5.08),
('L', 'SIN', 'L', 9.525),
('H', 'SIN', 'H', 12.7),
('XH', 'SIN', 'XH', 22.225),
('XXH', 'SIN', 'XXH', 31.75),
-- PV/Poly-V
('PJ', 'PV', 'PJ', 2.34),
('PK', 'PV', 'PK', 3.56),
('PL', 'PV', 'PL', 4.7),
('PM', 'PV', 'PM', 9.4),
-- Trapezoidais
('A', 'TRA', 'Perfil A', NULL),
('B', 'TRA', 'Perfil B', NULL),
('C', 'TRA', 'Perfil C', NULL),
('D', 'TRA', 'Perfil D', NULL),
('SPZ', 'TRA', 'SPZ', NULL),
('SPA', 'TRA', 'SPA', NULL),
('SPB', 'TRA', 'SPB', NULL),
('SPC', 'TRA', 'SPC', NULL)
ON DUPLICATE KEY UPDATE nome = VALUES(nome);

-- -----------------------------------------------------
-- 4. Tabela Principal de Especificações Técnicas
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS produto_especificacoes_tecnicas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    produto_id INT NOT NULL,
    
    -- DIMENSÕES PRINCIPAIS
    largura_mm DECIMAL(10,2) COMMENT 'Largura em milímetros',
    comprimento_mm DECIMAL(10,2) COMMENT 'Comprimento em milímetros',
    espessura_mm DECIMAL(10,2) COMMENT 'Espessura total em milímetros',
    
    -- TIPO E MATERIAL (referências)
    tipo_correia_id INT COMMENT 'FK tipos_correia',
    material_base_id INT COMMENT 'FK materiais_correia',
    perfil_id INT COMMENT 'FK perfis_correia',
    
    -- CARACTERÍSTICAS ADICIONAIS
    material_revestimento VARCHAR(100) COMMENT 'Revestimento superficial',
    cor VARCHAR(50),
    dureza_shore DECIMAL(5,2) COMMENT 'Dureza Shore A',
    
    -- PARA SINCRONIZADAS
    passo_mm DECIMAL(10,2) COMMENT 'Passo em mm (sobreescreve perfil)',
    numero_dentes INT COMMENT 'Número de dentes',
    largura_dente_mm DECIMAL(10,2) COMMENT 'Largura do dente',
    
    -- LONAS E CAMADAS
    numero_lonas INT COMMENT 'Quantidade de lonas',
    tipo_lona VARCHAR(50) COMMENT 'EP, NN, Poliéster, Nylon, etc',
    reforco VARCHAR(100) COMMENT 'Tipo de reforço: Aço, Kevlar, Fibra de vidro',
    
    -- EMENDAS E ACABAMENTO
    tipo_emenda VARCHAR(50) COMMENT 'Vulcanizada, Mecânica, Sem emenda, Soldada',
    acabamento_borda VARCHAR(50) COMMENT 'Selada, Cortada, Fresada',
    
    -- CARACTERÍSTICAS OPERACIONAIS
    temperatura_max DECIMAL(5,1) COMMENT 'Temperatura máxima operação °C',
    temperatura_min DECIMAL(5,1) COMMENT 'Temperatura mínima operação °C',
    velocidade_max DECIMAL(10,2) COMMENT 'Velocidade máxima m/s',
    carga_max_kg DECIMAL(10,2) COMMENT 'Carga máxima suportada kg',
    
    -- APLICAÇÃO
    aplicacao VARCHAR(200) COMMENT 'Uso: Transporte, Sincronização, Elevação',
    ambiente VARCHAR(100) COMMENT 'Ambiente: Alimentício, Industrial, Químico',
    
    -- NORMAS E CERTIFICAÇÕES
    norma_tecnica VARCHAR(100) COMMENT 'ISO, DIN, ABNT, etc',
    certificacoes VARCHAR(200) COMMENT 'FDA, ATEX, etc',
    
    -- CÓDIGO DNA (gerado automaticamente)
    codigo_dna VARCHAR(100) COMMENT 'Código único para matching',
    
    -- OBSERVAÇÕES
    observacoes_tecnicas TEXT,
    
    -- METADADOS
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    created_by INT,
    updated_by INT,
    
    FOREIGN KEY (produto_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (tipo_correia_id) REFERENCES tipos_correia(id),
    FOREIGN KEY (material_base_id) REFERENCES materiais_correia(id),
    FOREIGN KEY (perfil_id) REFERENCES perfis_correia(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (updated_by) REFERENCES users(id),
    
    UNIQUE INDEX idx_produto (produto_id),
    INDEX idx_tipo_correia (tipo_correia_id),
    INDEX idx_material (material_base_id),
    INDEX idx_perfil (perfil_id),
    INDEX idx_codigo_dna (codigo_dna),
    INDEX idx_dimensoes (largura_mm, comprimento_mm, espessura_mm)
);

-- -----------------------------------------------------
-- 5. Adicionar campo de tipo industrial na products
-- -----------------------------------------------------
-- Verificar e adicionar coluna tipo_produto_industrial
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'products' AND COLUMN_NAME = 'tipo_produto_industrial');
SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE products ADD COLUMN tipo_produto_industrial VARCHAR(50) DEFAULT NULL COMMENT ''correia, componente, materia_prima, servico''',
    'SELECT ''Coluna tipo_produto_industrial já existe''');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Verificar e adicionar coluna tem_especificacao_tecnica
SET @col_exists2 = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'products' AND COLUMN_NAME = 'tem_especificacao_tecnica');
SET @sql2 = IF(@col_exists2 = 0, 
    'ALTER TABLE products ADD COLUMN tem_especificacao_tecnica TINYINT(1) DEFAULT 0 COMMENT ''1 se possui especificação técnica cadastrada''',
    'SELECT ''Coluna tem_especificacao_tecnica já existe''');
PREPARE stmt2 FROM @sql2;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;

-- -----------------------------------------------------
-- 6. Função para Gerar Código DNA
-- -----------------------------------------------------
DELIMITER //

CREATE FUNCTION IF NOT EXISTS fn_gerar_codigo_dna(
    p_tipo_codigo VARCHAR(10),
    p_material_codigo VARCHAR(10),
    p_perfil_codigo VARCHAR(20),
    p_dureza DECIMAL(5,2),
    p_lonas INT,
    p_emenda VARCHAR(50)
) RETURNS VARCHAR(100)
DETERMINISTIC
BEGIN
    DECLARE v_dna VARCHAR(100);
    DECLARE v_emenda_cod VARCHAR(3);
    
    -- Código da emenda
    SET v_emenda_cod = CASE 
        WHEN p_emenda LIKE '%Vulcan%' THEN 'VUL'
        WHEN p_emenda LIKE '%Mec%' THEN 'MEC'
        WHEN p_emenda LIKE '%Sold%' THEN 'SOL'
        WHEN p_emenda LIKE '%Sem%' OR p_emenda IS NULL THEN 'SEM'
        ELSE 'OUT'
    END;
    
    -- Montar DNA
    SET v_dna = CONCAT(
        COALESCE(p_tipo_codigo, 'XXX'), '-',
        COALESCE(p_material_codigo, 'XXX'), '-',
        COALESCE(p_perfil_codigo, 'XXX'), '-',
        COALESCE(CAST(FLOOR(p_dureza) AS CHAR), '00'), '-',
        COALESCE(CAST(p_lonas AS CHAR), '0'), 'L-',
        v_emenda_cod
    );
    
    RETURN v_dna;
END //

DELIMITER ;

-- -----------------------------------------------------
-- 7. Trigger para Atualizar DNA Automaticamente
-- -----------------------------------------------------
DELIMITER //

CREATE TRIGGER IF NOT EXISTS trg_especificacoes_before_insert
BEFORE INSERT ON produto_especificacoes_tecnicas
FOR EACH ROW
BEGIN
    DECLARE v_tipo_cod VARCHAR(10);
    DECLARE v_mat_cod VARCHAR(10);
    DECLARE v_perfil_cod VARCHAR(20);
    
    -- Buscar códigos
    SELECT codigo INTO v_tipo_cod FROM tipos_correia WHERE id = NEW.tipo_correia_id;
    SELECT codigo INTO v_mat_cod FROM materiais_correia WHERE id = NEW.material_base_id;
    SELECT codigo INTO v_perfil_cod FROM perfis_correia WHERE id = NEW.perfil_id;
    
    -- Gerar DNA
    SET NEW.codigo_dna = fn_gerar_codigo_dna(
        v_tipo_cod,
        v_mat_cod,
        v_perfil_cod,
        NEW.dureza_shore,
        NEW.numero_lonas,
        NEW.tipo_emenda
    );
    
    -- Atualizar flag na products
    UPDATE products SET tem_especificacao_tecnica = 1 WHERE id = NEW.produto_id;
END //

CREATE TRIGGER IF NOT EXISTS trg_especificacoes_before_update
BEFORE UPDATE ON produto_especificacoes_tecnicas
FOR EACH ROW
BEGIN
    DECLARE v_tipo_cod VARCHAR(10);
    DECLARE v_mat_cod VARCHAR(10);
    DECLARE v_perfil_cod VARCHAR(20);
    
    -- Buscar códigos
    SELECT codigo INTO v_tipo_cod FROM tipos_correia WHERE id = NEW.tipo_correia_id;
    SELECT codigo INTO v_mat_cod FROM materiais_correia WHERE id = NEW.material_base_id;
    SELECT codigo INTO v_perfil_cod FROM perfis_correia WHERE id = NEW.perfil_id;
    
    -- Gerar DNA
    SET NEW.codigo_dna = fn_gerar_codigo_dna(
        v_tipo_cod,
        v_mat_cod,
        v_perfil_cod,
        NEW.dureza_shore,
        NEW.numero_lonas,
        NEW.tipo_emenda
    );
END //

CREATE TRIGGER IF NOT EXISTS trg_especificacoes_after_delete
AFTER DELETE ON produto_especificacoes_tecnicas
FOR EACH ROW
BEGIN
    UPDATE products SET tem_especificacao_tecnica = 0 WHERE id = OLD.produto_id;
END //

DELIMITER ;

-- -----------------------------------------------------
-- 8. View para Consulta Completa de Especificações
-- -----------------------------------------------------
CREATE OR REPLACE VIEW vw_produtos_especificacoes AS
SELECT 
    p.id AS produto_id,
    p.internal_code,
    p.name AS produto_nome,
    p.tipo_produto_industrial,
    e.id AS especificacao_id,
    e.codigo_dna,
    
    -- Dimensões
    e.largura_mm,
    e.comprimento_mm,
    e.espessura_mm,
    
    -- Tipo e Material
    tc.codigo AS tipo_codigo,
    tc.nome AS tipo_nome,
    mc.codigo AS material_codigo,
    mc.nome AS material_nome,
    pc.codigo AS perfil_codigo,
    pc.nome AS perfil_nome,
    
    -- Características
    e.cor,
    e.dureza_shore,
    e.passo_mm,
    e.numero_dentes,
    e.numero_lonas,
    e.tipo_lona,
    e.tipo_emenda,
    e.acabamento_borda,
    
    -- Operacionais
    e.temperatura_min,
    e.temperatura_max,
    e.aplicacao,
    e.ambiente,
    
    -- Estoque
    p.stock_quantity,
    p.min_stock
    
FROM products p
LEFT JOIN produto_especificacoes_tecnicas e ON e.produto_id = p.id
LEFT JOIN tipos_correia tc ON tc.id = e.tipo_correia_id
LEFT JOIN materiais_correia mc ON mc.id = e.material_base_id
LEFT JOIN perfis_correia pc ON pc.id = e.perfil_id
WHERE p.active = 1;

-- -----------------------------------------------------
-- 9. Dados de Exemplo
-- -----------------------------------------------------
-- Atualizar produto ID 1 como correia
UPDATE products SET tipo_produto_industrial = 'correia' WHERE id = 1;

-- Inserir especificação de exemplo para produto 1
INSERT INTO produto_especificacoes_tecnicas (
    produto_id,
    largura_mm,
    comprimento_mm,
    espessura_mm,
    tipo_correia_id,
    material_base_id,
    perfil_id,
    cor,
    dureza_shore,
    numero_lonas,
    tipo_lona,
    tipo_emenda,
    acabamento_borda,
    temperatura_min,
    temperatura_max,
    aplicacao,
    created_by
) VALUES (
    1,
    200,
    6000,
    6.5,
    (SELECT id FROM tipos_correia WHERE codigo = 'SIN'),
    (SELECT id FROM materiais_correia WHERE codigo = 'PU'),
    (SELECT id FROM perfis_correia WHERE codigo = 'H'),
    'Preto',
    65,
    2,
    'Poliéster',
    'Vulcanizada',
    'Selada',
    -10,
    80,
    'Transporte industrial',
    1
) ON DUPLICATE KEY UPDATE updated_at = NOW();

-- Verificar
SELECT * FROM vw_produtos_especificacoes WHERE produto_id = 1;

SELECT 'FASE 1 - Tabelas de Especificações Técnicas criadas com sucesso!' AS status;
