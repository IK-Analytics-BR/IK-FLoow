-- =====================================================
-- SCRIPT 040: CLASSIFICAR PRODUTOS POR CATEGORIA
-- =====================================================
-- Baseado na origem do cadastro e descritivo do produto
-- Categorias:
--   1 = Produto (genérico)
--   2 = Serviço
--   3 = Matéria Prima
--   4 = Consumo Interno
--   5 = Produto Revenda
--   6 = Produto para Produção (produzido internamente)
-- =====================================================

-- VERIFICAR CATEGORIAS EXISTENTES
SELECT * FROM product_categories;

-- =====================================================
-- ETAPA 1: PRODUTOS DE NFE SAÍDA (VENDIDOS)
-- =====================================================

-- 1.1 CORREIAS SINCRONIZADAS PRODUZIDAS (CS = Correia Sincronizada)
UPDATE products 
SET category_id = 6,  -- Produto para Produção
    category = 'Produto Produzido'
WHERE category = 'Importado NFe Saida'
  AND (
    name LIKE 'CS %' OR           -- Correia Sincronizada
    name LIKE 'CS-%' OR
    name LIKE 'CORREIA SINC%' OR
    name LIKE 'CORREIA SINCR%'
  );

-- 1.2 CORREIAS POLY-V PRODUZIDAS
UPDATE products 
SET category_id = 6,
    category = 'Produto Produzido'
WHERE category = 'Importado NFe Saida'
  AND (
    name LIKE 'PV %' OR           -- Poly-V
    name LIKE 'PV-%' OR
    name LIKE 'POLY V%' OR
    name LIKE 'POLY-V%'
  );

-- 1.3 CORREIAS TRANSPORTADORAS PRODUZIDAS
UPDATE products 
SET category_id = 6,
    category = 'Produto Produzido'
WHERE category = 'Importado NFe Saida'
  AND (
    name LIKE 'CT %' OR           -- Correia Transportadora
    name LIKE 'CORREIA TRANSP%'
  );

-- 1.4 CORREIAS PLANAS PRODUZIDAS
UPDATE products 
SET category_id = 6,
    category = 'Produto Produzido'
WHERE category = 'Importado NFe Saida'
  AND (
    name LIKE 'CP %' OR           -- Correia Plana
    name LIKE 'CORREIA PLANA%'
  );

-- 1.5 CORREIAS ELEVADORAS PRODUZIDAS
UPDATE products 
SET category_id = 6,
    category = 'Produto Produzido'
WHERE category = 'Importado NFe Saida'
  AND (
    name LIKE 'CE %' OR           -- Correia Elevadora
    name LIKE 'CORREIA ELEV%'
  );

-- 1.6 CORREIAS DENTADAS PRODUZIDAS
UPDATE products 
SET category_id = 6,
    category = 'Produto Produzido'
WHERE category = 'Importado NFe Saida'
  AND (
    name LIKE 'CD %' OR           -- Correia Dentada
    name LIKE 'CORREIA DENT%' OR
    name LIKE '%HTD%' OR          -- High Torque Drive
    name LIKE '%RPP%'             -- Rubber Parabolic Profile
  );

-- 1.7 OUTRAS CORREIAS PRODUZIDAS (genérico)
UPDATE products 
SET category_id = 6,
    category = 'Produto Produzido'
WHERE category = 'Importado NFe Saida'
  AND name LIKE 'CORREIA%';

-- 1.8 FORÇA/TORQUE - CORREIAS INDUSTRIAIS
UPDATE products 
SET category_id = 6,
    category = 'Produto Produzido'
WHERE category = 'Importado NFe Saida'
  AND (
    name LIKE 'FORCE TORQUE%' OR
    name LIKE 'POWER BAND%'
  );

-- 1.9 SERVIÇOS
UPDATE products 
SET category_id = 2,  -- Serviço
    category = 'Serviço'
WHERE category = 'Importado NFe Saida'
  AND (
    name LIKE 'SERVICO%' OR
    name LIKE 'SERVIÇO%' OR
    name LIKE 'MO %' OR           -- Mão de Obra
    name LIKE 'MAO DE OBRA%' OR
    name LIKE 'MÃO DE OBRA%'
  );

-- 1.10 RESTANTE DE NFE SAÍDA = REVENDA (não produzido)
UPDATE products 
SET category_id = 5,  -- Produto Revenda
    category = 'Produto Revenda'
WHERE category = 'Importado NFe Saida';

-- =====================================================
-- ETAPA 2: PRODUTOS DE NFE ENTRADA (COMPRADOS)
-- =====================================================

-- 2.1 MATÉRIA PRIMA - BORRACHAS E ELASTÔMEROS
UPDATE products 
SET category_id = 3,  -- Matéria Prima
    category = 'Matéria Prima'
WHERE category = 'Importado NFe Entrada'
  AND (
    name LIKE '%BORRACHA%' OR
    name LIKE '%ELASTOMERO%' OR
    name LIKE '%SBR%' OR
    name LIKE '%EPDM%' OR
    name LIKE '%NITRILO%' OR
    name LIKE '%NITRILICA%' OR
    name LIKE '%NBR%' OR
    name LIKE '%NR %' OR
    name LIKE '%NEOPRENE%'
  );

-- 2.2 MATÉRIA PRIMA - LONAS E TECIDOS
UPDATE products 
SET category_id = 3,
    category = 'Matéria Prima'
WHERE category = 'Importado NFe Entrada'
  AND (
    name LIKE '%LONA%' OR
    name LIKE '%TECIDO%' OR
    name LIKE '%POLIESTER%' OR
    name LIKE '%NYLON%' OR
    name LIKE '%ARAMIDA%' OR
    name LIKE '%KEVLAR%' OR
    name LIKE '%FIBRA%'
  );

