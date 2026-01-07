-- ========================================
-- CORREÇÃO SEGURA - CATEGORIA_FISCAL
-- Ignora erros se as colunas já existirem
-- ========================================

USE supply_chain_system;

-- ========================================
-- ADICIONAR COLUNA EM PRODUCTS
-- ========================================

-- Tente executar este comando:
ALTER TABLE products 
ADD COLUMN categoria_fiscal ENUM('servico', 'materia_prima', 'consumo_interno', 'produto_final') DEFAULT NULL;

-- Se der erro "Duplicate column name 'categoria_fiscal'" = IGNORE, a coluna já existe!

-- ========================================
-- ADICIONAR COLUNA EM PRODUCT_CATEGORIES
-- ========================================

-- Tente executar este comando:
ALTER TABLE product_categories 
ADD COLUMN categoria_fiscal ENUM('servico', 'materia_prima', 'consumo_interno', 'produto_final') DEFAULT NULL;

-- Se der erro "Duplicate column name 'categoria_fiscal'" = IGNORE, a coluna já existe!

-- ========================================
-- ADICIONAR ÍNDICES
-- ========================================

-- Tente executar estes comandos:
CREATE INDEX idx_categoria_fiscal_products ON products(categoria_fiscal);
CREATE INDEX idx_categoria_fiscal_categories ON product_categories(categoria_fiscal);

-- Se der erro "Duplicate key name" = IGNORE, o índice já existe!

-- ========================================
-- VERIFICAÇÃO FINAL
-- ========================================

-- Verificar PRODUCTS
SELECT 'PRODUCTS:' as tabela, column_name, column_type
FROM information_schema.COLUMNS
WHERE table_schema = 'supply_chain_system'
AND table_name = 'products'
AND column_name = 'categoria_fiscal';

-- Verificar PRODUCT_CATEGORIES
SELECT 'PRODUCT_CATEGORIES:' as tabela, column_name, column_type
FROM information_schema.COLUMNS
WHERE table_schema = 'supply_chain_system'
AND table_name = 'product_categories'
AND column_name = 'categoria_fiscal';

-- Se ambas as queries retornarem 1 linha cada = SUCESSO! ✅
