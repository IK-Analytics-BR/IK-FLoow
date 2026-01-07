-- ========================================
-- ATUALIZAR CATEGORIA FISCAL DOS PRODUTOS
-- Script para categorizar produtos existentes
-- ========================================

USE supplychain;

-- ========================================
-- OPÇÃO 1: CATEGORIZAÇÃO AUTOMÁTICA
-- Baseada em palavras-chave no nome do produto
-- ========================================

SELECT '========================================' as '';
SELECT '🔍 INICIANDO CATEGORIZAÇÃO AUTOMÁTICA...' as '';
SELECT '========================================' as '';

-- 1. Identificar SERVIÇOS (palavras-chave)
UPDATE products 
SET categoria_fiscal = 'servico'
WHERE categoria_fiscal IS NULL
AND (
    UPPER(name) LIKE '%SERVICO%' OR
    UPPER(name) LIKE '%SERVICE%' OR
    UPPER(name) LIKE '%MÃO DE OBRA%' OR
    UPPER(name) LIKE '%MAO DE OBRA%' OR
    UPPER(name) LIKE '%HORA%' OR
    UPPER(name) LIKE '%HR%' OR
    UPPER(name) LIKE '%CONSULTORIA%' OR
    UPPER(name) LIKE '%INSTALAÇÃO%' OR
    UPPER(name) LIKE '%INSTALACAO%' OR
    UPPER(name) LIKE '%MANUTENÇÃO%' OR
    UPPER(name) LIKE '%MANUTENCAO%'
);

SELECT CONCAT('✅ ', ROW_COUNT(), ' produtos categorizados como SERVIÇO') as resultado;

-- 2. Identificar MATÉRIA PRIMA (palavras-chave)
UPDATE products 
SET categoria_fiscal = 'materia_prima'
WHERE categoria_fiscal IS NULL
AND (
    UPPER(name) LIKE '%MATERIA%' OR
    UPPER(name) LIKE '%INSUMO%' OR
    UPPER(name) LIKE '%COMPONENTE%' OR
    UPPER(name) LIKE '%PEÇA%' OR
    UPPER(name) LIKE '%PECA%' OR
    UPPER(name) LIKE '%MATERIAL%' OR
    UPPER(name) LIKE '%CHAPA%' OR
    UPPER(name) LIKE '%BARRA%' OR
    UPPER(name) LIKE '%TUBO%' OR
    UPPER(name) LIKE '%ARAME%' OR
    UPPER(name) LIKE '%FIO%'
);

SELECT CONCAT('✅ ', ROW_COUNT(), ' produtos categorizados como MATÉRIA PRIMA') as resultado;

-- 3. Identificar CONSUMO INTERNO (palavras-chave)
UPDATE products 
SET categoria_fiscal = 'consumo_interno'
WHERE categoria_fiscal IS NULL
AND (
    UPPER(name) LIKE '%CONSUMO%' OR
    UPPER(name) LIKE '%FERRAMENTA%' OR
    UPPER(name) LIKE '%EQUIPAMENTO%' OR
    UPPER(name) LIKE '%MÁQUINA%' OR
    UPPER(name) LIKE '%MAQUINA%' OR
    UPPER(name) LIKE '%ENERGIA%' OR
    UPPER(name) LIKE '%ÁGUA%' OR
    UPPER(name) LIKE '%AGUA%' OR
    UPPER(name) LIKE '%GÁS%' OR
    UPPER(name) LIKE '%GAS%'
);

SELECT CONCAT('✅ ', ROW_COUNT(), ' produtos categorizados como CONSUMO INTERNO') as resultado;

-- 4. Produtos restantes como PRODUTO FINAL
UPDATE products 
SET categoria_fiscal = 'produto_final'
WHERE categoria_fiscal IS NULL;

SELECT CONCAT('✅ ', ROW_COUNT(), ' produtos categorizados como PRODUTO FINAL') as resultado;