-- 2.3 MATÉRIA PRIMA - AÇOS E METAIS
UPDATE products 
SET category_id = 3,
    category = 'Matéria Prima'
WHERE category = 'Importado NFe Entrada'
  AND (
    name LIKE '%CABO DE ACO%' OR
    name LIKE '%CORDOALHA%' OR
    name LIKE '%ARAME%' OR
    name LIKE 'CHAPA ACO%'
  );

-- 2.4 MATÉRIA PRIMA - ADESIVOS E COLAS
UPDATE products 
SET category_id = 3,
    category = 'Matéria Prima'
WHERE category = 'Importado NFe Entrada'
  AND (
    name LIKE '%ADESIVO%' OR
    name LIKE '%COLA%' OR
    name LIKE '%PRIMER%' OR
    name LIKE '%VULCANIZANTE%'
  );

-- 2.5 MATÉRIA PRIMA - CORREIAS PARA PRODUÇÃO (insumo)
UPDATE products 
SET category_id = 3,
    category = 'Matéria Prima'
WHERE category = 'Importado NFe Entrada'
  AND (
    name LIKE 'CORREIA PV%' OR
    name LIKE 'CORREIA SINC%' OR
    name LIKE '%LENCOL%'
  );

-- 2.6 CONSUMO INTERNO - FERRAMENTAS
UPDATE products 
SET category_id = 4,  -- Consumo Interno
    category = 'Consumo Interno'
WHERE category = 'Importado NFe Entrada'
  AND (
    name LIKE '%ALICATE%' OR
    name LIKE '%CHAVE%' OR
    name LIKE '%MARTELO%' OR
    name LIKE '%ESTILETE%' OR
    name LIKE '%TESOURA%' OR
    name LIKE '%FURADEIRA%' OR
    name LIKE '%ESMERILHADEIRA%' OR
    name LIKE '%PARAFUSADEIRA%' OR
    name LIKE '%SOPRADOR%' OR
    name LIKE '%ESCALA%' OR
    name LIKE '%TRENA%' OR
    name LIKE '%PAQUIMETRO%' OR
    name LIKE '%CALIBRADOR%'
  );

-- 2.7 CONSUMO INTERNO - EPIs
UPDATE products 
SET category_id = 4,
    category = 'Consumo Interno'
WHERE category = 'Importado NFe Entrada'
  AND (
    name LIKE '%BOTINA%' OR
    name LIKE '%LUVA%' OR
    name LIKE '%OCULOS%' OR
    name LIKE '%CAPACETE%' OR
    name LIKE '%PROTETOR%' OR
    name LIKE '%AVENTAL%' OR
    name LIKE '%MASCARA%' OR
    name LIKE '%RESPIRADOR%'
  );

-- 2.8 CONSUMO INTERNO - MATERIAIS DE ESCRITÓRIO E LIMPEZA
UPDATE products 
SET category_id = 4,
    category = 'Consumo Interno'
WHERE category = 'Importado NFe Entrada'
  AND (
    name LIKE '%PAPEL%' OR
    name LIKE '%CANETA%' OR
    name LIKE '%ETIQUETA%' OR
    name LIKE '%RIBBON%' OR
    name LIKE '%TONER%' OR
    name LIKE '%CARTUCHO%' OR
    name LIKE '%DETERGENTE%' OR
    name LIKE '%DESENGORDURANTE%'
  );

-- 2.9 CONSUMO INTERNO - RESISTÊNCIAS E PEÇAS
UPDATE products 
SET category_id = 4,
    category = 'Consumo Interno'
WHERE category = 'Importado NFe Entrada'
  AND (
    name LIKE 'RESIST%' OR
    name LIKE '%ROLAMENTO%' OR
    name LIKE '%MANCAL%'
  );

-- 2.10 REVENDA - CORREIAS PRONTAS PARA REVENDA
UPDATE products 
SET category_id = 5,  -- Produto Revenda
    category = 'Produto Revenda'
WHERE category = 'Importado NFe Entrada'
  AND (
    name LIKE 'CORREIA POWER%' OR
    name LIKE 'CORREIA INDUSTRIAL%' OR
    name LIKE 'CORREIA REXON%' OR
    name LIKE '%UNIBELT%' OR
    name LIKE '%GATES%' OR
    name LIKE '%GOODYEAR%'
  );

-- 2.11 RESTANTE DE ENTRADA SEM CLASSIFICAÇÃO = CONSUMO INTERNO
UPDATE products 
SET category_id = 4,  -- Consumo Interno (default para entradas)
    category = 'Consumo Interno'
WHERE category = 'Importado NFe Entrada';

-- =====================================================
-- ETAPA 3: OUTROS AJUSTES
-- =====================================================

-- Corrigir categoria "outro" para produto genérico
UPDATE products 
SET category_id = 1
WHERE category = 'outro';

-- Corrigir Informática e Papelaria para Consumo Interno
UPDATE products 
SET category_id = 4,
    category = 'Consumo Interno'
WHERE category IN ('Informática', 'Papelaria');

-- Manter Serviços
UPDATE products 
SET category_id = 2
WHERE category = 'Serviços';

-- =====================================================
-- VERIFICAÇÃO FINAL
-- =====================================================
SELECT 
    pc.name as categoria_fiscal,
    p.category as categoria_texto,
    COUNT(*) as quantidade
FROM products p
LEFT JOIN product_categories pc ON p.category_id = pc.id
GROUP BY pc.name, p.category
ORDER BY quantidade DESC;
