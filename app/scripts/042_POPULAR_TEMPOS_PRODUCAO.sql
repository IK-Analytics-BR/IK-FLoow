-- =====================================================
-- SCRIPT 042: POPULAR TEMPOS DE PRODUÇÃO POR ETAPA
-- =====================================================
-- Popula a tabela produtos_tempo_etapa com tempos estimados
-- para cada produto produzido em cada etapa de produção
-- 
-- Etapas (15 total):
--   8  - Engenharia/Especificação (15 min)
--   9  - PCP (10 min)
--   10 - Separação MP (20 min)
--   11 - Preparação Borracha (45 min)
--   12 - Preparação Lonas (30 min)
--   13 - Montagem (60 min)
--   14 - Pré-Compactação (30 min)
--   15 - Corte (25 min)
--   16 - Vulcanização (90 min)
--   17 - Resfriamento (30 min)
--   18 - Acabamento (40 min)
--   19 - Emenda (45 min)
--   20 - Inspeção QC (20 min)
--   21 - Embalagem (15 min)
--   22 - Expedição (10 min)
-- =====================================================

-- Limpar tempos existentes
DELETE FROM produtos_tempo_etapa WHERE produto_id > 0;

-- =====================================================
-- TEMPOS PARA CORREIAS SINCRONIZADAS (CS)
-- Total estimado: ~8 horas (480 min)
-- =====================================================
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT 
    p.id,
    8,  -- Engenharia
    15,
    'Tempo padrão CS - Engenharia'
FROM products p
WHERE p.category_id = 6 AND p.name LIKE 'CS %';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 9, 10, 'Tempo padrão CS - PCP' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'CS %';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 10, 20, 'Tempo padrão CS - Separação MP' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'CS %';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 11, 40, 'Tempo padrão CS - Prep Borracha' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'CS %';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 12, 25, 'Tempo padrão CS - Prep Lonas' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'CS %';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 13, 50, 'Tempo padrão CS - Montagem' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'CS %';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 14, 25, 'Tempo padrão CS - Pré-Compactação' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'CS %';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 15, 20, 'Tempo padrão CS - Corte' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'CS %';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 16, 80, 'Tempo padrão CS - Vulcanização' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'CS %';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 17, 25, 'Tempo padrão CS - Resfriamento' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'CS %';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 18, 35, 'Tempo padrão CS - Acabamento' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'CS %';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 19, 40, 'Tempo padrão CS - Emenda' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'CS %';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 20, 15, 'Tempo padrão CS - Inspeção' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'CS %';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 21, 10, 'Tempo padrão CS - Embalagem' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'CS %';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 22, 10, 'Tempo padrão CS - Expedição' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'CS %';

-- =====================================================
-- TEMPOS PARA POLY-V (PV)
-- Total estimado: ~6 horas (360 min) - mais simples
-- =====================================================
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 8, 10, 'Tempo padrão PV' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'PV %';
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 9, 8, 'Tempo padrão PV' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'PV %';
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 10, 15, 'Tempo padrão PV' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'PV %';
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 11, 30, 'Tempo padrão PV' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'PV %';
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 12, 20, 'Tempo padrão PV' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'PV %';
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 13, 40, 'Tempo padrão PV' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'PV %';
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 14, 20, 'Tempo padrão PV' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'PV %';
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 15, 15, 'Tempo padrão PV' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'PV %';
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 16, 60, 'Tempo padrão PV' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'PV %';
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 17, 20, 'Tempo padrão PV' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'PV %';
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 18, 25, 'Tempo padrão PV' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'PV %';
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 19, 30, 'Tempo padrão PV' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'PV %';
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 20, 12, 'Tempo padrão PV' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'PV %';
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 21, 8, 'Tempo padrão PV' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'PV %';
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 22, 7, 'Tempo padrão PV' FROM products p WHERE p.category_id = 6 AND p.name LIKE 'PV %';

