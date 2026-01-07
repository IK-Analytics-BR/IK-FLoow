-- =====================================================
-- SCRIPT 041: CRIAR TEMPLATES DE PRODUÇÃO (FICHAS TÉCNICAS)
-- =====================================================
-- Cria templates padrão para cada tipo de correia
-- Tipos identificados:
--   CS - Correia Sincronizada (14.313 produtos)
--   PV - Poly-V (1.585 produtos)
--   CP - Correia Plana (512 produtos)
--   CT - Correia Transportadora (13 produtos)
--   HTD - High Torque Drive (17 produtos)
--   OUTROS (1.106 produtos)
-- =====================================================

-- Limpar templates existentes (para reset)
SET FOREIGN_KEY_CHECKS = 0;
DELETE FROM produto_template_itens WHERE template_id > 0;
DELETE FROM produto_templates_producao WHERE id > 0;
SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================
-- ETAPA 1: CRIAR TEMPLATES PADRÃO POR TIPO
-- =====================================================

-- Pegar um produto de cada tipo para criar o template base
SET @produto_cs = (SELECT MIN(id) FROM products WHERE category_id = 6 AND name LIKE 'CS %');
SET @produto_pv = (SELECT MIN(id) FROM products WHERE category_id = 6 AND name LIKE 'PV %');
SET @produto_cp = (SELECT MIN(id) FROM products WHERE category_id = 6 AND (name LIKE 'CP %' OR name LIKE 'CORREIA PLANA%'));
SET @produto_ct = (SELECT MIN(id) FROM products WHERE category_id = 6 AND (name LIKE 'CT %' OR name LIKE 'CORREIA TRANSP%'));
SET @produto_htd = (SELECT MIN(id) FROM products WHERE category_id = 6 AND name LIKE '%HTD%');
SET @produto_outros = (SELECT MIN(id) FROM products WHERE category_id = 6 AND name NOT LIKE 'CS %' AND name NOT LIKE 'PV %' AND name NOT LIKE 'CP %' AND name NOT LIKE 'CT %' AND name NOT LIKE 'CORREIA PLANA%' AND name NOT LIKE 'CORREIA TRANSP%' AND name NOT LIKE '%HTD%');

-- Template 1: Correia Sincronizada (CS)
INSERT INTO produto_templates_producao (produto_id, versao, nome_template, custo_total_base, tempo_producao_horas, ativo, observacoes)
VALUES (@produto_cs, 1, 'Template Padrão - Correia Sincronizada (CS)', 450.00, 8.0, 1, 
'Template padrão para correias sincronizadas. Inclui etapas de corte, montagem, vulcanização e acabamento.');

SET @template_cs = LAST_INSERT_ID();

-- Template 2: Poly-V (PV)
INSERT INTO produto_templates_producao (produto_id, versao, nome_template, custo_total_base, tempo_producao_horas, ativo, observacoes)
VALUES (@produto_pv, 1, 'Template Padrão - Poly-V (PV)', 320.00, 6.0, 1, 
'Template padrão para correias Poly-V. Processo mais simples que sincronizadas.');

SET @template_pv = LAST_INSERT_ID();

-- Template 3: Correia Plana (CP)
INSERT INTO produto_templates_producao (produto_id, versao, nome_template, custo_total_base, tempo_producao_horas, ativo, observacoes)
VALUES (@produto_cp, 1, 'Template Padrão - Correia Plana (CP)', 380.00, 7.0, 1, 
'Template padrão para correias planas. Inclui etapas de laminação e vulcanização.');

SET @template_cp = LAST_INSERT_ID();

-- Template 4: Correia Transportadora (CT)
INSERT INTO produto_templates_producao (produto_id, versao, nome_template, custo_total_base, tempo_producao_horas, ativo, observacoes)
VALUES (@produto_ct, 1, 'Template Padrão - Correia Transportadora (CT)', 850.00, 16.0, 1, 
'Template padrão para correias transportadoras. Processo mais complexo com múltiplas lonas.');

SET @template_ct = LAST_INSERT_ID();

