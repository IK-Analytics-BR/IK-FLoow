-- Adicionar campo internal_code à tabela products se não existir
SET @col_exists_internal_code = (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'products'
      AND COLUMN_NAME = 'internal_code'
);
SET @sql_internal_code = IF(
    @col_exists_internal_code = 0,
    'ALTER TABLE products ADD COLUMN internal_code VARCHAR(50) DEFAULT NULL COMMENT ''Código interno do produto'' AFTER id',
    'SELECT ''Coluna internal_code já existe'''
);
PREPARE stmt FROM @sql_internal_code;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Criar tabela de unidades de medida se não existir
CREATE TABLE IF NOT EXISTS unit_measures (
    id INT NOT NULL AUTO_INCREMENT,
    code VARCHAR(10) NOT NULL COMMENT 'Código da unidade (ex: UN, KG, M)',
    name VARCHAR(50) NOT NULL COMMENT 'Nome da unidade (ex: Unidade, Quilograma, Metro)',
    description TEXT COMMENT 'Descrição detalhada da unidade',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY (code)
);

-- Inserir unidades de medida padrão (idempotente)
INSERT INTO unit_measures (code, name, description) VALUES
('UN', 'Unidade', 'Unidade individual do produto'),
('KG', 'Quilograma', 'Peso em quilogramas'),
('G', 'Grama', 'Peso em gramas'),
('L', 'Litro', 'Volume em litros'),
('ML', 'Mililitro', 'Volume em mililitros'),
('M', 'Metro', 'Comprimento em metros'),
('CM', 'Centímetro', 'Comprimento em centímetros'),
('M2', 'Metro Quadrado', 'Área em metros quadrados'),
('M3', 'Metro Cúbico', 'Volume em metros cúbicos'),
('CX', 'Caixa', 'Caixa com múltiplas unidades'),
('PCT', 'Pacote', 'Pacote com múltiplas unidades'),
('DZ', 'Dúzia', 'Conjunto de 12 unidades'),
('PAR', 'Par', 'Conjunto de 2 unidades')
ON DUPLICATE KEY UPDATE 
    name = VALUES(name),
    description = VALUES(description),
    active = TRUE;

