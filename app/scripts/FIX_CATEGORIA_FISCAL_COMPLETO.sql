-- ========================================
-- CORREÇÃO COMPLETA - CATEGORIA_FISCAL
-- Adiciona coluna em PRODUCTS e PRODUCT_CATEGORIES
-- ========================================

USE supply_chain_system;

-- ========================================
-- 1. ADICIONAR COLUNA EM PRODUCTS
-- ========================================

SELECT '📦 Adicionando coluna em PRODUCTS...' as status;

ALTER TABLE products 
ADD COLUMN categoria_fiscal ENUM('servico', 'materia_prima', 'consumo_interno', 'produto_final') DEFAULT NULL;

SELECT '✅ Coluna adicionada em PRODUCTS!' as status;

-- ========================================
-- 2. ADICIONAR COLUNA EM PRODUCT_CATEGORIES
-- ========================================

SELECT '📁 Adicionando coluna em PRODUCT_CATEGORIES...' as status;

ALTER TABLE product_categories 
ADD COLUMN categoria_fiscal ENUM('servico', 'materia_prima', 'consumo_interno', 'produto_final') DEFAULT NULL;

SELECT '✅ Coluna adicionada em PRODUCT_CATEGORIES!' as status;

-- ========================================
-- 3. ADICIONAR ÍNDICES
-- ========================================

SELECT '📊 Adicionando índices...' as status;

CREATE INDEX idx_categoria_fiscal ON products(categoria_fiscal);
CREATE INDEX idx_categoria_fiscal ON product_categories(categoria_fiscal);

SELECT '✅ Índices adicionados!' as status;

-- ========================================
-- 4. VERIFICAÇÃO
-- ========================================

SELECT '========================================' as '';
SELECT '🔍 VERIFICAÇÃO - TABELA PRODUCTS' as '';
SELECT '========================================' as '';

SELECT column_name, column_type, is_nullable
FROM information_schema.COLUMNS
WHERE table_schema = 'supply_chain_system'
AND table_name = 'products'
AND column_name = 'categoria_fiscal';

SELECT '========================================' as '';
SELECT '🔍 VERIFICAÇÃO - TABELA PRODUCT_CATEGORIES' as '';
SELECT '========================================' as '';

SELECT column_name, column_type, is_nullable
FROM information_schema.COLUMNS
WHERE table_schema = 'supply_chain_system'
AND table_name = 'product_categories'
AND column_name = 'categoria_fiscal';

SELECT '========================================' as '';
SELECT '✅ SCRIPT EXECUTADO COM SUCESSO!' as '';
SELECT 'Agora você pode usar a aplicação sem erros!' as '';
SELECT '========================================' as '';
