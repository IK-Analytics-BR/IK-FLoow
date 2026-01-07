-- ========================================
-- VERIFICAÇÃO DE DEPLOY - ORDEM DE PRODUÇÃO
-- Execute este script após o deploy para verificar se tudo está OK
-- ========================================

USE supplychain;

SELECT '========================================' as '';
SELECT '🔍 VERIFICAÇÃO DE DEPLOY - ORDEM DE PRODUÇÃO' as '';
SELECT '========================================' as '';
SELECT '' as '';

-- ========================================
-- 1. VERIFICAR TABELAS
-- ========================================

SELECT '📋 1. VERIFICANDO TABELAS...' as '';
SELECT '' as '';

SELECT 
    table_name as 'Tabela',
    CASE 
        WHEN table_name IN ('templates_producao', 'template_producao_itens', 'ordens_producao', 'ordem_producao_itens') 
        THEN '✅ OK'
        ELSE '❌ ERRO'
    END as 'Status'
FROM information_schema.TABLES
WHERE table_schema = DATABASE()
AND table_name IN ('templates_producao', 'template_producao_itens', 'ordens_producao', 'ordem_producao_itens')
ORDER BY table_name;

SELECT '' as '';

-- Verificar se todas as 4 tabelas existem
SELECT 
    CASE 
        WHEN COUNT(*) = 4 THEN '✅ TODAS AS 4 TABELAS CRIADAS COM SUCESSO'
        ELSE CONCAT('❌ ERRO: Apenas ', COUNT(*), ' de 4 tabelas encontradas')
    END as 'Resultado'
FROM information_schema.TABLES
WHERE table_schema = DATABASE()
AND table_name IN ('templates_producao', 'template_producao_itens', 'ordens_producao', 'ordem_producao_itens');

SELECT '' as '';
SELECT '========================================' as '';
SELECT '' as '';

-- ========================================
-- 2. VERIFICAR VIEWS
-- ========================================

SELECT '👁️ 2. VERIFICANDO VIEWS...' as '';
SELECT '' as '';

SELECT 
    table_name as 'View',
    CASE 
        WHEN table_name IN ('vw_templates_ativos', 'vw_ordens_producao_resumo', 'vw_ordem_producao_itens_detalhado') 
        THEN '✅ OK'
        ELSE '❌ ERRO'
    END as 'Status'
FROM information_schema.VIEWS
WHERE table_schema = DATABASE()
AND table_name IN ('vw_templates_ativos', 'vw_ordens_producao_resumo', 'vw_ordem_producao_itens_detalhado')
ORDER BY table_name;

SELECT '' as '';

-- Verificar se todas as 3 views existem
SELECT 
    CASE 
        WHEN COUNT(*) = 3 THEN '✅ TODAS AS 3 VIEWS CRIADAS COM SUCESSO'
        ELSE CONCAT('❌ ERRO: Apenas ', COUNT(*), ' de 3 views encontradas')
    END as 'Resultado'
FROM information_schema.VIEWS
WHERE table_schema = DATABASE()
AND table_name IN ('vw_templates_ativos', 'vw_ordens_producao_resumo', 'vw_ordem_producao_itens_detalhado');

SELECT '' as '';
SELECT '========================================' as '';
SELECT '' as '';

-- ========================================
-- 3. VERIFICAR TRIGGERS
-- ========================================

SELECT '⚡ 3. VERIFICANDO TRIGGERS...' as '';
SELECT '' as '';

SELECT 
    trigger_name as 'Trigger',
    event_manipulation as 'Evento',
    event_object_table as 'Tabela',
    CASE 
        WHEN trigger_name = 'gerar_numero_op' THEN '✅ OK'
        ELSE '❌ ERRO'
    END as 'Status'
FROM information_schema.TRIGGERS
WHERE trigger_schema = DATABASE()
AND trigger_name = 'gerar_numero_op';

SELECT '' as '';

-- Verificar se o trigger existe
SELECT 
    CASE 
        WHEN COUNT(*) = 1 THEN '✅ TRIGGER CRIADO COM SUCESSO'
        ELSE '❌ ERRO: Trigger não encontrado'
    END as 'Resultado'
FROM information_schema.TRIGGERS
WHERE trigger_schema = DATABASE()
AND trigger_name = 'gerar_numero_op';

SELECT '' as '';
SELECT '========================================' as '';
SELECT '' as '';

