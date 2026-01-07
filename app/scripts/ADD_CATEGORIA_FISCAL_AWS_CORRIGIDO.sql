-- ========================================
-- ADICIONAR COLUNA CATEGORIA_FISCAL - VERSÃO CORRIGIDA
-- Compatível com todas as versões do MySQL
-- ========================================

USE supply_chain_system;

-- ========================================
-- MÉTODO 1: Verificar e adicionar (RECOMENDADO)
-- ========================================

-- Criar procedure temporária para adicionar coluna se não existir
DELIMITER $$

DROP PROCEDURE IF EXISTS add_categoria_fiscal$$

CREATE PROCEDURE add_categoria_fiscal()
BEGIN
    -- Verificar se a coluna já existe
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.COLUMNS 
        WHERE table_schema = DATABASE()
        AND table_name = 'products' 
        AND column_name = 'categoria_fiscal'
    ) THEN
        -- Adicionar coluna
        ALTER TABLE products 
        ADD COLUMN categoria_fiscal ENUM('servico', 'materia_prima', 'consumo_interno', 'produto_final') DEFAULT NULL 
        AFTER category_id;
        
        SELECT '✅ Coluna categoria_fiscal CRIADA com sucesso!' as resultado;
    ELSE
        SELECT '⚠️ Coluna categoria_fiscal JÁ EXISTE!' as resultado;
    END IF;
END$$

DELIMITER ;

-- Executar procedure
CALL add_categoria_fiscal();

-- Remover procedure
DROP PROCEDURE IF EXISTS add_categoria_fiscal;

-- ========================================
-- Adicionar índice
-- ========================================

-- Criar procedure para adicionar índice se não existir
DELIMITER $$

DROP PROCEDURE IF EXISTS add_index_categoria_fiscal$$

CREATE PROCEDURE add_index_categoria_fiscal()
BEGIN
    -- Verificar se o índice já existe
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.STATISTICS 
        WHERE table_schema = DATABASE()
        AND table_name = 'products' 
        AND index_name = 'idx_categoria_fiscal'
    ) THEN
        -- Adicionar índice
        CREATE INDEX idx_categoria_fiscal ON products(categoria_fiscal);
        
        SELECT '✅ Índice idx_categoria_fiscal CRIADO com sucesso!' as resultado;
    ELSE
        SELECT '⚠️ Índice idx_categoria_fiscal JÁ EXISTE!' as resultado;
    END IF;
END$$

DELIMITER ;

-- Executar procedure
CALL add_index_categoria_fiscal();

-- Remover procedure
DROP PROCEDURE IF EXISTS add_index_categoria_fiscal;

-- ========================================
-- VERIFICAÇÃO FINAL
-- ========================================

SELECT '========================================' as '';
SELECT '📊 VERIFICAÇÃO DA COLUNA CATEGORIA_FISCAL' as '';
SELECT '========================================' as '';

-- Verificar se a coluna existe
SELECT 
    column_name as 'Coluna',
    column_type as 'Tipo',
    is_nullable as 'Nullable',
    column_default as 'Default',
    '✅ OK' as 'Status'
FROM information_schema.COLUMNS
WHERE table_schema = DATABASE()
AND table_name = 'products'
AND column_name = 'categoria_fiscal';

-- Verificar se o índice existe
SELECT 
    index_name as 'Índice',
    column_name as 'Coluna',
    '✅ OK' as 'Status'
FROM information_schema.STATISTICS
WHERE table_schema = DATABASE()
AND table_name = 'products'
AND index_name = 'idx_categoria_fiscal';

-- Mostrar estrutura da tabela
SELECT '========================================' as '';
SELECT 'ESTRUTURA DA TABELA PRODUCTS:' as '';
SELECT '========================================' as '';

DESCRIBE products;

SELECT '========================================' as '';
SELECT '✅ SCRIPT EXECUTADO COM SUCESSO!' as '';
SELECT '========================================' as '';
