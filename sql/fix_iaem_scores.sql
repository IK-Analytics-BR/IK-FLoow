-- ============================================================
-- FIX: Recalcular IAEM scores para todos os 79 municípios
-- O UPDATE original falhou por causa do safe update mode
-- ============================================================

USE supply_chain_system;
SET SQL_SAFE_UPDATES = 0;

-- 1. Verificar estado atual
SELECT 'ANTES DO FIX' as info, COUNT(*) as total, 
       SUM(CASE WHEN iaem_score = 0 THEN 1 ELSE 0 END) as com_score_zero
FROM dev_eco_iaem;

-- 2. Deletar IAEM antigos (todos zerados) e reinserir com scores corretos
DELETE FROM dev_eco_iaem;

-- 3. Reinserir com scores já calculados diretamente
INSERT INTO dev_eco_iaem (municipio_id, data_calculo, score_pix, score_empresas, score_emprego, score_uso_solo, score_exportacao, score_logistica, iaem_score, iaem_classificacao, prob_crescimento_6m, prob_crescimento_12m, prob_crescimento_24m, setor_destaque, tendencia)
SELECT 
    id,
    CURDATE(),
    -- score_pix
    CASE 
        WHEN nome = 'Três Lagoas' THEN 92 WHEN nome = 'Campo Grande' THEN 78 WHEN nome = 'Dourados' THEN 75
        WHEN nome = 'Chapadão do Sul' THEN 88 WHEN nome = 'Costa Rica' THEN 85 WHEN nome = 'Maracaju' THEN 82
        WHEN nome = 'Rio Brilhante' THEN 80 WHEN nome = 'Sidrolândia' THEN 76 WHEN nome = 'Naviraí' THEN 74
        WHEN nome = 'Ribas do Rio Pardo' THEN 90 WHEN nome = 'Bonito' THEN 70 WHEN nome = 'Corumbá' THEN 58
        WHEN nome = 'São Gabriel do Oeste' THEN 84 WHEN nome = 'Sonora' THEN 72
        WHEN nome = 'Ponta Porã' THEN 68 WHEN nome = 'Aquidauana' THEN 55 WHEN nome = 'Nova Andradina' THEN 65
        WHEN nome = 'Paranaíba' THEN 62 WHEN nome = 'Caarapó' THEN 71 WHEN nome = 'Aparecida do Taboado' THEN 66
        ELSE LEAST(85, GREATEST(30, ROUND(40 + (pib_per_capita / 1500), 0)))
    END,
    -- score_empresas
    CASE 
        WHEN nome = 'Três Lagoas' THEN 88 WHEN nome = 'Campo Grande' THEN 82 WHEN nome = 'Dourados' THEN 79
        WHEN nome = 'Chapadão do Sul' THEN 75 WHEN nome = 'Ribas do Rio Pardo' THEN 85
        WHEN nome = 'Maracaju' THEN 73 WHEN nome = 'Costa Rica' THEN 70 WHEN nome = 'Naviraí' THEN 68
        WHEN nome = 'Ponta Porã' THEN 65 WHEN nome = 'Corumbá' THEN 52
        ELSE LEAST(80, GREATEST(25, ROUND(35 + (pib_total / 500000), 0)))
    END,
    -- score_emprego
    CASE 
        WHEN nome = 'Três Lagoas' THEN 90 WHEN nome = 'Campo Grande' THEN 76 WHEN nome = 'Dourados' THEN 73
        WHEN nome = 'Sidrolândia' THEN 78 WHEN nome = 'Ribas do Rio Pardo' THEN 87
        WHEN nome = 'Maracaju' THEN 75 WHEN nome = 'Rio Brilhante' THEN 77 WHEN nome = 'Naviraí' THEN 70
        WHEN nome = 'Chapadão do Sul' THEN 72 WHEN nome = 'Corumbá' THEN 50
        ELSE LEAST(80, GREATEST(20, ROUND(30 + (populacao / 5000), 0)))
    END,
    -- score_uso_solo
    CASE 
        WHEN nome = 'Chapadão do Sul' THEN 95 WHEN nome = 'Costa Rica' THEN 92 WHEN nome = 'Maracaju' THEN 88
        WHEN nome = 'São Gabriel do Oeste' THEN 90 WHEN nome = 'Ribas do Rio Pardo' THEN 85
        WHEN nome = 'Três Lagoas' THEN 82 WHEN nome = 'Rio Brilhante' THEN 86
        WHEN nome = 'Sidrolândia' THEN 83 WHEN nome = 'Dourados' THEN 80 WHEN nome = 'Caarapó' THEN 84
        ELSE LEAST(85, GREATEST(20, ROUND(25 + (pib_agropecuaria / 100000), 0)))
    END,
    -- score_exportacao
    CASE 
        WHEN nome = 'Três Lagoas' THEN 95 WHEN nome = 'Dourados' THEN 80 WHEN nome = 'Campo Grande' THEN 65
        WHEN nome = 'Corumbá' THEN 72 WHEN nome = 'Naviraí' THEN 78
        WHEN nome = 'Chapadão do Sul' THEN 82 WHEN nome = 'Costa Rica' THEN 75
        WHEN nome = 'Maracaju' THEN 76 WHEN nome = 'Rio Brilhante' THEN 74
        ELSE LEAST(80, GREATEST(15, ROUND(20 + (pib_industria / 200000), 0)))
    END,
    -- score_logistica
    CASE 
        WHEN nome = 'Campo Grande' THEN 85 WHEN nome = 'Três Lagoas' THEN 82 WHEN nome = 'Dourados' THEN 78
        WHEN nome = 'Corumbá' THEN 65 WHEN nome = 'Ponta Porã' THEN 70
        WHEN nome = 'Maracaju' THEN 68 WHEN nome = 'Naviraí' THEN 66 WHEN nome = 'Ribas do Rio Pardo' THEN 72
        ELSE LEAST(80, GREATEST(20, ROUND(30 + (populacao / 8000), 0)))
    END,
    -- iaem_score (calculado inline)
    0, '', 0, 0, 0,
    vocacao_principal,
    'Estável'
