-- ========================================
-- ADICIONAR COLUNA CATEGORIA_FISCAL
-- Script para AWS - Correção do erro 1054
-- ========================================

USE supplychain;

-- Verificar se a coluna já existe
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN 'COLUNA JÁ EXISTE - NENHUMA AÇÃO NECESSÁRIA'
        ELSE 'COLUNA NÃO EXISTE - SERÁ CRIADA'
    END as status
FROM information_schema.COLUMNS
WHERE table_schema = DATABASE()
AND table_name = 'products'
AND column_name = 'categoria_fiscal';

-- Adicionar coluna categoria_fiscal se não existir
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS categoria_fiscal ENUM('servico', 'materia_prima', 'consumo_interno', 'produto_final') DEFAULT NULL 
AFTER category_id;

-- Adicionar índice para melhor performance
CREATE INDEX IF NOT EXISTS idx_categoria_fiscal ON products(categoria_fiscal);

-- Verificação final
SELECT 
    column_name as 'Coluna',
    column_type as 'Tipo',
    is_nullable as 'Nullable',
    column_default as 'Default',
    '✅ CRIADA COM SUCESSO' as 'Status'
FROM information_schema.COLUMNS
WHERE table_schema = DATABASE()
AND table_name = 'products'
AND column_name = 'categoria_fiscal';

-- Mostrar estrutura da tabela products
SELECT '========================================' as '';
SELECT 'ESTRUTURA ATUALIZADA DA TABELA PRODUCTS:' as '';
SELECT '========================================' as '';

DESCRIBE products;

-- Contar produtos por categoria fiscal
SELECT '========================================' as '';
SELECT 'PRODUTOS POR CATEGORIA FISCAL:' as '';
SELECT '========================================' as '';

SELECT 
    COALESCE(categoria_fiscal, 'NÃO DEFINIDA') as categoria,
    COUNT(*) as total
FROM products
GROUP BY categoria_fiscal
ORDER BY categoria_fiscal;

SELECT '========================================' as '';
SELECT '✅ COLUNA CATEGORIA_FISCAL ADICIONADA COM SUCESSO!' as '';
SELECT '========================================' as '';
