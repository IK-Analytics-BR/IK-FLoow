-- =====================================================
-- ADICIONAR CAMPO categoria_fiscal NA TABELA product_categories
-- Data: 28/10/2025
-- Objetivo: Classificar categorias como Produto, Serviço, Matéria Prima ou Consumo Interno
-- =====================================================

USE supply_chain_system;

-- Adicionar coluna categoria_fiscal
ALTER TABLE product_categories
ADD COLUMN categoria_fiscal ENUM('produto', 'servico', 'materia_prima', 'consumo_interno') 
NOT NULL DEFAULT 'produto' 
AFTER description;

-- Desabilitar safe update mode temporariamente
SET SQL_SAFE_UPDATES = 0;

-- Atualizar categorias existentes baseado no nome (se aplicável)
UPDATE product_categories SET categoria_fiscal = 'produto' WHERE LOWER(name) LIKE '%produto%';
UPDATE product_categories SET categoria_fiscal = 'servico' WHERE LOWER(name) LIKE '%servi%';
UPDATE product_categories SET categoria_fiscal = 'materia_prima' WHERE LOWER(name) LIKE '%mat%ria%prima%';
UPDATE product_categories SET categoria_fiscal = 'consumo_interno' WHERE LOWER(name) LIKE '%consumo%';

-- Reabilitar safe update mode
SET SQL_SAFE_UPDATES = 1;

-- Verificar resultado
SELECT 
    id,
    name,
    categoria_fiscal,
    description
FROM product_categories
WHERE active = TRUE
ORDER BY categoria_fiscal, name;

-- =====================================================
-- FIM DO SCRIPT
-- =====================================================
