-- Adicionar campo internal_code à tabela products se não existir
ALTER TABLE products ADD COLUMN IF NOT EXISTS internal_code VARCHAR(50) DEFAULT NULL COMMENT 'Código interno do produto' AFTER id;

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

-- Inserir unidades de medida padrão
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
ALTER TABLE products ADD COLUMN IF NOT EXISTS main_supplier_id INT DEFAULT NULL COMMENT 'ID do fornecedor principal' AFTER tax_benefits;

-- Adicionar chave estrangeira para main_supplier_id se não existir
ALTER TABLE products 
ADD CONSTRAINT IF NOT EXISTS fk_products_supplier 
FOREIGN KEY (main_supplier_id) REFERENCES suppliers(id);

-- Adicionar campo max_discount à tabela products se não existir
ALTER TABLE products ADD COLUMN IF NOT EXISTS max_discount DECIMAL(10,2) DEFAULT NULL COMMENT 'Desconto máximo permitido (%)' AFTER price;

-- Adicionar campo stock_quantity à tabela products se não existir
ALTER TABLE products ADD COLUMN IF NOT EXISTS stock_quantity DECIMAL(10,2) DEFAULT 0 COMMENT 'Quantidade atual em estoque' AFTER main_customers;

-- Adicionar campo lot_control à tabela products se não existir
ALTER TABLE products ADD COLUMN IF NOT EXISTS lot_control TINYINT(1) DEFAULT 0 COMMENT 'Produto controlado por lote?' AFTER volume_m3;