-- =====================================================
-- TEMPOS PARA CORREIA TRANSPORTADORA (CT)
-- Total estimado: ~16 horas (960 min) - mais complexa
-- =====================================================
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 8, 30, 'Tempo padrão CT' FROM products p WHERE p.category_id = 6 AND (p.name LIKE 'CT %' OR p.name LIKE 'CORREIA TRANSP%');
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 9, 20, 'Tempo padrão CT' FROM products p WHERE p.category_id = 6 AND (p.name LIKE 'CT %' OR p.name LIKE 'CORREIA TRANSP%');
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 10, 40, 'Tempo padrão CT' FROM products p WHERE p.category_id = 6 AND (p.name LIKE 'CT %' OR p.name LIKE 'CORREIA TRANSP%');
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 11, 90, 'Tempo padrão CT' FROM products p WHERE p.category_id = 6 AND (p.name LIKE 'CT %' OR p.name LIKE 'CORREIA TRANSP%');
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 12, 60, 'Tempo padrão CT' FROM products p WHERE p.category_id = 6 AND (p.name LIKE 'CT %' OR p.name LIKE 'CORREIA TRANSP%');
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 13, 120, 'Tempo padrão CT' FROM products p WHERE p.category_id = 6 AND (p.name LIKE 'CT %' OR p.name LIKE 'CORREIA TRANSP%');
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 14, 60, 'Tempo padrão CT' FROM products p WHERE p.category_id = 6 AND (p.name LIKE 'CT %' OR p.name LIKE 'CORREIA TRANSP%');
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 15, 45, 'Tempo padrão CT' FROM products p WHERE p.category_id = 6 AND (p.name LIKE 'CT %' OR p.name LIKE 'CORREIA TRANSP%');
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 16, 180, 'Tempo padrão CT' FROM products p WHERE p.category_id = 6 AND (p.name LIKE 'CT %' OR p.name LIKE 'CORREIA TRANSP%');
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 17, 60, 'Tempo padrão CT' FROM products p WHERE p.category_id = 6 AND (p.name LIKE 'CT %' OR p.name LIKE 'CORREIA TRANSP%');
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 18, 80, 'Tempo padrão CT' FROM products p WHERE p.category_id = 6 AND (p.name LIKE 'CT %' OR p.name LIKE 'CORREIA TRANSP%');
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 19, 90, 'Tempo padrão CT' FROM products p WHERE p.category_id = 6 AND (p.name LIKE 'CT %' OR p.name LIKE 'CORREIA TRANSP%');
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 20, 30, 'Tempo padrão CT' FROM products p WHERE p.category_id = 6 AND (p.name LIKE 'CT %' OR p.name LIKE 'CORREIA TRANSP%');
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 21, 25, 'Tempo padrão CT' FROM products p WHERE p.category_id = 6 AND (p.name LIKE 'CT %' OR p.name LIKE 'CORREIA TRANSP%');
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 22, 20, 'Tempo padrão CT' FROM products p WHERE p.category_id = 6 AND (p.name LIKE 'CT %' OR p.name LIKE 'CORREIA TRANSP%');

-- =====================================================
-- TEMPOS PARA OUTROS PRODUTOS PRODUZIDOS
-- Total estimado: ~8 horas (480 min) - padrão médio
-- =====================================================
INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 8, 15, 'Tempo padrão genérico' FROM products p 
WHERE p.category_id = 6 
  AND p.name NOT LIKE 'CS %' AND p.name NOT LIKE 'PV %' 
  AND p.name NOT LIKE 'CT %' AND p.name NOT LIKE 'CORREIA TRANSP%';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 9, 10, 'Tempo padrão genérico' FROM products p 
WHERE p.category_id = 6 
  AND p.name NOT LIKE 'CS %' AND p.name NOT LIKE 'PV %' 
  AND p.name NOT LIKE 'CT %' AND p.name NOT LIKE 'CORREIA TRANSP%';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 10, 20, 'Tempo padrão genérico' FROM products p 
WHERE p.category_id = 6 
  AND p.name NOT LIKE 'CS %' AND p.name NOT LIKE 'PV %' 
  AND p.name NOT LIKE 'CT %' AND p.name NOT LIKE 'CORREIA TRANSP%';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 11, 45, 'Tempo padrão genérico' FROM products p 
WHERE p.category_id = 6 
  AND p.name NOT LIKE 'CS %' AND p.name NOT LIKE 'PV %' 
  AND p.name NOT LIKE 'CT %' AND p.name NOT LIKE 'CORREIA TRANSP%';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 12, 30, 'Tempo padrão genérico' FROM products p 
