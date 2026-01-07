-- =====================================================
-- SCRIPT 044: CRIAR TEMPLATES PARA TODOS OS PRODUTOS
-- =====================================================
-- Cria ficha técnica (template) para cada produto da categoria 6 (Produto Produzido)
-- Baseado no tipo do produto (CS, PV, CP, CT, HTD)
-- =====================================================

-- Buscar os templates base existentes
SET @template_cs_base = (SELECT id FROM produto_templates_producao WHERE nome_template LIKE '%Correia Sincronizada (CS)%' LIMIT 1);
SET @template_pv_base = (SELECT id FROM produto_templates_producao WHERE nome_template LIKE '%Poly-V (PV)%' LIMIT 1);
SET @template_cp_base = (SELECT id FROM produto_templates_producao WHERE nome_template LIKE '%Correia Plana (CP)%' LIMIT 1);
SET @template_ct_base = (SELECT id FROM produto_templates_producao WHERE nome_template LIKE '%Correia Transportadora (CT)%' LIMIT 1);
SET @template_htd_base = (SELECT id FROM produto_templates_producao WHERE nome_template LIKE '%HTD%' LIMIT 1);
SET @template_outros_base = (SELECT id FROM produto_templates_producao WHERE nome_template LIKE '%Correias Diversas%' LIMIT 1);

SELECT @template_cs_base, @template_pv_base, @template_cp_base, @template_ct_base, @template_htd_base, @template_outros_base;

-- =====================================================
-- CRIAR TEMPLATES PARA PRODUTOS CS SEM TEMPLATE
-- =====================================================
INSERT INTO produto_templates_producao (produto_id, versao, nome_template, custo_total_base, tempo_producao_horas, ativo, observacoes)
SELECT 
    p.id,
    1,
    CONCAT('Ficha Técnica - ', p.name),
    450.00,
    8.0,
    1,
    'Template automático baseado no tipo CS (Correia Sincronizada)'
FROM products p
WHERE p.category_id = 6 
  AND p.name LIKE 'CS %'
  AND NOT EXISTS (SELECT 1 FROM produto_templates_producao t WHERE t.produto_id = p.id);

SELECT CONCAT('Templates CS criados: ', ROW_COUNT()) AS resultado_cs;

-- =====================================================
-- CRIAR TEMPLATES PARA PRODUTOS PV SEM TEMPLATE
-- =====================================================
INSERT INTO produto_templates_producao (produto_id, versao, nome_template, custo_total_base, tempo_producao_horas, ativo, observacoes)
SELECT 
    p.id,
    1,
    CONCAT('Ficha Técnica - ', p.name),
    320.00,
    6.0,
    1,
    'Template automático baseado no tipo PV (Poly-V)'
FROM products p
WHERE p.category_id = 6 
  AND p.name LIKE 'PV %'
  AND NOT EXISTS (SELECT 1 FROM produto_templates_producao t WHERE t.produto_id = p.id);

SELECT CONCAT('Templates PV criados: ', ROW_COUNT()) AS resultado_pv;

-- =====================================================
-- CRIAR TEMPLATES PARA PRODUTOS CP SEM TEMPLATE
-- =====================================================
INSERT INTO produto_templates_producao (produto_id, versao, nome_template, custo_total_base, tempo_producao_horas, ativo, observacoes)
SELECT 
    p.id,
    1,
    CONCAT('Ficha Técnica - ', p.name),
    380.00,
    7.0,
    1,
    'Template automático baseado no tipo CP (Correia Plana)'
FROM products p
WHERE p.category_id = 6 
  AND (p.name LIKE 'CP %' OR p.name LIKE 'CORREIA PLANA%')
  AND NOT EXISTS (SELECT 1 FROM produto_templates_producao t WHERE t.produto_id = p.id);

SELECT CONCAT('Templates CP criados: ', ROW_COUNT()) AS resultado_cp;

-- =====================================================
-- CRIAR TEMPLATES PARA PRODUTOS CT SEM TEMPLATE
-- =====================================================
INSERT INTO produto_templates_producao (produto_id, versao, nome_template, custo_total_base, tempo_producao_horas, ativo, observacoes)
SELECT 
    p.id,
    1,
    CONCAT('Ficha Técnica - ', p.name),
    850.00,
    16.0,
    1,
    'Template automático baseado no tipo CT (Correia Transportadora)'
