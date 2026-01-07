-- Script para adicionar novos campos à tabela de produtos

-- 1. Campos de Identificação Básica
ALTER TABLE products ADD COLUMN internal_code VARCHAR(50) NULL COMMENT 'Código interno do produto';
ALTER TABLE products ADD COLUMN unit_measure VARCHAR(20) NULL COMMENT 'Unidade de medida (un, kg, m, litro etc.)';
ALTER TABLE products ADD COLUMN photo_url VARCHAR(255) NULL COMMENT 'URL da foto do produto';

-- 2. Dados Fiscais
ALTER TABLE products ADD COLUMN ncm VARCHAR(10) NULL COMMENT 'Nomenclatura Comum do Mercosul';
ALTER TABLE products ADD COLUMN cest VARCHAR(10) NULL COMMENT 'Código Especificador da Substituição Tributária';
ALTER TABLE products ADD COLUMN cfop_in VARCHAR(10) NULL COMMENT 'CFOP padrão de entrada';
ALTER TABLE products ADD COLUMN cfop_out VARCHAR(10) NULL COMMENT 'CFOP padrão de saída';
ALTER TABLE products ADD COLUMN cst_csosn VARCHAR(10) NULL COMMENT 'Situação tributária do ICMS';
ALTER TABLE products ADD COLUMN icms_rate DECIMAL(10,2) NULL COMMENT 'Alíquota de ICMS';
ALTER TABLE products ADD COLUMN pis_rate DECIMAL(10,2) NULL COMMENT 'Alíquota de PIS';
ALTER TABLE products ADD COLUMN cofins_rate DECIMAL(10,2) NULL COMMENT 'Alíquota de COFINS';
ALTER TABLE products ADD COLUMN ipi_rate DECIMAL(10,2) NULL COMMENT 'Alíquota de IPI';
ALTER TABLE products ADD COLUMN origin TINYINT NULL COMMENT 'Origem do produto (0=nacional, 1=estrangeiro etc.)';
ALTER TABLE products ADD COLUMN tax_benefits TEXT NULL COMMENT 'Benefícios fiscais';

-- 3. Dados de Compras
ALTER TABLE products ADD COLUMN main_supplier_id INT NULL COMMENT 'ID do fornecedor principal';
ALTER TABLE products ADD COLUMN supplier_code VARCHAR(50) NULL COMMENT 'Código do produto no fornecedor';
ALTER TABLE products ADD COLUMN last_purchase_price DECIMAL(10,2) NULL COMMENT 'Último preço de compra';
ALTER TABLE products ADD COLUMN avg_delivery_time INT NULL COMMENT 'Prazo médio de entrega em dias';

-- 4. Dados de Vendas
-- Preço de venda já existe como 'price'
-- Margem de lucro já existe como 'margin'
ALTER TABLE products ADD COLUMN max_discount DECIMAL(10,2) NULL COMMENT 'Desconto máximo permitido (%)';
ALTER TABLE products ADD COLUMN main_customers TEXT NULL COMMENT 'Clientes principais que consomem o produto';

-- 5. Estoque e Logística
ALTER TABLE products ADD COLUMN stock_quantity DECIMAL(10,2) NULL COMMENT 'Quantidade em estoque atual';
ALTER TABLE products ADD COLUMN min_stock DECIMAL(10,2) NULL COMMENT 'Estoque mínimo (nível de alerta)';
ALTER TABLE products ADD COLUMN max_stock DECIMAL(10,2) NULL COMMENT 'Estoque máximo';
ALTER TABLE products ADD COLUMN location VARCHAR(100) NULL COMMENT 'Localização física (ex.: Almoxarifado A, Prateleira 3)';
ALTER TABLE products ADD COLUMN lot_number VARCHAR(50) NULL COMMENT 'Lote / Série';
ALTER TABLE products ADD COLUMN expiry_date DATE NULL COMMENT 'Data de validade';
ALTER TABLE products ADD COLUMN net_weight DECIMAL(10,3) NULL COMMENT 'Peso líquido';
ALTER TABLE products ADD COLUMN gross_weight DECIMAL(10,3) NULL COMMENT 'Peso bruto';
ALTER TABLE products ADD COLUMN length_cm DECIMAL(10,2) NULL COMMENT 'Comprimento';
ALTER TABLE products ADD COLUMN width_cm DECIMAL(10,2) NULL COMMENT 'Largura';
ALTER TABLE products ADD COLUMN height_cm DECIMAL(10,2) NULL COMMENT 'Altura';
ALTER TABLE products ADD COLUMN volume_m3 DECIMAL(10,3) NULL COMMENT 'Volume (m³)';

-- 6. Integrações / Outras Informações
-- active já existe
ALTER TABLE products ADD COLUMN lot_control BOOLEAN NULL DEFAULT FALSE COMMENT 'Produto controlado por lote?';
ALTER TABLE products ADD COLUMN serial_control BOOLEAN NULL DEFAULT FALSE COMMENT 'Produto controlado por série?';
ALTER TABLE products ADD COLUMN imported BOOLEAN NULL DEFAULT FALSE COMMENT 'Produto importado?';
ALTER TABLE products ADD COLUMN notes TEXT NULL COMMENT 'Observações gerais';

-- Criar tabela para unidades de medida
CREATE TABLE IF NOT EXISTS unit_measures (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(10) NOT NULL COMMENT 'Código da unidade (ex.: UN, KG, M)',
    name VARCHAR(50) NOT NULL COMMENT 'Nome da unidade (ex.: Unidade, Quilograma, Metro)',
    description TEXT NULL COMMENT 'Descrição da unidade',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Inserir algumas unidades de medida padrão
INSERT INTO unit_measures (code, name) VALUES 
('UN', 'Unidade'),
('KG', 'Quilograma'),
('M', 'Metro'),
('L', 'Litro'),
('CX', 'Caixa'),
('PC', 'Peça'),
('PAR', 'Par'),
('M2', 'Metro Quadrado'),
('M3', 'Metro Cúbico'),
('TON', 'Tonelada');

-- Criar tabela para histórico de preços de compra
CREATE TABLE IF NOT EXISTS purchase_price_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    supplier_id INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    purchase_date DATE NOT NULL,
    invoice_number VARCHAR(50) NULL,
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

-- Índices para melhorar a performance
CREATE INDEX idx_products_internal_code ON products(internal_code);
CREATE INDEX idx_products_barcode ON products(barcode);
CREATE INDEX idx_products_ncm ON products(ncm);
