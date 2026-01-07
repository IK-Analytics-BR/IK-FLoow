-- Tabela para Categorias de Produtos
CREATE TABLE IF NOT EXISTS product_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Adicionar índice para melhorar a performance
CREATE INDEX idx_product_categories_name ON product_categories(name);

-- Adicionar campo para relacionar produtos com categorias
ALTER TABLE products ADD COLUMN IF NOT EXISTS category_id INT;

-- Adicionar chave estrangeira para relacionar produtos com categorias
ALTER TABLE products ADD CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES product_categories(id);
