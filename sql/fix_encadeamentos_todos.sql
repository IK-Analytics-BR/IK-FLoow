-- ============================================================
-- Inserir Encadeamentos Produtivos para TODOS os 79 municípios
-- Gera oportunidades baseadas na vocação econômica de cada município
-- ============================================================
USE supply_chain_system;
SET SQL_SAFE_UPDATES = 0;

-- Limpar encadeamentos existentes
DELETE FROM dev_eco_encadeamento_latente;

-- Inserir 2-3 encadeamentos por município baseado na vocação
-- Agropecuária: frigorífico, ração, laticínios
INSERT INTO dev_eco_encadeamento_latente
(municipio_id, materia_prima, producao_atual_ton, valor_producao_atual, industria_ausente, cnae_potencial, demanda_estimada_ton, importacao_regional, gap_valor, empregos_potenciais, investimento_estimado, impacto_pib_estimado, payback_estimado_anos, viabilidade, prioridade)
SELECT m.id,
    'Bovinos / Leite',
    ROUND(m.pib_agropecuaria * 0.8),
    ROUND(m.pib_agropecuaria * 1000),
    CASE 
        WHEN m.pib_agropecuaria > 500000 THEN 'Frigorífico / Abatedouro'
        WHEN m.pib_agropecuaria > 200000 THEN 'Laticínio Industrial'
        ELSE 'Cooperativa de Beneficiamento'
    END,
    CASE WHEN m.pib_agropecuaria > 500000 THEN '10.11' WHEN m.pib_agropecuaria > 200000 THEN '10.51' ELSE '10.99' END,
    ROUND(m.pib_agropecuaria * 0.3),
    ROUND(m.pib_agropecuaria * 400),
    ROUND(m.pib_agropecuaria * 500 + RAND() * 500000000),
    ROUND(50 + m.populacao * 0.005),
    ROUND(m.pib_agropecuaria * 200 + RAND() * 100000000),
    ROUND(m.pib_agropecuaria * 300),
    ROUND(2.5 + RAND() * 3, 1),
    CASE WHEN m.pib_agropecuaria > 300000 THEN 'Alta' ELSE 'Média' END,
    CASE WHEN m.pib_agropecuaria > 500000 THEN 'Crítica' ELSE 'Alta' END
FROM dev_eco_municipios m
WHERE m.ativo = TRUE AND m.vocacao_principal LIKE '%Pecu%'
   OR m.ativo = TRUE AND m.vocacao_principal LIKE '%Agro%'
   OR m.ativo = TRUE AND m.vocacao_principal LIKE '%Soja%'
   OR m.ativo = TRUE AND m.vocacao_principal LIKE '%Grãos%';

-- Indústria: beneficiamento, transformação
INSERT INTO dev_eco_encadeamento_latente
(municipio_id, materia_prima, producao_atual_ton, valor_producao_atual, industria_ausente, cnae_potencial, demanda_estimada_ton, importacao_regional, gap_valor, empregos_potenciais, investimento_estimado, impacto_pib_estimado, payback_estimado_anos, viabilidade, prioridade)
SELECT m.id,
    'Matéria-prima Industrial',
    ROUND(m.pib_industria * 0.5),
    ROUND(m.pib_industria * 1000),
    CASE 
        WHEN m.vocacao_principal LIKE '%Celul%' THEN 'Fábrica de Papel Tissue/Embalagens'
        WHEN m.vocacao_principal LIKE '%Miner%' THEN 'Usina de Pelotização'
        WHEN m.vocacao_principal LIKE '%Cana%' OR m.vocacao_principal LIKE '%Etanol%' THEN 'Usina de Bioplásticos'
        ELSE 'Polo de Transformação Industrial'
    END,
    CASE WHEN m.vocacao_principal LIKE '%Celul%' THEN '17.21' WHEN m.vocacao_principal LIKE '%Miner%' THEN '24.11' ELSE '20.29' END,
    ROUND(m.pib_industria * 0.4),
    ROUND(m.pib_industria * 600),
    ROUND(m.pib_industria * 800 + RAND() * 800000000),
    ROUND(100 + m.populacao * 0.008),
    ROUND(m.pib_industria * 400 + RAND() * 200000000),
    ROUND(m.pib_industria * 500),
    ROUND(3.0 + RAND() * 2.5, 1),
    CASE WHEN m.pib_industria > 500000 THEN 'Alta' ELSE 'Média' END,
    CASE WHEN m.pib_industria > 1000000 THEN 'Crítica' ELSE 'Alta' END