-- Template 5: HTD - High Torque Drive
INSERT INTO produto_templates_producao (produto_id, versao, nome_template, custo_total_base, tempo_producao_horas, ativo, observacoes)
VALUES (@produto_htd, 1, 'Template Padrão - HTD (High Torque Drive)', 520.00, 10.0, 1, 
'Template padrão para correias HTD de alto torque.');

SET @template_htd = LAST_INSERT_ID();

-- Template 6: Outros tipos
INSERT INTO produto_templates_producao (produto_id, versao, nome_template, custo_total_base, tempo_producao_horas, ativo, observacoes)
VALUES (@produto_outros, 1, 'Template Padrão - Correias Diversas', 400.00, 8.0, 1, 
'Template genérico para outros tipos de correias não classificadas.');

SET @template_outros = LAST_INSERT_ID();

-- =====================================================
-- ETAPA 2: BUSCAR IDs DE INSUMOS PARA OS TEMPLATES
-- =====================================================

-- Buscar IDs de matérias-primas típicas
SET @mp_borracha = (SELECT id FROM products WHERE category_id = 3 AND name LIKE '%BORRACHA%' LIMIT 1);
SET @mp_lona = (SELECT id FROM products WHERE category_id = 3 AND name LIKE '%LONA%' LIMIT 1);
SET @mp_adesivo = (SELECT id FROM products WHERE category_id = 3 AND name LIKE '%ADESIVO%' LIMIT 1);
SET @mp_fibra = (SELECT id FROM products WHERE category_id = 3 AND name LIKE '%FIBRA%' LIMIT 1);

-- Se não encontrar, usar o primeiro disponível
SET @mp_borracha = COALESCE(@mp_borracha, (SELECT MIN(id) FROM products WHERE category_id = 3));
SET @mp_lona = COALESCE(@mp_lona, (SELECT MIN(id) FROM products WHERE category_id = 3 AND id != @mp_borracha));
SET @mp_adesivo = COALESCE(@mp_adesivo, (SELECT MIN(id) FROM products WHERE category_id = 3 AND id NOT IN (@mp_borracha, @mp_lona)));
SET @mp_fibra = COALESCE(@mp_fibra, (SELECT MIN(id) FROM products WHERE category_id = 3 AND id NOT IN (@mp_borracha, @mp_lona, @mp_adesivo)));

-- Buscar IDs de serviços
SET @srv_mo = (SELECT id FROM products WHERE category_id = 2 LIMIT 1);
SET @srv_mo = COALESCE(@srv_mo, 1);

-- =====================================================
-- ETAPA 3: INSERIR ITENS DOS TEMPLATES (BOM)
-- =====================================================

-- Template CS - Correia Sincronizada
INSERT INTO produto_template_itens (template_id, tipo_item, produto_id, descricao, quantidade, unidade_medida, custo_unitario_base, custo_total_base) VALUES
(@template_cs, 'materia_prima', @mp_borracha, 'Borracha base para correia', 2.5, 'KG', 45.00, 112.50),
(@template_cs, 'materia_prima', @mp_lona, 'Lona de reforço estrutural', 1.5, 'M2', 85.00, 127.50),
(@template_cs, 'materia_prima', @mp_adesivo, 'Adesivo para laminação', 0.3, 'KG', 120.00, 36.00),
(@template_cs, 'materia_prima', @mp_fibra, 'Fibra de vidro/kevlar', 0.5, 'M', 80.00, 40.00),
(@template_cs, 'servico', @srv_mo, 'Mão de obra produção', 8.0, 'HR', 35.00, 280.00);

-- Template PV - Poly-V
INSERT INTO produto_template_itens (template_id, tipo_item, produto_id, descricao, quantidade, unidade_medida, custo_unitario_base, custo_total_base) VALUES
(@template_pv, 'materia_prima', @mp_borracha, 'Borracha base para correia', 1.8, 'KG', 45.00, 81.00),
(@template_pv, 'materia_prima', @mp_lona, 'Lona de reforço estrutural', 1.0, 'M2', 85.00, 85.00),
(@template_pv, 'materia_prima', @mp_adesivo, 'Adesivo para laminação', 0.2, 'KG', 120.00, 24.00),
(@template_pv, 'servico', @srv_mo, 'Mão de obra produção', 6.0, 'HR', 35.00, 210.00);

