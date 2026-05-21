-- ============================================================
-- MÓDULOS PREMIUM - Portal de Desenvolvimento Econômico MS
-- 1. IAEM - Índice de Antecipação Econômica Municipal
-- 2. Mapa de Encadeamento Produtivo Latente
-- 3. Simulador de Impacto Econômico
-- ============================================================

USE supply_chain_system;

-- ============================================================
-- 1. IAEM - ÍNDICE DE ANTECIPAÇÃO ECONÔMICA MUNICIPAL
-- Modelo de nowcasting municipal baseado em leading indicators
-- ============================================================

-- Dados de fluxo Pix por município (proxy de atividade econômica real)
CREATE TABLE IF NOT EXISTS dev_eco_pix_fluxo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT NOT NULL,
    ano_mes VARCHAR(7) NOT NULL COMMENT 'YYYY-MM',
    volume_pj_recebido DECIMAL(18,2) DEFAULT 0 COMMENT 'Volume Pix recebido por PJ (R$)',
    volume_pj_enviado DECIMAL(18,2) DEFAULT 0 COMMENT 'Volume Pix enviado por PJ (R$)',
    volume_pf_recebido DECIMAL(18,2) DEFAULT 0,
    volume_pf_enviado DECIMAL(18,2) DEFAULT 0,
    qtd_transacoes_pj INT DEFAULT 0,
    qtd_transacoes_pf INT DEFAULT 0,
    ticket_medio_pj DECIMAL(12,2) DEFAULT 0,
    variacao_mensal DECIMAL(8,4) DEFAULT 0 COMMENT '% variação vs mês anterior',
    variacao_anual DECIMAL(8,4) DEFAULT 0 COMMENT '% variação vs mesmo mês ano anterior',
    fonte VARCHAR(50) DEFAULT 'BCB',
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    UNIQUE KEY uk_mun_mes (municipio_id, ano_mes),
    INDEX idx_ano_mes (ano_mes)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Abertura/Fechamento de empresas por CNAE e município
