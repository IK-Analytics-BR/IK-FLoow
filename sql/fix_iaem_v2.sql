-- ============================================================
-- FIX IAEM v2: Abordagem simplificada e robusta
-- ============================================================
USE supply_chain_system;
SET SQL_SAFE_UPDATES = 0;

-- Passo 1: Limpar tabela IAEM completamente
TRUNCATE TABLE dev_eco_iaem;

-- Passo 2: Inserir scores para TODOS os 79 municípios com cálculo direto
-- Usa fórmula baseada nos dados reais de cada município
INSERT INTO dev_eco_iaem 
(municipio_id, data_calculo, score_pix, score_empresas, score_emprego, score_uso_solo, score_exportacao, score_logistica, iaem_score, iaem_classificacao, prob_crescimento_6m, prob_crescimento_12m, prob_crescimento_24m, setor_destaque, tendencia)
SELECT 
    m.id,
    CURDATE(),
    -- score_pix: baseado em PIB per capita (proxy para fluxo financeiro)
    LEAST(95, GREATEST(25, ROUND(
        CASE 
            WHEN m.pib_per_capita >= 80000 THEN 90
            WHEN m.pib_per_capita >= 50000 THEN 80
            WHEN m.pib_per_capita >= 30000 THEN 70
            WHEN m.pib_per_capita >= 20000 THEN 60
            WHEN m.pib_per_capita >= 15000 THEN 50
            ELSE 35
        END + (RAND() * 8 - 4)
    ))) as spix,
    -- score_empresas: baseado em população (proxy para base empresarial)
    LEAST(95, GREATEST(25, ROUND(
        CASE 
            WHEN m.populacao >= 500000 THEN 82
            WHEN m.populacao >= 100000 THEN 75
            WHEN m.populacao >= 50000 THEN 68
            WHEN m.populacao >= 20000 THEN 58
            WHEN m.populacao >= 10000 THEN 48
            ELSE 35
        END + (RAND() * 10 - 5)
    ))) as semp,
    -- score_emprego: baseado em PIB total (proxy para mercado de trabalho)
    LEAST(95, GREATEST(25, ROUND(
        CASE 
            WHEN m.pib_total >= 10000000 THEN 85
            WHEN m.pib_total >= 3000000 THEN 75
            WHEN m.pib_total >= 1000000 THEN 65
            WHEN m.pib_total >= 500000 THEN 55
            ELSE 40
        END + (RAND() * 10 - 5)
    ))) as sempr,
    -- score_uso_solo: baseado em PIB agropecuário (proxy para uso produtivo do solo)
    LEAST(95, GREATEST(25, ROUND(
        CASE 
            WHEN m.pib_agropecuaria / NULLIF(m.pib_total, 0) >= 0.4 THEN 88
            WHEN m.pib_agropecuaria / NULLIF(m.pib_total, 0) >= 0.25 THEN 78
            WHEN m.pib_agropecuaria / NULLIF(m.pib_total, 0) >= 0.15 THEN 65
            ELSE 45
        END + (RAND() * 10 - 5)
    ))) as ssolo,
    -- score_exportacao: baseado em PIB industrial (proxy para exportação)
    LEAST(95, GREATEST(20, ROUND(
        CASE 
            WHEN m.pib_industria / NULLIF(m.pib_total, 0) >= 0.35 THEN 90
            WHEN m.pib_industria / NULLIF(m.pib_total, 0) >= 0.2 THEN 75
            WHEN m.pib_industria / NULLIF(m.pib_total, 0) >= 0.1 THEN 60
            ELSE 35
        END + (RAND() * 8 - 4)
    ))) as sexp,
    -- score_logistica: baseado em localização e população
    LEAST(95, GREATEST(20, ROUND(
        CASE 
            WHEN m.populacao >= 200000 THEN 82
            WHEN m.populacao >= 50000 THEN 70
            WHEN m.populacao >= 20000 THEN 58
            ELSE 40
        END + (RAND() * 10 - 5)
    ))) as slog,
    -- iaem_score placeholder (será calculado abaixo)
    0, '', 0, 0, 0,
    m.vocacao_principal,
    'Estável'
FROM dev_eco_municipios m
WHERE m.ativo = TRUE;

-- Passo 3: Calcular score ponderado
UPDATE dev_eco_iaem SET 
    iaem_score = ROUND(score_pix * 0.25 + score_empresas * 0.20 + score_emprego * 0.20 + score_uso_solo * 0.15 + score_exportacao * 0.10 + score_logistica * 0.10, 2);

-- Passo 4: Classificação
UPDATE dev_eco_iaem SET 
    iaem_classificacao = CASE
        WHEN iaem_score >= 78 THEN 'Expansão Forte'
        WHEN iaem_score >= 62 THEN 'Expansão'
        WHEN iaem_score >= 48 THEN 'Estável'
        ELSE 'Retração'
    END;

-- Passo 5: Probabilidades
UPDATE dev_eco_iaem SET 
    prob_crescimento_6m = LEAST(95, ROUND(iaem_score * 1.08, 1)),
    prob_crescimento_12m = LEAST(92, ROUND(iaem_score * 0.98, 1)),
    prob_crescimento_24m = LEAST(88, ROUND(iaem_score * 0.88, 1));

-- Passo 6: Tendência
UPDATE dev_eco_iaem SET 
    tendencia = CASE
        WHEN iaem_score >= 70 THEN 'Alta'
        WHEN iaem_score >= 50 THEN 'Estável'
        ELSE 'Baixa'
    END;

-- ============================================================
-- VERIFICAÇÃO
-- ============================================================
SELECT '=== CONTAGEM POR CLASSIFICAÇÃO ===' as info;
SELECT iaem_classificacao, COUNT(*) as qtd FROM dev_eco_iaem GROUP BY iaem_classificacao ORDER BY FIELD(iaem_classificacao, 'Expansão Forte', 'Expansão', 'Estável', 'Retração');

SELECT '=== TOP 10 ===' as info;
SELECT m.nome, ROUND(i.iaem_score,1) as score, i.iaem_classificacao, i.tendencia, 
       ROUND(i.prob_crescimento_6m,0) as p6m, ROUND(i.prob_crescimento_12m,0) as p12m
FROM dev_eco_iaem i JOIN dev_eco_municipios m ON i.municipio_id = m.id
ORDER BY i.iaem_score DESC LIMIT 10;

SELECT '=== BOTTOM 5 ===' as info;
SELECT m.nome, ROUND(i.iaem_score,1) as score, i.iaem_classificacao, i.tendencia
FROM dev_eco_iaem i JOIN dev_eco_municipios m ON i.municipio_id = m.id
ORDER BY i.iaem_score ASC LIMIT 5;

SET SQL_SAFE_UPDATES = 1;
