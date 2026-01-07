-- ========================================
-- CRIAR VIEWS PARA ORDEM DE PRODUÇÃO
-- Script para AWS
-- ========================================

USE supply_chain_system;

-- ========================================
-- 1. VIEW: vw_templates_ativos
-- ========================================

DROP VIEW IF EXISTS vw_templates_ativos;

CREATE VIEW vw_templates_ativos AS
SELECT 
    t.id,
    t.nome,
    t.produto_id,
    p.name as produto_nome,
    t.versao,
    t.custo_base,
    t.observacoes,
    t.created_at,
    COUNT(ti.id) as total_itens
FROM templates_producao t
INNER JOIN products p ON t.produto_id = p.id
LEFT JOIN template_producao_itens ti ON t.id = ti.template_id
WHERE t.ativo = 1
GROUP BY t.id, t.nome, t.produto_id, p.name, t.versao, t.custo_base, t.observacoes, t.created_at
ORDER BY t.created_at DESC;

SELECT '✅ View vw_templates_ativos criada!' as status;

-- ========================================
-- 2. VIEW: vw_ordens_producao_resumo
-- ========================================

DROP VIEW IF EXISTS vw_ordens_producao_resumo;

CREATE VIEW vw_ordens_producao_resumo AS
SELECT 
    op.id,
    op.numero_op,
    e.nome_fantasia as empresa_nome,
    c.name as cliente_nome,
    p.name as produto_nome,
    op.quantidade,
    op.status,
    op.data_solicitacao,
    op.data_prevista,
    op.data_conclusao,
    op.custo_total_atual,
    op.usou_template,
    CASE 
        WHEN op.usou_template = 1 THEN CONCAT('Template v', t.versao)
        ELSE 'Manual'
    END as template_info,
    op.variacao_custo_percentual,
    op.created_at
FROM ordens_producao op
INNER JOIN empresas e ON op.empresa_id = e.id
INNER JOIN customers c ON op.cliente_id = c.id
INNER JOIN products p ON op.produto_id = p.id
LEFT JOIN templates_producao t ON op.template_usado_id = t.id
ORDER BY op.created_at DESC;

SELECT '✅ View vw_ordens_producao_resumo criada!' as status;

-- ========================================
-- 3. VIEW: vw_ordem_producao_itens_detalhado
-- ========================================

DROP VIEW IF EXISTS vw_ordem_producao_itens_detalhado;

CREATE VIEW vw_ordem_producao_itens_detalhado AS
SELECT 
    opi.id,
    opi.ordem_producao_id,
    op.numero_op,
    opi.tipo_item,
    CASE 
        WHEN opi.tipo_item = 'servico' THEN '🔧 Serviço'
        WHEN opi.tipo_item = 'materia_prima' THEN '📦 Matéria Prima'
        WHEN opi.tipo_item = 'consumo_interno' THEN '🧰 Consumo Interno'
    END as tipo_item_label,
    opi.produto_id,
    p.name as produto_nome,
    opi.descricao,
    opi.quantidade,
    opi.unidade_medida,
    opi.custo_unitario_template,
    opi.custo_unitario_atual,
    CASE 
        WHEN opi.custo_unitario_template > 0 THEN
            ((opi.custo_unitario_atual - opi.custo_unitario_template) / opi.custo_unitario_template * 100)
        ELSE 0
    END as variacao_custo_percentual,
    opi.custo_total,
    opi.veio_template,
    opi.created_at
FROM ordem_producao_itens opi
INNER JOIN ordens_producao op ON opi.ordem_producao_id = op.id
INNER JOIN products p ON opi.produto_id = p.id
ORDER BY opi.ordem_producao_id, opi.tipo_item, p.name;

SELECT '✅ View vw_ordem_producao_itens_detalhado criada!' as status;

-- ========================================
-- VERIFICAÇÃO FINAL
-- ========================================

SELECT '========================================' as '';
SELECT '🔍 VERIFICAÇÃO DAS VIEWS CRIADAS' as '';
SELECT '========================================' as '';

-- Listar views criadas
SELECT 
    table_name as 'View',
    '✅ Criada' as 'Status'
FROM information_schema.VIEWS
WHERE table_schema = 'supply_chain_system'
AND table_name IN ('vw_templates_ativos', 'vw_ordens_producao_resumo', 'vw_ordem_producao_itens_detalhado')
ORDER BY table_name;

-- Contar views
SELECT 
    CASE 
        WHEN COUNT(*) = 3 THEN '✅ TODAS AS 3 VIEWS CRIADAS COM SUCESSO!'
        ELSE CONCAT('⚠️ Apenas ', COUNT(*), ' de 3 views criadas')
    END as 'Resultado'
FROM information_schema.VIEWS
WHERE table_schema = 'supply_chain_system'
AND table_name IN ('vw_templates_ativos', 'vw_ordens_producao_resumo', 'vw_ordem_producao_itens_detalhado');

SELECT '========================================' as '';
SELECT '✅ VIEWS CRIADAS COM SUCESSO!' as '';
SELECT 'Agora você pode acessar as Ordens de Produção!' as '';
SELECT '========================================' as '';