WHERE p.category_id = 6 
  AND p.name NOT LIKE 'CS %' AND p.name NOT LIKE 'PV %' 
  AND p.name NOT LIKE 'CT %' AND p.name NOT LIKE 'CORREIA TRANSP%';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 13, 60, 'Tempo padrão genérico' FROM products p 
WHERE p.category_id = 6 
  AND p.name NOT LIKE 'CS %' AND p.name NOT LIKE 'PV %' 
  AND p.name NOT LIKE 'CT %' AND p.name NOT LIKE 'CORREIA TRANSP%';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 14, 30, 'Tempo padrão genérico' FROM products p 
WHERE p.category_id = 6 
  AND p.name NOT LIKE 'CS %' AND p.name NOT LIKE 'PV %' 
  AND p.name NOT LIKE 'CT %' AND p.name NOT LIKE 'CORREIA TRANSP%';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 15, 25, 'Tempo padrão genérico' FROM products p 
WHERE p.category_id = 6 
  AND p.name NOT LIKE 'CS %' AND p.name NOT LIKE 'PV %' 
  AND p.name NOT LIKE 'CT %' AND p.name NOT LIKE 'CORREIA TRANSP%';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 16, 90, 'Tempo padrão genérico' FROM products p 
WHERE p.category_id = 6 
  AND p.name NOT LIKE 'CS %' AND p.name NOT LIKE 'PV %' 
  AND p.name NOT LIKE 'CT %' AND p.name NOT LIKE 'CORREIA TRANSP%';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 17, 30, 'Tempo padrão genérico' FROM products p 
WHERE p.category_id = 6 
  AND p.name NOT LIKE 'CS %' AND p.name NOT LIKE 'PV %' 
  AND p.name NOT LIKE 'CT %' AND p.name NOT LIKE 'CORREIA TRANSP%';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 18, 40, 'Tempo padrão genérico' FROM products p 
WHERE p.category_id = 6 
  AND p.name NOT LIKE 'CS %' AND p.name NOT LIKE 'PV %' 
  AND p.name NOT LIKE 'CT %' AND p.name NOT LIKE 'CORREIA TRANSP%';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 19, 45, 'Tempo padrão genérico' FROM products p 
WHERE p.category_id = 6 
  AND p.name NOT LIKE 'CS %' AND p.name NOT LIKE 'PV %' 
  AND p.name NOT LIKE 'CT %' AND p.name NOT LIKE 'CORREIA TRANSP%';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 20, 20, 'Tempo padrão genérico' FROM products p 
WHERE p.category_id = 6 
  AND p.name NOT LIKE 'CS %' AND p.name NOT LIKE 'PV %' 
  AND p.name NOT LIKE 'CT %' AND p.name NOT LIKE 'CORREIA TRANSP%';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 21, 15, 'Tempo padrão genérico' FROM products p 
WHERE p.category_id = 6 
  AND p.name NOT LIKE 'CS %' AND p.name NOT LIKE 'PV %' 
  AND p.name NOT LIKE 'CT %' AND p.name NOT LIKE 'CORREIA TRANSP%';

INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, observacao)
SELECT p.id, 22, 10, 'Tempo padrão genérico' FROM products p 
WHERE p.category_id = 6 
  AND p.name NOT LIKE 'CS %' AND p.name NOT LIKE 'PV %' 
  AND p.name NOT LIKE 'CT %' AND p.name NOT LIKE 'CORREIA TRANSP%';

-- =====================================================
-- VERIFICAÇÃO FINAL
-- =====================================================
SELECT 'TEMPOS DE PRODUÇÃO POPULADOS' as info;
SELECT COUNT(*) as total_registros FROM produtos_tempo_etapa;

SELECT 
    CASE 
        WHEN observacao LIKE '%CS%' THEN 'CS - Sincronizada'
        WHEN observacao LIKE '%PV%' THEN 'PV - Poly-V'
        WHEN observacao LIKE '%CT%' THEN 'CT - Transportadora'
        ELSE 'OUTROS'
    END as tipo,
    COUNT(DISTINCT produto_id) as produtos,
    SUM(tempo_padrao_minutos) / COUNT(DISTINCT produto_id) as tempo_medio_total_min
FROM produtos_tempo_etapa
GROUP BY 1
ORDER BY produtos DESC;