-- ========================================
-- RELATÓRIO DE CATEGORIZAÇÃO
-- ========================================

SELECT '========================================' as '';
SELECT '📊 RELATÓRIO DE CATEGORIZAÇÃO' as '';
SELECT '========================================' as '';

SELECT 
    CASE categoria_fiscal
        WHEN 'servico' THEN '🔧 Serviço'
        WHEN 'materia_prima' THEN '📦 Matéria Prima'
        WHEN 'consumo_interno' THEN '🧰 Consumo Interno'
        WHEN 'produto_final' THEN '📦 Produto Final'
        ELSE '❓ Não Definida'
    END as categoria,
    COUNT(*) as total,
    CONCAT(ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM products), 2), '%') as percentual
FROM products
GROUP BY categoria_fiscal
ORDER BY 
    CASE categoria_fiscal
        WHEN 'servico' THEN 1
        WHEN 'materia_prima' THEN 2
        WHEN 'consumo_interno' THEN 3
        WHEN 'produto_final' THEN 4
        ELSE 5
    END;

-- ========================================
-- EXEMPLOS DE PRODUTOS POR CATEGORIA
-- ========================================

SELECT '========================================' as '';
SELECT '📋 EXEMPLOS DE PRODUTOS POR CATEGORIA' as '';
SELECT '========================================' as '';

-- Serviços
SELECT '🔧 SERVIÇOS:' as '';
SELECT id, name, cost_price
FROM products
WHERE categoria_fiscal = 'servico'
LIMIT 5;

SELECT '' as '';

-- Matéria Prima
SELECT '📦 MATÉRIA PRIMA:' as '';
SELECT id, name, cost_price
FROM products
WHERE categoria_fiscal = 'materia_prima'
LIMIT 5;

SELECT '' as '';

-- Consumo Interno
SELECT '🧰 CONSUMO INTERNO:' as '';
SELECT id, name, cost_price
FROM products
WHERE categoria_fiscal = 'consumo_interno'
LIMIT 5;

SELECT '' as '';

-- Produto Final
SELECT '📦 PRODUTO FINAL:' as '';
SELECT id, name, cost_price
FROM products
WHERE categoria_fiscal = 'produto_final'
LIMIT 5;

SELECT '========================================' as '';
SELECT '✅ CATEGORIZAÇÃO CONCLUÍDA!' as '';
SELECT '========================================' as '';

-- ========================================
-- OPÇÃO 2: CATEGORIZAÇÃO MANUAL
-- Descomente e ajuste conforme necessário
-- ========================================

/*
-- Exemplo: Categorizar produtos específicos por ID
UPDATE products SET categoria_fiscal = 'servico' WHERE id IN (1, 2, 3);
UPDATE products SET categoria_fiscal = 'materia_prima' WHERE id IN (4, 5, 6);
UPDATE products SET categoria_fiscal = 'consumo_interno' WHERE id IN (7, 8, 9);
UPDATE products SET categoria_fiscal = 'produto_final' WHERE id IN (10, 11, 12);
*/

/*
-- Exemplo: Categorizar por categoria de produto
UPDATE products p
INNER JOIN product_categories pc ON p.category_id = pc.id
SET p.categoria_fiscal = 'servico'
WHERE pc.name LIKE '%Serviço%';

UPDATE products p
INNER JOIN product_categories pc ON p.category_id = pc.id
SET p.categoria_fiscal = 'materia_prima'
WHERE pc.name LIKE '%Matéria Prima%';
*/

-- ========================================
-- VERIFICAÇÃO FINAL
-- ========================================

SELECT 
    CASE 
        WHEN COUNT(*) = 0 THEN '✅ TODOS OS PRODUTOS FORAM CATEGORIZADOS'
        ELSE CONCAT('⚠️ ', COUNT(*), ' produtos ainda sem categoria')
    END as status_final
FROM products
WHERE categoria_fiscal IS NULL;
