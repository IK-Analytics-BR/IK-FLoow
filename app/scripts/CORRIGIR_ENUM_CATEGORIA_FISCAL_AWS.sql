-- ========================================
-- CORRIGIR ENUM CATEGORIA_FISCAL - ADICIONAR 'produto'
-- O código local usa 'produto', então o banco precisa aceitar este valor
-- ========================================

USE supply_chain_system;

-- ========================================
-- MODIFICAR ENUM EM PRODUCTS
-- ========================================

SELECT '📦 Modificando ENUM em PRODUCTS...' as status;

-- Modificar coluna para incluir 'produto'
ALTER TABLE products 
MODIFY COLUMN categoria_fiscal ENUM('servico', 'materia_prima', 'consumo_interno', 'produto_final', 'produto') DEFAULT NULL;

SELECT '✅ ENUM modificado em PRODUCTS!' as status;

-- ========================================
-- MODIFICAR ENUM EM PRODUCT_CATEGORIES
-- ========================================

SELECT '📁 Modificando ENUM em PRODUCT_CATEGORIES...' as status;

-- Modificar coluna para incluir 'produto'
ALTER TABLE product_categories 
MODIFY COLUMN categoria_fiscal ENUM('servico', 'materia_prima', 'consumo_interno', 'produto_final', 'produto') DEFAULT NULL;

SELECT '✅ ENUM modificado em PRODUCT_CATEGORIES!' as status;

-- ========================================
-- VERIFICAÇÃO
-- ========================================

SELECT '========================================' as '';
SELECT '🔍 VERIFICAÇÃO - ENUM ATUALIZADO' as '';
SELECT '========================================' as '';

-- Verificar PRODUCTS
SELECT 'PRODUCTS' as tabela, column_type
FROM information_schema.COLUMNS
WHERE table_schema = 'supply_chain_system'
AND table_name = 'products'
AND column_name = 'categoria_fiscal';

-- Verificar PRODUCT_CATEGORIES
SELECT 'PRODUCT_CATEGORIES' as tabela, column_type
FROM information_schema.COLUMNS
WHERE table_schema = 'supply_chain_system'
AND table_name = 'product_categories'
AND column_name = 'categoria_fiscal';

-- Deve mostrar:
-- enum('servico','materia_prima','consumo_interno','produto_final','produto')

SELECT '========================================' as '';
SELECT '✅ ENUM CORRIGIDO COM SUCESSO!' as '';
SELECT 'Agora aceita os valores:' as '';
SELECT '  - servico' as '';
SELECT '  - materia_prima' as '';
SELECT '  - consumo_interno' as '';
SELECT '  - produto_final' as '';
SELECT '  - produto (ADICIONADO)' as '';
SELECT '========================================' as '';