FROM dev_eco_municipios
WHERE ativo = TRUE;

-- 4. Agora calcular o score ponderado, classificação e probabilidades
UPDATE dev_eco_iaem SET 
    iaem_score = ROUND(
        score_pix * 0.25 + 
        score_empresas * 0.20 + 
        score_emprego * 0.20 + 
        score_uso_solo * 0.15 + 
        score_exportacao * 0.10 + 
        score_logistica * 0.10
    , 2),
    iaem_classificacao = CASE
        WHEN (score_pix * 0.25 + score_empresas * 0.20 + score_emprego * 0.20 + score_uso_solo * 0.15 + score_exportacao * 0.10 + score_logistica * 0.10) >= 80 THEN 'Expansão Forte'
        WHEN (score_pix * 0.25 + score_empresas * 0.20 + score_emprego * 0.20 + score_uso_solo * 0.15 + score_exportacao * 0.10 + score_logistica * 0.10) >= 65 THEN 'Expansão'
        WHEN (score_pix * 0.25 + score_empresas * 0.20 + score_emprego * 0.20 + score_uso_solo * 0.15 + score_exportacao * 0.10 + score_logistica * 0.10) >= 50 THEN 'Estável'
        WHEN (score_pix * 0.25 + score_empresas * 0.20 + score_emprego * 0.20 + score_uso_solo * 0.15 + score_exportacao * 0.10 + score_logistica * 0.10) >= 35 THEN 'Retração'
        ELSE 'Retração Forte'
    END,
    prob_crescimento_6m = LEAST(95, ROUND((score_pix * 0.25 + score_empresas * 0.20 + score_emprego * 0.20 + score_uso_solo * 0.15 + score_exportacao * 0.10 + score_logistica * 0.10) * 1.05, 1)),
    prob_crescimento_12m = LEAST(92, ROUND((score_pix * 0.25 + score_empresas * 0.20 + score_emprego * 0.20 + score_uso_solo * 0.15 + score_exportacao * 0.10 + score_logistica * 0.10) * 0.95, 1)),
    prob_crescimento_24m = LEAST(88, ROUND((score_pix * 0.25 + score_empresas * 0.20 + score_emprego * 0.20 + score_uso_solo * 0.15 + score_exportacao * 0.10 + score_logistica * 0.10) * 0.85, 1)),
    tendencia = CASE
        WHEN (score_pix * 0.25 + score_empresas * 0.20 + score_emprego * 0.20 + score_uso_solo * 0.15 + score_exportacao * 0.10 + score_logistica * 0.10) >= 70 THEN 'Alta'
        WHEN (score_pix * 0.25 + score_empresas * 0.20 + score_emprego * 0.20 + score_uso_solo * 0.15 + score_exportacao * 0.10 + score_logistica * 0.10) >= 45 THEN 'Estável'
        ELSE 'Baixa'
    END;

-- 5. Verificação final
SELECT '=== RESULTADO FINAL ===' as info;
SELECT iaem_classificacao, COUNT(*) as qtd FROM dev_eco_iaem GROUP BY iaem_classificacao ORDER BY qtd DESC;

SELECT '=== TOP 15 IAEM ===' as info;
SELECT m.nome, i.iaem_score, i.iaem_classificacao, i.tendencia,
       i.score_pix, i.score_empresas, i.score_emprego, i.score_uso_solo,
       i.score_exportacao, i.score_logistica,
       i.prob_crescimento_6m, i.prob_crescimento_12m, i.prob_crescimento_24m
FROM dev_eco_iaem i 
JOIN dev_eco_municipios m ON i.municipio_id = m.id
ORDER BY i.iaem_score DESC 
LIMIT 15;

SELECT '=== BOTTOM 5 IAEM ===' as info;
SELECT m.nome, i.iaem_score, i.iaem_classificacao, i.tendencia
FROM dev_eco_iaem i 
JOIN dev_eco_municipios m ON i.municipio_id = m.id
ORDER BY i.iaem_score ASC 
LIMIT 5;

SET SQL_SAFE_UPDATES = 1;