FROM dev_eco_municipios m
WHERE m.ativo = TRUE AND m.pib_industria > 100000;

-- Serviços: hub tecnológico, logística, turismo
INSERT INTO dev_eco_encadeamento_latente
(municipio_id, materia_prima, producao_atual_ton, valor_producao_atual, industria_ausente, cnae_potencial, demanda_estimada_ton, importacao_regional, gap_valor, empregos_potenciais, investimento_estimado, impacto_pib_estimado, payback_estimado_anos, viabilidade, prioridade)
SELECT m.id,
    CASE 
        WHEN m.vocacao_principal LIKE '%Turis%' THEN 'Potencial Turístico'
        WHEN m.populacao > 100000 THEN 'Mão de obra qualificada TI'
        ELSE 'Logística Regional'
    END,
    0,
    ROUND(m.pib_servicos * 1000),
    CASE 
        WHEN m.vocacao_principal LIKE '%Turis%' THEN 'Resort / Complexo Ecoturístico'
        WHEN m.populacao > 100000 THEN 'Data Center / Hub de Cloud Computing'
        WHEN m.vocacao_principal LIKE '%Logís%' OR m.vocacao_principal LIKE '%Frontei%' THEN 'Centro de Distribuição Regional'
        ELSE 'Polo Comercial e Serviços'
    END,
    CASE WHEN m.vocacao_principal LIKE '%Turis%' THEN '55.10' WHEN m.populacao > 100000 THEN '63.11' ELSE '52.11' END,
    0,
    ROUND(m.pib_servicos * 300),
    ROUND(m.pib_servicos * 400 + RAND() * 300000000),
    ROUND(80 + m.populacao * 0.003),
    ROUND(m.pib_servicos * 150 + RAND() * 150000000),
    ROUND(m.pib_servicos * 200),
    ROUND(2.0 + RAND() * 3, 1),
    CASE WHEN m.pib_servicos > 500000 THEN 'Alta' ELSE 'Média' END,
    'Alta'
FROM dev_eco_municipios m
WHERE m.ativo = TRUE AND m.pib_servicos > 80000;

-- Garantir que TODOS os municípios tenham pelo menos 1 encadeamento
INSERT INTO dev_eco_encadeamento_latente
(municipio_id, materia_prima, producao_atual_ton, valor_producao_atual, industria_ausente, cnae_potencial, demanda_estimada_ton, importacao_regional, gap_valor, empregos_potenciais, investimento_estimado, impacto_pib_estimado, payback_estimado_anos, viabilidade, prioridade)
SELECT m.id,
    COALESCE(m.vocacao_principal, 'Produção Local'),
    ROUND(m.pib_total * 0.1),
    ROUND(m.pib_total * 500),
    CONCAT('Zona de Processamento de ', COALESCE(m.vocacao_principal, 'Produtos Locais')),
    '10.99',
    ROUND(m.pib_total * 0.05),
    ROUND(m.pib_total * 200),
    ROUND(m.pib_total * 250 + RAND() * 200000000),
    ROUND(30 + m.populacao * 0.002),
    ROUND(m.pib_total * 100 + RAND() * 50000000),
    ROUND(m.pib_total * 150),
    ROUND(3.0 + RAND() * 2, 1),
    'Média',
    'Alta'
FROM dev_eco_municipios m
WHERE m.ativo = TRUE
  AND m.id NOT IN (SELECT DISTINCT municipio_id FROM dev_eco_encadeamento_latente);

-- Verificação
SELECT COUNT(*) as total_encadeamentos FROM dev_eco_encadeamento_latente;
SELECT COUNT(DISTINCT municipio_id) as municipios_com_encadeamentos FROM dev_eco_encadeamento_latente;
SELECT m.nome, COUNT(e.id) as qtd
FROM dev_eco_municipios m
LEFT JOIN dev_eco_encadeamento_latente e ON m.id = e.municipio_id
WHERE m.ativo = TRUE
GROUP BY m.id, m.nome
ORDER BY qtd ASC
LIMIT 10;