-- Adicionar campo main_supplier_id à tabela products se não existir
SET @col_exists_main_supplier_id = (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'products'
      AND COLUMN_NAME = 'main_supplier_id'
);
SET @sql_main_supplier_id = IF(
    @col_exists_main_supplier_id = 0,
    'ALTER TABLE products ADD COLUMN main_supplier_id INT DEFAULT NULL COMMENT ''ID do fornecedor principal'' AFTER tax_benefits',
    'SELECT ''Coluna main_supplier_id já existe'''
);
PREPARE stmt FROM @sql_main_supplier_id;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Adicionar chave estrangeira para main_supplier_id se não existir
SET @fk_exists_supplier = (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
    WHERE CONSTRAINT_SCHEMA = DATABASE()
      AND TABLE_NAME = 'products'
      AND CONSTRAINT_NAME = 'fk_products_supplier'
);
SET @sql_fk_supplier = IF(
    @fk_exists_supplier = 0,
    'ALTER TABLE products ADD CONSTRAINT fk_products_supplier FOREIGN KEY (main_supplier_id) REFERENCES suppliers(id)',
    'SELECT ''Constraint fk_products_supplier já existe'''
);
PREPARE stmt FROM @sql_fk_supplier;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Adicionar campo max_discount à tabela products se não existir
SET @col_exists_max_discount = (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'products'
      AND COLUMN_NAME = 'max_discount'
);
SET @sql_max_discount = IF(
    @col_exists_max_discount = 0,
    'ALTER TABLE products ADD COLUMN max_discount DECIMAL(10,2) DEFAULT NULL COMMENT ''Desconto máximo permitido (%)'' AFTER price',
    'SELECT ''Coluna max_discount já existe'''
);
PREPARE stmt FROM @sql_max_discount;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Adicionar campo stock_quantity à tabela products se não existir
SET @col_exists_stock_quantity = (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'products'
      AND COLUMN_NAME = 'stock_quantity'
);
SET @sql_stock_quantity = IF(
    @col_exists_stock_quantity = 0,
    'ALTER TABLE products ADD COLUMN stock_quantity DECIMAL(10,2) DEFAULT 0 COMMENT ''Quantidade atual em estoque'' AFTER main_customers',
    'SELECT ''Coluna stock_quantity já existe'''
);
PREPARE stmt FROM @sql_stock_quantity;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Adicionar campos de unidade de compra e conversão se não existirem
SET @col_exists_purchase_unit = (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'products'
      AND COLUMN_NAME = 'purchase_unit'
);
SET @sql_purchase_unit = IF(
    @col_exists_purchase_unit = 0,
    'ALTER TABLE products ADD COLUMN purchase_unit VARCHAR(20) NULL COMMENT ''Unidade de compra (pacote, caixa, fardo etc.)'' AFTER unit_measure',
    'SELECT ''Coluna purchase_unit já existe'''
);
PREPARE stmt FROM @sql_purchase_unit;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists_purchase_factor = (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'products'
      AND COLUMN_NAME = 'purchase_factor'
);
SET @sql_purchase_factor = IF(
    @col_exists_purchase_factor = 0,
    'ALTER TABLE products ADD COLUMN purchase_factor DECIMAL(15,6) NULL COMMENT ''Quantidade da unidade base por unidade de compra'' AFTER purchase_unit',
    'SELECT ''Coluna purchase_factor já existe'''
);
PREPARE stmt FROM @sql_purchase_factor;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists_purchase_freight = (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'products'
      AND COLUMN_NAME = 'purchase_freight_value'
);
SET @sql_purchase_freight = IF(
    @col_exists_purchase_freight = 0,
    'ALTER TABLE products ADD COLUMN purchase_freight_value DECIMAL(15,6) NULL COMMENT ''Frete por unidade de compra (R$)'' AFTER last_purchase_price',
    'SELECT ''Coluna purchase_freight_value já existe'''
);
PREPARE stmt FROM @sql_purchase_freight;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists_purchase_icms = (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'products'
      AND COLUMN_NAME = 'purchase_icms_value'
);
SET @sql_purchase_icms = IF(
    @col_exists_purchase_icms = 0,
    'ALTER TABLE products ADD COLUMN purchase_icms_value DECIMAL(15,6) NULL COMMENT ''ICMS por unidade de compra (R$)'' AFTER purchase_freight_value',
    'SELECT ''Coluna purchase_icms_value já existe'''
);
PREPARE stmt FROM @sql_purchase_icms;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists_purchase_other = (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'products'
      AND COLUMN_NAME = 'purchase_other_costs_value'
);
SET @sql_purchase_other = IF(
    @col_exists_purchase_other = 0,
    'ALTER TABLE products ADD COLUMN purchase_other_costs_value DECIMAL(15,6) NULL COMMENT ''Outros custos por unidade de compra (R$)'' AFTER purchase_icms_value',
    'SELECT ''Coluna purchase_other_costs_value já existe'''
);
PREPARE stmt FROM @sql_purchase_other;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists_purchase_total = (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'products'
      AND COLUMN_NAME = 'purchase_total_cost'
);
SET @sql_purchase_total = IF(
    @col_exists_purchase_total = 0,
    'ALTER TABLE products ADD COLUMN purchase_total_cost DECIMAL(15,6) NULL COMMENT ''Custo total por unidade de compra (R$)'' AFTER purchase_other_costs_value',
    'SELECT ''Coluna purchase_total_cost já existe'''
);
PREPARE stmt FROM @sql_purchase_total;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Adicionar campo lot_control à tabela products se não existir
SET @col_exists_lot_control = (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'products'
      AND COLUMN_NAME = 'lot_control'
);
SET @sql_lot_control = IF(
    @col_exists_lot_control = 0,
    'ALTER TABLE products ADD COLUMN lot_control TINYINT(1) DEFAULT 0 COMMENT ''Produto controlado por lote?'' AFTER volume_m3',
    'SELECT ''Coluna lot_control já existe'''
);
PREPARE stmt FROM @sql_lot_control;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