-- Template CP - Correia Plana
INSERT INTO produto_template_itens (template_id, tipo_item, produto_id, descricao, quantidade, unidade_medida, custo_unitario_base, custo_total_base) VALUES
(@template_cp, 'materia_prima', @mp_borracha, 'Borracha base para correia', 3.0, 'KG', 45.00, 135.00),
(@template_cp, 'materia_prima', @mp_lona, 'Lona de reforço estrutural', 2.0, 'M2', 85.00, 170.00),
(@template_cp, 'materia_prima', @mp_adesivo, 'Adesivo para laminação', 0.25, 'KG', 120.00, 30.00),
(@template_cp, 'servico', @srv_mo, 'Mão de obra produção', 7.0, 'HR', 35.00, 245.00);

-- Template CT - Correia Transportadora
INSERT INTO produto_template_itens (template_id, tipo_item, produto_id, descricao, quantidade, unidade_medida, custo_unitario_base, custo_total_base) VALUES
(@template_ct, 'materia_prima', @mp_borracha, 'Borracha base para correia', 8.0, 'KG', 45.00, 360.00),
(@template_ct, 'materia_prima', @mp_lona, 'Lona de reforço estrutural (3 camadas)', 4.0, 'M2', 85.00, 340.00),
(@template_ct, 'materia_prima', @mp_adesivo, 'Adesivo para laminação', 0.5, 'KG', 120.00, 60.00),
(@template_ct, 'materia_prima', @mp_fibra, 'Reforço estrutural adicional', 1.0, 'M', 80.00, 80.00),
(@template_ct, 'servico', @srv_mo, 'Mão de obra produção', 16.0, 'HR', 35.00, 560.00);

-- Template HTD - High Torque
INSERT INTO produto_template_itens (template_id, tipo_item, produto_id, descricao, quantidade, unidade_medida, custo_unitario_base, custo_total_base) VALUES
(@template_htd, 'materia_prima', @mp_borracha, 'Borracha especial alta resistência', 3.5, 'KG', 55.00, 192.50),
(@template_htd, 'materia_prima', @mp_lona, 'Lona de reforço estrutural', 2.0, 'M2', 85.00, 170.00),
(@template_htd, 'materia_prima', @mp_fibra, 'Fibra de vidro/kevlar', 0.8, 'M', 80.00, 64.00),
(@template_htd, 'servico', @srv_mo, 'Mão de obra produção', 10.0, 'HR', 35.00, 350.00);

-- Template Outros
INSERT INTO produto_template_itens (template_id, tipo_item, produto_id, descricao, quantidade, unidade_medida, custo_unitario_base, custo_total_base) VALUES
(@template_outros, 'materia_prima', @mp_borracha, 'Borracha base para correia', 2.0, 'KG', 45.00, 90.00),
(@template_outros, 'materia_prima', @mp_lona, 'Lona de reforço estrutural', 1.5, 'M2', 85.00, 127.50),
(@template_outros, 'materia_prima', @mp_adesivo, 'Adesivo para laminação', 0.2, 'KG', 120.00, 24.00),
(@template_outros, 'servico', @srv_mo, 'Mão de obra produção', 8.0, 'HR', 35.00, 280.00);

-- =====================================================
-- ETAPA 4: CRIAR TEMPLATES PARA TODOS OS PRODUTOS
-- =====================================================

-- Criar templates para produtos CS (Correia Sincronizada)
INSERT INTO produto_templates_producao (produto_id, versao, nome_template, custo_total_base, tempo_producao_horas, ativo, observacoes)
SELECT 
    p.id,
    1,
    CONCAT('Ficha Técnica - ', LEFT(p.name, 100)),
    450.00,
    8.0,
    1,
    'Template automático baseado em Correia Sincronizada'
FROM products p
WHERE p.category_id = 6 
  AND p.name LIKE 'CS %'
  AND NOT EXISTS (SELECT 1 FROM produto_templates_producao t WHERE t.produto_id = p.id);

