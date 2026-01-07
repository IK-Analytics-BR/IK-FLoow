-- Adicionar coluna NCM à tabela products
ALTER TABLE products ADD COLUMN IF NOT EXISTS ncm VARCHAR(8) DEFAULT NULL COMMENT 'Nomenclatura Comum do Mercosul' AFTER unit_measure;