CREATE TABLE IF NOT EXISTS dev_eco_empresas_dinamica (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT NOT NULL,
    ano_mes VARCHAR(7) NOT NULL,
    cnae_secao VARCHAR(5) COMMENT 'Seção CNAE (A-U)',
    cnae_descricao VARCHAR(200),
    abertas INT DEFAULT 0,
    fechadas INT DEFAULT 0,
    saldo INT DEFAULT 0,
    estoque_ativas INT DEFAULT 0,
    variacao_mensal DECIMAL(8,4) DEFAULT 0,
    fonte VARCHAR(50) DEFAULT 'Junta Comercial',
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    INDEX idx_mun_mes (municipio_id, ano_mes),
    INDEX idx_cnae (cnae_secao)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Uso do solo por município (dados de satélite - MapBiomas/INPE)
CREATE TABLE IF NOT EXISTS dev_eco_uso_solo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT NOT NULL,
    ano INT NOT NULL,
    classe VARCHAR(80) NOT NULL COMMENT 'Soja, Cana, Pastagem, Eucalipto, Floresta, Urbano, etc.',
    area_hectares DECIMAL(12,2) DEFAULT 0,
    percentual_territorio DECIMAL(6,3) DEFAULT 0,
    variacao_anual_ha DECIMAL(12,2) DEFAULT 0 COMMENT 'Variação em hectares vs ano anterior',
    variacao_anual_pct DECIMAL(8,4) DEFAULT 0,
    fonte VARCHAR(50) DEFAULT 'MapBiomas',
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    UNIQUE KEY uk_mun_ano_classe (municipio_id, ano, classe),
    INDEX idx_classe (classe)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Emprego mensal por município e setor (CAGED)
CREATE TABLE IF NOT EXISTS dev_eco_emprego_mensal (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT NOT NULL,
    ano_mes VARCHAR(7) NOT NULL,
    setor_ibge VARCHAR(5) COMMENT 'Código setor IBGE',
    setor_descricao VARCHAR(100),
    admissoes INT DEFAULT 0,
    desligamentos INT DEFAULT 0,
    saldo INT DEFAULT 0,
    estoque INT DEFAULT 0,
    salario_medio DECIMAL(10,2) DEFAULT 0,
    fonte VARCHAR(50) DEFAULT 'CAGED/MTE',
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    INDEX idx_mun_mes (municipio_id, ano_mes),
    INDEX idx_setor (setor_ibge)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- IAEM calculado por município (resultado do modelo)
CREATE TABLE IF NOT EXISTS dev_eco_iaem (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT NOT NULL,
    data_calculo DATE NOT NULL,
    -- Componentes do índice (0-100 cada)
    score_pix DECIMAL(6,2) DEFAULT 0 COMMENT 'Dinâmica financeira via Pix',
    score_empresas DECIMAL(6,2) DEFAULT 0 COMMENT 'Dinâmica empresarial',
    score_emprego DECIMAL(6,2) DEFAULT 0 COMMENT 'Mercado de trabalho',
    score_uso_solo DECIMAL(6,2) DEFAULT 0 COMMENT 'Expansão produtiva',
    score_exportacao DECIMAL(6,2) DEFAULT 0 COMMENT 'Comércio exterior',
    score_logistica DECIMAL(6,2) DEFAULT 0 COMMENT 'Atividade logística',
    -- Índice composto (0-100)
    iaem_score DECIMAL(6,2) DEFAULT 0 COMMENT 'Índice final ponderado',
    iaem_classificacao VARCHAR(30) COMMENT 'Expansão Forte, Expansão, Estável, Retração, Retração Forte',
    -- Previsões
    prob_crescimento_6m DECIMAL(6,2) DEFAULT 0 COMMENT '% probabilidade crescimento 6 meses',
    prob_crescimento_12m DECIMAL(6,2) DEFAULT 0 COMMENT '% probabilidade crescimento 12 meses',
    prob_crescimento_24m DECIMAL(6,2) DEFAULT 0 COMMENT '% probabilidade crescimento 24 meses',
    setor_destaque VARCHAR(100) COMMENT 'Setor com maior sinal de crescimento',
    tendencia VARCHAR(20) COMMENT 'Alta, Estável, Baixa',
    observacoes TEXT,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    UNIQUE KEY uk_mun_data (municipio_id, data_calculo),
    INDEX idx_score (iaem_score DESC),
    INDEX idx_classificacao (iaem_classificacao)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 2. MAPA DE ENCADEAMENTO PRODUTIVO LATENTE
-- Gap analysis: o que poderia existir mas não existe
-- ============================================================

CREATE TABLE IF NOT EXISTS dev_eco_encadeamento_latente (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT NOT NULL,
    -- O que existe
    materia_prima VARCHAR(200) NOT NULL COMMENT 'Ex: Abacaxi, Soja, Leite, Eucalipto',
    producao_atual_ton DECIMAL(15,2) DEFAULT 0,
    valor_producao_atual DECIMAL(15,2) DEFAULT 0,
    -- O que falta
    industria_ausente VARCHAR(200) NOT NULL COMMENT 'Ex: Fábrica de suco, Esmagadora, Laticínio',
    cnae_potencial VARCHAR(10),
    -- Análise de viabilidade
    demanda_estimada_ton DECIMAL(15,2) DEFAULT 0 COMMENT 'Demanda regional estimada',
    importacao_regional DECIMAL(15,2) DEFAULT 0 COMMENT 'Quanto a região importa desse produto',
    gap_valor DECIMAL(15,2) DEFAULT 0 COMMENT 'Valor do gap (oportunidade em R$)',
    -- Impacto estimado
    empregos_potenciais INT DEFAULT 0,
    investimento_estimado DECIMAL(15,2) DEFAULT 0,
    impacto_pib_estimado DECIMAL(15,2) DEFAULT 0 COMMENT 'Impacto estimado no PIB municipal',
    payback_estimado_anos DECIMAL(4,1) DEFAULT 0,
    -- Classificação
    viabilidade VARCHAR(20) DEFAULT 'Média' COMMENT 'Alta, Média, Baixa',
    prioridade VARCHAR(20) DEFAULT 'Média' COMMENT 'Crítica, Alta, Média, Baixa',
    status VARCHAR(30) DEFAULT 'Identificado' COMMENT 'Identificado, Em Estudo, Em Implantação, Implantado',
    observacoes TEXT,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    INDEX idx_viabilidade (viabilidade),
    INDEX idx_prioridade (prioridade)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 3. SIMULADOR DE IMPACTO ECONÔMICO
-- Parâmetros e resultados de simulações
-- ============================================================

-- Parâmetros de simulação (multiplicadores econômicos por setor)
CREATE TABLE IF NOT EXISTS dev_eco_multiplicadores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setor VARCHAR(100) NOT NULL,
    cnae_secao VARCHAR(5),
    -- Multiplicadores de emprego
    emprego_direto_por_milhao DECIMAL(8,2) DEFAULT 0 COMMENT 'Empregos diretos por R$ 1 milhão investido',
    multiplicador_emprego DECIMAL(6,3) DEFAULT 1.5 COMMENT 'Multiplicador de emprego indireto/induzido',
    -- Multiplicadores econômicos
    multiplicador_pib DECIMAL(6,3) DEFAULT 1.8 COMMENT 'Multiplicador do PIB (Leontief)',
    multiplicador_renda DECIMAL(6,3) DEFAULT 1.4 COMMENT 'Multiplicador de renda',
    multiplicador_tributo DECIMAL(6,3) DEFAULT 0.25 COMMENT 'Carga tributária efetiva do setor',
    -- Parâmetros de Pix
    pix_estimado_por_emprego DECIMAL(12,2) DEFAULT 0 COMMENT 'Volume Pix mensal estimado por emprego',
    -- Tempo
    tempo_implantacao_meses INT DEFAULT 24,
    tempo_maturacao_meses INT DEFAULT 36,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_setor (setor)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Simulações realizadas
CREATE TABLE IF NOT EXISTS dev_eco_simulacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT NOT NULL,
    data_simulacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario VARCHAR(100),
    -- Inputs
    tipo_empreendimento VARCHAR(200) NOT NULL,
    setor VARCHAR(100) NOT NULL,
    investimento_total DECIMAL(15,2) NOT NULL,
    porte VARCHAR(30) DEFAULT 'Médio' COMMENT 'Micro, Pequeno, Médio, Grande',
    area_m2 DECIMAL(12,2) DEFAULT 0,
    -- Outputs calculados
    empregos_diretos INT DEFAULT 0,
    empregos_indiretos INT DEFAULT 0,
    empregos_totais INT DEFAULT 0,
    impacto_pib_anual DECIMAL(15,2) DEFAULT 0,
    impacto_renda_anual DECIMAL(15,2) DEFAULT 0,
    impacto_tributos_anual DECIMAL(15,2) DEFAULT 0,
    impacto_pix_mensal DECIMAL(15,2) DEFAULT 0,
    variacao_pib_municipal DECIMAL(8,4) DEFAULT 0 COMMENT '% de variação no PIB municipal',
    novo_ranking_estadual INT DEFAULT 0,
    ranking_anterior INT DEFAULT 0,
    -- Análise
    viabilidade_score DECIMAL(6,2) DEFAULT 0 COMMENT '0-100',
    recomendacao TEXT,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    INDEX idx_municipio (municipio_id),
    INDEX idx_setor (setor)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- DADOS INICIAIS - Multiplicadores por setor
-- ============================================================
INSERT INTO dev_eco_multiplicadores (setor, cnae_secao, emprego_direto_por_milhao, multiplicador_emprego, multiplicador_pib, multiplicador_renda, multiplicador_tributo, pix_estimado_por_emprego, tempo_implantacao_meses, tempo_maturacao_meses) VALUES
('Celulose e Papel', 'C', 2.8, 2.1, 2.3, 1.6, 0.22, 8500, 36, 48),
('Frigorífico Bovino', 'C', 8.5, 1.8, 1.9, 1.5, 0.18, 4200, 24, 36),
('Frigorífico Aves', 'C', 12.0, 1.7, 1.8, 1.4, 0.17, 3800, 18, 30),
('Usina Sucroalcooleira', 'C', 6.2, 2.0, 2.1, 1.5, 0.20, 5500, 30, 42),
('Esmagadora de Soja', 'C', 3.5, 1.9, 2.2, 1.5, 0.21, 7200, 24, 36),
('Laticínio', 'C', 9.0, 1.6, 1.7, 1.4, 0.16, 3500, 12, 24),
('Indústria de Sucos', 'C', 7.5, 1.5, 1.6, 1.3, 0.15, 3200, 12, 24),
('Fábrica de Ração', 'C', 4.2, 1.7, 1.8, 1.4, 0.18, 5800, 12, 24),
('Têxtil/Confecção', 'C', 15.0, 1.4, 1.5, 1.3, 0.14, 2800, 12, 18),
('Tecnologia/Software', 'J', 5.0, 2.5, 2.8, 2.0, 0.28, 12000, 6, 12),
('Logística/Armazém', 'H', 6.0, 1.6, 1.7, 1.3, 0.16, 4500, 12, 24),
('Hotel/Resort', 'I', 10.0, 1.8, 1.9, 1.5, 0.15, 3000, 24, 36),
('Mineração', 'B', 2.0, 2.2, 2.5, 1.7, 0.25, 9500, 48, 60),
('Energia Solar/Eólica', 'D', 3.0, 1.9, 2.0, 1.4, 0.20, 7000, 18, 30),
('Comércio Atacadista', 'G', 8.0, 1.3, 1.4, 1.2, 0.12, 3500, 6, 12),
('Agricultura de Precisão', 'A', 4.0, 1.8, 2.0, 1.5, 0.18, 6500, 12, 24);

-- ============================================================
-- DADOS INICIAIS - IAEM (dados simulados para demonstração)
-- Baseados em tendências reais dos municípios
-- ============================================================
INSERT INTO dev_eco_iaem (municipio_id, data_calculo, score_pix, score_empresas, score_emprego, score_uso_solo, score_exportacao, score_logistica, iaem_score, iaem_classificacao, prob_crescimento_6m, prob_crescimento_12m, prob_crescimento_24m, setor_destaque, tendencia) 
SELECT id, CURDATE(),
    CASE 
        WHEN nome = 'Três Lagoas' THEN 92 WHEN nome = 'Campo Grande' THEN 78 WHEN nome = 'Dourados' THEN 75
        WHEN nome = 'Chapadão do Sul' THEN 88 WHEN nome = 'Costa Rica' THEN 85 WHEN nome = 'Maracaju' THEN 82
        WHEN nome = 'Rio Brilhante' THEN 80 WHEN nome = 'Sidrolândia' THEN 76 WHEN nome = 'Naviraí' THEN 74
        WHEN nome = 'Ribas do Rio Pardo' THEN 90 WHEN nome = 'Bonito' THEN 70 WHEN nome = 'Corumbá' THEN 58
        WHEN nome = 'São Gabriel do Oeste' THEN 84 WHEN nome = 'Sonora' THEN 72
        ELSE ROUND(40 + (pib_per_capita / 1500), 0)
    END as score_pix,
    CASE 
        WHEN nome = 'Três Lagoas' THEN 88 WHEN nome = 'Campo Grande' THEN 82 WHEN nome = 'Dourados' THEN 79
        WHEN nome = 'Chapadão do Sul' THEN 75 WHEN nome = 'Ribas do Rio Pardo' THEN 85
        ELSE ROUND(35 + (pib_total / 500000), 0)
    END as score_empresas,
    CASE 
        WHEN nome = 'Três Lagoas' THEN 90 WHEN nome = 'Campo Grande' THEN 76 WHEN nome = 'Dourados' THEN 73
        WHEN nome = 'Sidrolândia' THEN 78 WHEN nome = 'Ribas do Rio Pardo' THEN 87
        ELSE ROUND(30 + (populacao / 5000), 0)
    END as score_emprego,
    CASE 
        WHEN nome = 'Chapadão do Sul' THEN 95 WHEN nome = 'Costa Rica' THEN 92 WHEN nome = 'Maracaju' THEN 88
        WHEN nome = 'São Gabriel do Oeste' THEN 90 WHEN nome = 'Ribas do Rio Pardo' THEN 85
        WHEN nome = 'Três Lagoas' THEN 82 WHEN nome = 'Rio Brilhante' THEN 86
        ELSE ROUND(25 + (pib_agropecuaria / 100000), 0)
    END as score_uso_solo,
    CASE 
        WHEN nome = 'Três Lagoas' THEN 95 WHEN nome = 'Dourados' THEN 80 WHEN nome = 'Campo Grande' THEN 65
        WHEN nome = 'Corumbá' THEN 72 WHEN nome = 'Naviraí' THEN 78
        ELSE ROUND(20 + (pib_industria / 200000), 0)
    END as score_exportacao,
    CASE 
        WHEN nome = 'Campo Grande' THEN 85 WHEN nome = 'Três Lagoas' THEN 82 WHEN nome = 'Dourados' THEN 78
        WHEN nome = 'Corumbá' THEN 65 WHEN nome = 'Ponta Porã' THEN 70
        ELSE ROUND(30 + (populacao / 8000), 0)
    END as score_logistica,
    -- IAEM Score (média ponderada)
    0, -- será calculado abaixo
    '', -- classificação
    0, 0, 0, -- probabilidades
    vocacao_principal,
    'Estável'
FROM dev_eco_municipios;

-- Calcular IAEM score ponderado
-- Pesos: Pix 25%, Empresas 20%, Emprego 20%, Uso Solo 15%, Exportação 10%, Logística 10%
SET SQL_SAFE_UPDATES = 0;
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

-- ============================================================
-- DADOS INICIAIS - Encadeamentos Produtivos Latentes
-- Oportunidades reais identificadas em MS
-- ============================================================
INSERT INTO dev_eco_encadeamento_latente (municipio_id, materia_prima, producao_atual_ton, valor_producao_atual, industria_ausente, cnae_potencial, demanda_estimada_ton, importacao_regional, gap_valor, empregos_potenciais, investimento_estimado, impacto_pib_estimado, payback_estimado_anos, viabilidade, prioridade) VALUES
-- Três Lagoas: celulose → papel tissue, embalagens
((SELECT id FROM dev_eco_municipios WHERE nome='Três Lagoas'), 'Celulose', 7500000, 28000000000, 'Fábrica de Papel Tissue/Embalagens', '17.21', 500000, 2800000000, 3500000000, 850, 450000000, 890000000, 3.5, 'Alta', 'Alta'),
-- Dourados: soja → esmagadora/biodiesel
((SELECT id FROM dev_eco_municipios WHERE nome='Dourados'), 'Soja em Grão', 3200000, 8500000000, 'Esmagadora de Soja / Biodiesel', '10.41', 1500000, 4200000000, 5800000000, 420, 380000000, 720000000, 4.0, 'Alta', 'Crítica'),
-- Bonito: frutas regionais → indústria de polpas/sucos
((SELECT id FROM dev_eco_municipios WHERE nome='Bonito'), 'Frutas Regionais (Guavira, Bocaiuva)', 8500, 25000000, 'Indústria de Polpas e Sucos Nativos', '10.33', 15000, 85000000, 120000000, 180, 15000000, 45000000, 2.5, 'Alta', 'Alta'),
-- Maracaju: milho → ração animal / etanol de milho
((SELECT id FROM dev_eco_municipios WHERE nome='Maracaju'), 'Milho 2ª Safra', 2800000, 4200000000, 'Fábrica de Ração Animal Premium', '10.66', 800000, 1200000000, 1800000000, 320, 120000000, 380000000, 3.0, 'Alta', 'Alta'),
-- Corumbá: minério de ferro → pelotização
((SELECT id FROM dev_eco_municipios WHERE nome='Corumbá'), 'Minério de Ferro', 5000000, 12000000000, 'Usina de Pelotização', '07.10', 3000000, 8500000000, 6500000000, 600, 850000000, 1200000000, 5.0, 'Média', 'Alta'),
-- Sidrolândia: frango → processados de frango
((SELECT id FROM dev_eco_municipios WHERE nome='Sidrolândia'), 'Frango Abatido', 450000, 3200000000, 'Fábrica de Empanados/Processados', '10.12', 200000, 1500000000, 2100000000, 550, 180000000, 420000000, 3.0, 'Alta', 'Crítica'),
-- Aquidauana: leite → laticínio de queijos especiais
((SELECT id FROM dev_eco_municipios WHERE nome='Aquidauana'), 'Leite in natura', 85000, 280000000, 'Laticínio de Queijos Artesanais/Especiais', '10.52', 120000, 450000000, 380000000, 150, 25000000, 85000000, 2.0, 'Alta', 'Alta'),
-- Naviraí: mandioca → fécula/amido
((SELECT id FROM dev_eco_municipios WHERE nome='Naviraí'), 'Mandioca', 320000, 180000000, 'Fecularia / Amido Modificado', '10.63', 250000, 520000000, 450000000, 220, 45000000, 120000000, 2.5, 'Alta', 'Média'),
-- Campo Grande: serviços → hub de tecnologia
((SELECT id FROM dev_eco_municipios WHERE nome='Campo Grande'), 'Mão de obra qualificada TI', 0, 0, 'Data Center / Hub de Cloud Computing', '63.11', 0, 2500000000, 3200000000, 1200, 250000000, 580000000, 3.5, 'Alta', 'Crítica'),
-- Ponta Porã: comércio fronteira → zona franca de processamento
((SELECT id FROM dev_eco_municipios WHERE nome='Ponta Porã'), 'Fluxo Comercial Fronteira', 0, 3500000000, 'Zona de Processamento de Exportação', '52.11', 0, 1800000000, 2500000000, 800, 200000000, 450000000, 3.0, 'Média', 'Alta'),
-- Rio Brilhante: cana → biogás/biometano
((SELECT id FROM dev_eco_municipios WHERE nome='Rio Brilhante'), 'Vinhaça e Palha de Cana', 2500000, 0, 'Usina de Biogás/Biometano', '35.21', 0, 350000000, 480000000, 120, 85000000, 180000000, 4.0, 'Alta', 'Alta'),
-- Costa Rica: algodão → fiação/tecelagem
((SELECT id FROM dev_eco_municipios WHERE nome='Costa Rica'), 'Algodão em Pluma', 180000, 2800000000, 'Fiação e Tecelagem Básica', '13.11', 120000, 1500000000, 1800000000, 450, 150000000, 320000000, 3.5, 'Média', 'Média');

-- ============================================================
-- Verificação
-- ============================================================
SELECT '=== MÓDULOS PREMIUM ===' as info;
SELECT 'IAEM calculados' as modulo, COUNT(*) as registros FROM dev_eco_iaem;
SELECT 'Encadeamentos latentes' as modulo, COUNT(*) as registros FROM dev_eco_encadeamento_latente;
SELECT 'Multiplicadores setoriais' as modulo, COUNT(*) as registros FROM dev_eco_multiplicadores;

SELECT '=== TOP 10 IAEM ===' as info;
SELECT m.nome, i.iaem_score, i.iaem_classificacao, i.prob_crescimento_6m, i.setor_destaque, i.tendencia
FROM dev_eco_iaem i JOIN dev_eco_municipios m ON i.municipio_id = m.id
ORDER BY i.iaem_score DESC LIMIT 10;
