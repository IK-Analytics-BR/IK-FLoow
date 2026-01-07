-- ========================================
-- VERIFICAR TABELAS E VIEWS FALTANTES NA AWS
-- ========================================

USE supply_chain_system;

SELECT '========================================' as '';
SELECT '🔍 VERIFICAÇÃO DE TABELAS E VIEWS' as '';
SELECT '========================================' as '';

-- ========================================
-- 1. TABELAS EXISTENTES
-- ========================================

SELECT '📋 TABELAS EXISTENTES:' as '';
SELECT table_name as 'Tabela'
FROM information_schema.TABLES
WHERE table_schema = 'supply_chain_system'
AND table_type = 'BASE TABLE'
ORDER BY table_name;

SELECT '' as '';

-- ========================================
-- 2. VIEWS EXISTENTES
-- ========================================

SELECT '👁️ VIEWS EXISTENTES:' as '';
SELECT table_name as 'View'
FROM information_schema.VIEWS
WHERE table_schema = 'supply_chain_system'
ORDER BY table_name;

SELECT '' as '';

-- ========================================
-- 3. VERIFICAR TABELAS ESPECÍFICAS
-- ========================================

SELECT '🔍 VERIFICANDO TABELAS NECESSÁRIAS:' as '';

-- Ordem de Produção
SELECT 
    'ordens_producao' as tabela,
    CASE WHEN COUNT(*) > 0 THEN '✅ Existe' ELSE '❌ Não existe' END as status
FROM information_schema.TABLES
WHERE table_schema = 'supply_chain_system'
AND table_name = 'ordens_producao'

UNION ALL

SELECT 
    'ordem_producao_itens' as tabela,
    CASE WHEN COUNT(*) > 0 THEN '✅ Existe' ELSE '❌ Não existe' END as status
FROM information_schema.TABLES
WHERE table_schema = 'supply_chain_system'
AND table_name = 'ordem_producao_itens'

UNION ALL

SELECT 
    'templates_producao' as tabela,
    CASE WHEN COUNT(*) > 0 THEN '✅ Existe' ELSE '❌ Não existe' END as status
FROM information_schema.TABLES
WHERE table_schema = 'supply_chain_system'
AND table_name = 'templates_producao'

UNION ALL

SELECT 
    'template_producao_itens' as tabela,
    CASE WHEN COUNT(*) > 0 THEN '✅ Existe' ELSE '❌ Não existe' END as status
FROM information_schema.TABLES
WHERE table_schema = 'supply_chain_system'
AND table_name = 'template_producao_itens'

UNION ALL

-- Jornada de Trabalho
SELECT 
    'jornadas_trabalho' as tabela,
    CASE WHEN COUNT(*) > 0 THEN '✅ Existe' ELSE '❌ Não existe' END as status
FROM information_schema.TABLES
WHERE table_schema = 'supply_chain_system'
AND table_name = 'jornadas_trabalho';

SELECT '' as '';

-- ========================================
-- 4. VERIFICAR VIEWS ESPECÍFICAS
-- ========================================

SELECT '🔍 VERIFICANDO VIEWS NECESSÁRIAS:' as '';

SELECT 
    'vw_ordens_producao_resumo' as view_name,
    CASE WHEN COUNT(*) > 0 THEN '✅ Existe' ELSE '❌ Não existe' END as status
FROM information_schema.VIEWS
WHERE table_schema = 'supply_chain_system'
AND table_name = 'vw_ordens_producao_resumo'

UNION ALL

SELECT 
    'vw_ordem_producao_itens_detalhado' as view_name,
    CASE WHEN COUNT(*) > 0 THEN '✅ Existe' ELSE '❌ Não existe' END as status
FROM information_schema.VIEWS
WHERE table_schema = 'supply_chain_system'
AND table_name = 'vw_ordem_producao_itens_detalhado'

UNION ALL

SELECT 
    'vw_templates_ativos' as view_name,
    CASE WHEN COUNT(*) > 0 THEN '✅ Existe' ELSE '❌ Não existe' END as status
FROM information_schema.VIEWS
WHERE table_schema = 'supply_chain_system'
AND table_name = 'vw_templates_ativos';

SELECT '' as '';

-- ========================================
-- 5. RESUMO
-- ========================================

SELECT '========================================' as '';
SELECT '📊 RESUMO' as '';
SELECT '========================================' as '';

SELECT 
    CONCAT('Total de tabelas: ', COUNT(*)) as info
FROM information_schema.TABLES
WHERE table_schema = 'supply_chain_system'
AND table_type = 'BASE TABLE';

SELECT 
    CONCAT('Total de views: ', COUNT(*)) as info
FROM information_schema.VIEWS
WHERE table_schema = 'supply_chain_system';

SELECT '========================================' as '';
