-- Tabela para Marcas de Produtos
CREATE TABLE IF NOT EXISTS product_brands (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabela para Grupos de Produtos
CREATE TABLE IF NOT EXISTS product_groups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabela para Subgrupos de Produtos
CREATE TABLE IF NOT EXISTS product_subgroups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    group_id INT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES product_groups(id)
);

-- Adicionar índices para melhorar a performance
CREATE INDEX idx_product_brands_name ON product_brands(name);
CREATE INDEX idx_product_groups_name ON product_groups(name);
CREATE INDEX idx_product_subgroups_name ON product_subgroups(name);
CREATE INDEX idx_product_subgroups_group_id ON product_subgroups(group_id);

-- Adicionar campo para relacionar produtos com marcas, grupos e subgrupos (se necessário)
ALTER TABLE products ADD COLUMN IF NOT EXISTS brand_id INT;
ALTER TABLE products ADD COLUMN IF NOT EXISTS group_id INT;
ALTER TABLE products ADD COLUMN IF NOT EXISTS subgroup_id INT;

-- Adicionar chaves estrangeiras para relacionar produtos com marcas, grupos e subgrupos
ALTER TABLE products ADD CONSTRAINT fk_products_brand FOREIGN KEY (brand_id) REFERENCES product_brands(id);
ALTER TABLE products ADD CONSTRAINT fk_products_group FOREIGN KEY (group_id) REFERENCES product_groups(id);
ALTER TABLE products ADD CONSTRAINT fk_products_subgroup FOREIGN KEY (subgroup_id) REFERENCES product_subgroups(id);