FROM products p
WHERE p.category_id = 6 
  AND (p.name LIKE 'CT %' OR p.name LIKE 'CORREIA TRANSP%')
  AND NOT EXISTS (SELECT 1 FROM produto_templates_producao t WHERE t.produto_id = p.id);

SELECT CONCAT('Templates CT criados: ', ROW_COUNT()) AS resultado_ct;

-- =====================================================
-- CRIAR TEMPLATES PARA PRODUTOS HTD SEM TEMPLATE
-- =====================================================
INSERT INTO produto_templates_producao (produto_id, versao, nome_template, custo_total_base, tempo_producao_horas, ativo, observacoes)
SELECT 
    p.id,
    1,
    CONCAT('Ficha Técnica - ', p.name),
    520.00,
    10.0,
    1,
    'Template automático baseado no tipo HTD (High Torque Drive)'
FROM products p
WHERE p.category_id = 6 
  AND p.name LIKE '%HTD%'
  AND p.name NOT LIKE 'CS %'  -- Evitar duplicar CS que já têm template
  AND NOT EXISTS (SELECT 1 FROM produto_templates_producao t WHERE t.produto_id = p.id);

SELECT CONCAT('Templates HTD criados: ', ROW_COUNT()) AS resultado_htd;

-- =====================================================
-- CRIAR TEMPLATES PARA OUTROS PRODUTOS SEM TEMPLATE
-- =====================================================
INSERT INTO produto_templates_producao (produto_id, versao, nome_template, custo_total_base, tempo_producao_horas, ativo, observacoes)
SELECT 
    p.id,
    1,
    CONCAT('Ficha Técnica - ', p.name),
    400.00,
    8.0,
    1,
    'Template automático genérico para produto produzido'
FROM products p
WHERE p.category_id = 6 
  AND NOT EXISTS (SELECT 1 FROM produto_templates_producao t WHERE t.produto_id = p.id);

SELECT CONCAT('Templates Outros criados: ', ROW_COUNT()) AS resultado_outros;

-- =====================================================
-- COPIAR ITENS DO TEMPLATE BASE PARA OS NOVOS TEMPLATES
-- =====================================================

-- Buscar itens do template CS base
SET @template_cs_base = (SELECT MIN(id) FROM produto_templates_producao WHERE nome_template LIKE '%Correia Sincronizada (CS)%');

-- Copiar itens para templates CS
INSERT INTO produto_template_itens (template_id, tipo_item, produto_id, descricao, quantidade, unidade_medida, custo_unitario_base, custo_total_base)
SELECT 
    t.id,
    base_item.tipo_item,
    base_item.produto_id,
    base_item.descricao,
    base_item.quantidade,
    base_item.unidade_medida,
    base_item.custo_unitario_base,
    base_item.custo_total_base
FROM produto_templates_producao t
CROSS JOIN produto_template_itens base_item
WHERE base_item.template_id = @template_cs_base
  AND t.observacoes LIKE '%tipo CS%'
  AND NOT EXISTS (SELECT 1 FROM produto_template_itens pti WHERE pti.template_id = t.id);

SELECT CONCAT('Itens copiados para templates CS: ', ROW_COUNT()) AS itens_cs;

-- =====================================================
-- VERIFICAÇÃO FINAL
-- =====================================================
SELECT 
    'Templates criados' AS tipo,
    COUNT(*) AS total
FROM produto_templates_producao
UNION ALL
SELECT 
    'Produtos categoria 6 com template' AS tipo,
    COUNT(DISTINCT t.produto_id) AS total
FROM produto_templates_producao t
JOIN products p ON t.produto_id = p.id
WHERE p.category_id = 6
UNION ALL
SELECT 
    'Produtos categoria 6 SEM template' AS tipo,
    COUNT(*) AS total
FROM products p
WHERE p.category_id = 6
  AND NOT EXISTS (SELECT 1 FROM produto_templates_producao t WHERE t.produto_id = p.id);
