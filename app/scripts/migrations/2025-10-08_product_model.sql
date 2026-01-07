-- Tabela para Modelos de Produtos
CREATE TABLE IF NOT EXISTS product_models (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_product_models_name (name)
);

-- Índice para busca por nome
CREATE INDEX IF NOT EXISTS idx_product_models_name ON product_models(name);

-- Adicionar coluna model_id em products
ALTER TABLE products ADD COLUMN IF NOT EXISTS model_id INT NULL;
ALTER TABLE products ADD CONSTRAINT IF NOT EXISTS fk_products_model FOREIGN KEY (model_id) REFERENCES product_models(id);