-- ========================================
-- 4. VERIFICAR COLUNA CATEGORIA_FISCAL
-- ========================================

SELECT '🏷️ 4. VERIFICANDO COLUNA CATEGORIA_FISCAL...' as '';
SELECT '' as '';

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

SELECT '' as '';

-- Verificar se a coluna existe
SELECT 
    CASE 
        WHEN COUNT(*) = 1 THEN '✅ COLUNA CATEGORIA_FISCAL CRIADA COM SUCESSO'
        ELSE '❌ ERRO: Coluna não encontrada'
    END as 'Resultado'
FROM information_schema.COLUMNS
WHERE table_schema = DATABASE()
AND table_name = 'products'
AND column_name = 'categoria_fiscal';

SELECT '' as '';
SELECT '========================================' as '';
SELECT '' as '';

-- ========================================
-- 5. VERIFICAR FOREIGN KEYS
-- ========================================

SELECT '🔗 5. VERIFICANDO FOREIGN KEYS...' as '';
SELECT '' as '';

SELECT 
    constraint_name as 'Foreign Key',
    table_name as 'Tabela',
    referenced_table_name as 'Referencia',
    '✅ OK' as 'Status'
FROM information_schema.KEY_COLUMN_USAGE
WHERE table_schema = DATABASE()
AND table_name IN ('templates_producao', 'template_producao_itens', 'ordens_producao', 'ordem_producao_itens')
AND referenced_table_name IS NOT NULL
ORDER BY table_name, constraint_name;

SELECT '' as '';

-- Contar foreign keys
SELECT 
    CONCAT('✅ Total de Foreign Keys: ', COUNT(*)) as 'Resultado'
FROM information_schema.KEY_COLUMN_USAGE
WHERE table_schema = DATABASE()
AND table_name IN ('templates_producao', 'template_producao_itens', 'ordens_producao', 'ordem_producao_itens')
AND referenced_table_name IS NOT NULL;

SELECT '' as '';
SELECT '========================================' as '';
SELECT '' as '';

-- ========================================
-- 6. VERIFICAR ÍNDICES
-- ========================================

SELECT '📊 6. VERIFICANDO ÍNDICES...' as '';
SELECT '' as '';

SELECT 
    table_name as 'Tabela',
    index_name as 'Índice',
    column_name as 'Coluna',
    '✅ OK' as 'Status'
FROM information_schema.STATISTICS
WHERE table_schema = DATABASE()
AND table_name IN ('templates_producao', 'template_producao_itens', 'ordens_producao', 'ordem_producao_itens', 'products')
AND index_name NOT IN ('PRIMARY')
ORDER BY table_name, index_name;

SELECT '' as '';

-- Contar índices
SELECT 
    CONCAT('✅ Total de Índices: ', COUNT(*)) as 'Resultado'
FROM information_schema.STATISTICS
WHERE table_schema = DATABASE()
AND table_name IN ('templates_producao', 'template_producao_itens', 'ordens_producao', 'ordem_producao_itens')
AND index_name NOT IN ('PRIMARY');

SELECT '' as '';
SELECT '========================================' as '';
SELECT '' as '';

-- ========================================
-- 7. TESTE DE INSERÇÃO
-- ========================================

SELECT '🧪 7. TESTE DE INSERÇÃO (SIMULADO)...' as '';
SELECT '' as '';

-- Verificar se existem empresas
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN CONCAT('✅ ', COUNT(*), ' empresa(s) disponível(is)')
        ELSE '❌ ERRO: Nenhuma empresa cadastrada'
    END as 'Empresas'
FROM empresas WHERE ativo = TRUE;

-- Verificar se existem clientes
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN CONCAT('✅ ', COUNT(*), ' cliente(s) disponível(is)')
        ELSE '❌ ERRO: Nenhum cliente cadastrado'
    END as 'Clientes'
FROM customers WHERE active = TRUE;

-- Verificar se existem produtos
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN CONCAT('✅ ', COUNT(*), ' produto(s) disponível(is)')
        ELSE '❌ ERRO: Nenhum produto cadastrado'
    END as 'Produtos'
FROM products WHERE active = TRUE;

SELECT '' as '';
SELECT '========================================' as '';
SELECT '' as '';

-- ========================================
-- 8. RESUMO FINAL
-- ========================================

SELECT '📊 8. RESUMO FINAL DO DEPLOY' as '';
SELECT '' as '';