-- Criar templates para produtos PV (Poly-V)
INSERT INTO produto_templates_producao (produto_id, versao, nome_template, custo_total_base, tempo_producao_horas, ativo, observacoes)
SELECT 
    p.id,
    1,
    CONCAT('Ficha Técnica - ', LEFT(p.name, 100)),
    320.00,
    6.0,
    1,
    'Template automático baseado em Poly-V'
FROM products p
WHERE p.category_id = 6 
  AND p.name LIKE 'PV %'
  AND NOT EXISTS (SELECT 1 FROM produto_templates_producao t WHERE t.produto_id = p.id);

-- Criar templates para produtos CP (Correia Plana)
INSERT INTO produto_templates_producao (produto_id, versao, nome_template, custo_total_base, tempo_producao_horas, ativo, observacoes)
SELECT 
    p.id,
    1,
    CONCAT('Ficha Técnica - ', LEFT(p.name, 100)),
    380.00,
    7.0,
    1,
    'Template automático baseado em Correia Plana'
FROM products p
WHERE p.category_id = 6 
  AND (p.name LIKE 'CP %' OR p.name LIKE 'CORREIA PLANA%')
  AND NOT EXISTS (SELECT 1 FROM produto_templates_producao t WHERE t.produto_id = p.id);

-- Criar templates para produtos CT (Correia Transportadora)
INSERT INTO produto_templates_producao (produto_id, versao, nome_template, custo_total_base, tempo_producao_horas, ativo, observacoes)
SELECT 
    p.id,
    1,
    CONCAT('Ficha Técnica - ', LEFT(p.name, 100)),
    850.00,
    16.0,
    1,
    'Template automático baseado em Correia Transportadora'
FROM products p
WHERE p.category_id = 6 
  AND (p.name LIKE 'CT %' OR p.name LIKE 'CORREIA TRANSP%')
  AND NOT EXISTS (SELECT 1 FROM produto_templates_producao t WHERE t.produto_id = p.id);

-- Criar templates para produtos HTD
INSERT INTO produto_templates_producao (produto_id, versao, nome_template, custo_total_base, tempo_producao_horas, ativo, observacoes)
SELECT 
    p.id,
    1,
    CONCAT('Ficha Técnica - ', LEFT(p.name, 100)),
    520.00,
    10.0,
    1,
    'Template automático baseado em HTD'
FROM products p
WHERE p.category_id = 6 
  AND p.name LIKE '%HTD%'
  AND NOT EXISTS (SELECT 1 FROM produto_templates_producao t WHERE t.produto_id = p.id);

-- Criar templates para outros produtos produzidos
INSERT INTO produto_templates_producao (produto_id, versao, nome_template, custo_total_base, tempo_producao_horas, ativo, observacoes)
SELECT 
    p.id,
    1,
    CONCAT('Ficha Técnica - ', LEFT(p.name, 100)),
    400.00,
    8.0,
    1,
    'Template automático genérico'
FROM products p
WHERE p.category_id = 6 
  AND NOT EXISTS (SELECT 1 FROM produto_templates_producao t WHERE t.produto_id = p.id);

-- =====================================================
-- VERIFICAÇÃO FINAL
-- =====================================================
SELECT 'TEMPLATES CRIADOS' as info;
SELECT COUNT(*) as total_templates FROM produto_templates_producao;

SELECT 
    CASE 
        WHEN observacoes LIKE '%Sincronizada%' THEN 'CS - Sincronizada'
        WHEN observacoes LIKE '%Poly-V%' THEN 'PV - Poly-V'
        WHEN observacoes LIKE '%Plana%' THEN 'CP - Plana'
        WHEN observacoes LIKE '%Transportadora%' THEN 'CT - Transportadora'
        WHEN observacoes LIKE '%HTD%' THEN 'HTD'
        ELSE 'OUTROS'
    END as tipo_template,
    COUNT(*) as quantidade
FROM produto_templates_producao
GROUP BY 1
ORDER BY quantidade DESC;