SELECT 
    'Tabelas' as 'Item',
    CONCAT(
        (SELECT COUNT(*) FROM information_schema.TABLES 
         WHERE table_schema = DATABASE() 
         AND table_name IN ('templates_producao', 'template_producao_itens', 'ordens_producao', 'ordem_producao_itens')),
        ' / 4'
    ) as 'Status',
    CASE 
        WHEN (SELECT COUNT(*) FROM information_schema.TABLES 
              WHERE table_schema = DATABASE() 
              AND table_name IN ('templates_producao', 'template_producao_itens', 'ordens_producao', 'ordem_producao_itens')) = 4 
        THEN '✅'
        ELSE '❌'
    END as 'OK'
UNION ALL
SELECT 
    'Views' as 'Item',
    CONCAT(
        (SELECT COUNT(*) FROM information_schema.VIEWS 
         WHERE table_schema = DATABASE() 
         AND table_name IN ('vw_templates_ativos', 'vw_ordens_producao_resumo', 'vw_ordem_producao_itens_detalhado')),
        ' / 3'
    ) as 'Status',
    CASE 
        WHEN (SELECT COUNT(*) FROM information_schema.VIEWS 
              WHERE table_schema = DATABASE() 
              AND table_name IN ('vw_templates_ativos', 'vw_ordens_producao_resumo', 'vw_ordem_producao_itens_detalhado')) = 3 
        THEN '✅'
        ELSE '❌'
    END as 'OK'
UNION ALL
SELECT 
    'Triggers' as 'Item',
    CONCAT(
        (SELECT COUNT(*) FROM information_schema.TRIGGERS 
         WHERE trigger_schema = DATABASE() 
         AND trigger_name = 'gerar_numero_op'),
        ' / 1'
    ) as 'Status',
    CASE 
        WHEN (SELECT COUNT(*) FROM information_schema.TRIGGERS 
              WHERE trigger_schema = DATABASE() 
              AND trigger_name = 'gerar_numero_op') = 1 
        THEN '✅'
        ELSE '❌'
    END as 'OK'
UNION ALL
SELECT 
    'Coluna categoria_fiscal' as 'Item',
    CASE 
        WHEN (SELECT COUNT(*) FROM information_schema.COLUMNS 
              WHERE table_schema = DATABASE() 
              AND table_name = 'products' 
              AND column_name = 'categoria_fiscal') = 1 
        THEN 'Existe'
        ELSE 'Não existe'
    END as 'Status',
    CASE 
        WHEN (SELECT COUNT(*) FROM information_schema.COLUMNS 
              WHERE table_schema = DATABASE() 
              AND table_name = 'products' 
              AND column_name = 'categoria_fiscal') = 1 
        THEN '✅'
        ELSE '❌'
    END as 'OK';

SELECT '' as '';
SELECT '========================================' as '';
SELECT '' as '';

-- Resultado final
SELECT 
    CASE 
        WHEN 
            (SELECT COUNT(*) FROM information_schema.TABLES 
             WHERE table_schema = DATABASE() 
             AND table_name IN ('templates_producao', 'template_producao_itens', 'ordens_producao', 'ordem_producao_itens')) = 4
        AND
            (SELECT COUNT(*) FROM information_schema.VIEWS 
             WHERE table_schema = DATABASE() 
             AND table_name IN ('vw_templates_ativos', 'vw_ordens_producao_resumo', 'vw_ordem_producao_itens_detalhado')) = 3
        AND
            (SELECT COUNT(*) FROM information_schema.TRIGGERS 
             WHERE trigger_schema = DATABASE() 
             AND trigger_name = 'gerar_numero_op') = 1
        AND
            (SELECT COUNT(*) FROM information_schema.COLUMNS 
             WHERE table_schema = DATABASE() 
             AND table_name = 'products' 
             AND column_name = 'categoria_fiscal') = 1
        THEN '🎉 DEPLOY CONCLUÍDO COM SUCESSO! TODOS OS COMPONENTES ESTÃO OK!'
        ELSE '⚠️ ATENÇÃO: Alguns componentes não foram criados corretamente. Verifique os detalhes acima.'
    END as 'RESULTADO FINAL';

SELECT '' as '';
SELECT '========================================' as '';
SELECT 'Próximo passo: Enviar arquivos Python, JavaScript e HTML' as '';
SELECT '========================================' as '';
