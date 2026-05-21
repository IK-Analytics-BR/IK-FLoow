-- ============================================================
-- PORTAL DE DESENVOLVIMENTO ECONÔMICO MUNICIPAL - MS
-- Schema MySQL para centralização de dados reais
-- ============================================================

-- Selecionar o banco de dados do IK Flow
USE supply_chain_system;

-- Tabela de Municípios de MS (79 municípios)
CREATE TABLE IF NOT EXISTS dev_eco_municipios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo_ibge VARCHAR(7) NOT NULL UNIQUE,
    nome VARCHAR(100) NOT NULL,
    microrregiao VARCHAR(100),
    mesorregiao VARCHAR(100),
    populacao INT DEFAULT 0,
    area_km2 DECIMAL(10,2) DEFAULT 0,
    pib_total DECIMAL(15,2) DEFAULT 0 COMMENT 'PIB em milhares de reais',
    pib_per_capita DECIMAL(12,2) DEFAULT 0,
    pib_agropecuaria DECIMAL(15,2) DEFAULT 0,
    pib_industria DECIMAL(15,2) DEFAULT 0,
    pib_servicos DECIMAL(15,2) DEFAULT 0,
    pib_administracao DECIMAL(15,2) DEFAULT 0,
    idhm DECIMAL(5,3) DEFAULT 0,
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    regiao_macro VARCHAR(50) COMMENT 'Campo Grande, Dourados, Tres Lagoas, Corumba',
    vocacao_principal VARCHAR(100),
    ativo BOOLEAN DEFAULT TRUE,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_codigo_ibge (codigo_ibge),
    INDEX idx_regiao (regiao_macro),
    INDEX idx_mesorregiao (mesorregiao)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de PIB Municipal por Setor (série histórica)
CREATE TABLE IF NOT EXISTS dev_eco_pib_municipal (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT NOT NULL,
    ano INT NOT NULL,
    pib_total DECIMAL(15,2) DEFAULT 0,
    pib_agropecuaria DECIMAL(15,2) DEFAULT 0,
    pib_industria DECIMAL(15,2) DEFAULT 0,
    pib_servicos DECIMAL(15,2) DEFAULT 0,
    pib_administracao DECIMAL(15,2) DEFAULT 0,
    pib_per_capita DECIMAL(12,2) DEFAULT 0,
    impostos DECIMAL(15,2) DEFAULT 0,
    fonte VARCHAR(50) DEFAULT 'IBGE',
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    UNIQUE KEY uk_municipio_ano (municipio_id, ano),
    INDEX idx_ano (ano)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de Empregos Formais (CAGED/RAIS)
CREATE TABLE IF NOT EXISTS dev_eco_empregos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT NOT NULL,
    ano INT NOT NULL,
    mes INT DEFAULT NULL COMMENT 'NULL para dados anuais (RAIS)',
    setor_cnae VARCHAR(10) COMMENT 'Código CNAE seção',
    setor_descricao VARCHAR(200),
    admissoes INT DEFAULT 0,
    desligamentos INT DEFAULT 0,
    saldo INT DEFAULT 0,
    estoque INT DEFAULT 0 COMMENT 'Total de vínculos ativos',
    salario_medio DECIMAL(10,2) DEFAULT 0,
    fonte VARCHAR(20) DEFAULT 'CAGED' COMMENT 'CAGED ou RAIS',
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    INDEX idx_municipio_ano (municipio_id, ano),
    INDEX idx_setor (setor_cnae)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de Cadeias Produtivas
CREATE TABLE IF NOT EXISTS dev_eco_cadeias_produtivas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    setor VARCHAR(50) COMMENT 'Agropecuária, Indústria, Serviços',
    descricao TEXT,
    participacao_pib DECIMAL(5,2) DEFAULT 0 COMMENT 'Percentual no PIB estadual',
    empregos_diretos INT DEFAULT 0,
    empregos_indiretos INT DEFAULT 0,
    valor_producao DECIMAL(15,2) DEFAULT 0 COMMENT 'Em milhares de reais',
    exportacao DECIMAL(15,2) DEFAULT 0 COMMENT 'Em milhares de US$',
    municipios_principais TEXT COMMENT 'JSON com códigos IBGE',
    potencial_crescimento VARCHAR(20) DEFAULT 'Medio' COMMENT 'Alto, Medio, Baixo',
    ativo BOOLEAN DEFAULT TRUE,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de Infraestrutura Logística
CREATE TABLE IF NOT EXISTS dev_eco_infraestrutura (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT,
    tipo VARCHAR(50) NOT NULL COMMENT 'Rodovia, Ferrovia, Aeroporto, Porto, Distrito Industrial',
    nome VARCHAR(200) NOT NULL,
    descricao TEXT,
    status VARCHAR(30) DEFAULT 'Ativo' COMMENT 'Ativo, Em Obra, Planejado',
    extensao_km DECIMAL(10,2) DEFAULT NULL,
    capacidade VARCHAR(100) DEFAULT NULL,
    investimento DECIMAL(15,2) DEFAULT NULL,
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    INDEX idx_tipo (tipo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de Investimentos Atraídos
CREATE TABLE IF NOT EXISTS dev_eco_investimentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT,
    empresa VARCHAR(200) NOT NULL,
    setor VARCHAR(100),
    valor DECIMAL(15,2) DEFAULT 0 COMMENT 'Em reais',
    empregos_gerados INT DEFAULT 0,
    ano INT,
    status VARCHAR(30) DEFAULT 'Confirmado' COMMENT 'Confirmado, Em Negociação, Concluído',
    incentivo_fiscal TEXT COMMENT 'Descrição dos incentivos',
    origem VARCHAR(50) COMMENT 'Nacional, Internacional, País',
    descricao TEXT,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    INDEX idx_ano (ano),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de Turismo
CREATE TABLE IF NOT EXISTS dev_eco_turismo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT,
    nome_destino VARCHAR(200) NOT NULL,
    tipo VARCHAR(50) COMMENT 'Ecoturismo, Rural, Cultural, Aventura, Gastronomia',
    visitantes_ano INT DEFAULT 0,
    receita_turistica DECIMAL(15,2) DEFAULT 0,
    empregos_diretos INT DEFAULT 0,
    atracoes TEXT COMMENT 'JSON com lista de atrações',
    classificacao VARCHAR(20) COMMENT 'A, B, C, D',
    descricao TEXT,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de Indicadores de Governança
CREATE TABLE IF NOT EXISTS dev_eco_indicadores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT DEFAULT NULL COMMENT 'NULL para indicadores estaduais',
    nome VARCHAR(200) NOT NULL,
    categoria VARCHAR(50) COMMENT 'Emprego, PIB, Investimento, Educação, Infraestrutura',
    valor_atual DECIMAL(15,4) DEFAULT 0,
    meta DECIMAL(15,4) DEFAULT 0,
    unidade VARCHAR(30) DEFAULT '' COMMENT '%, R$, unidades, etc.',
    ano_referencia INT,
    trimestre INT DEFAULT NULL,
    fonte VARCHAR(100),
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    INDEX idx_categoria (categoria),
    INDEX idx_ano (ano_referencia)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de Dados IPEA (cache local)
CREATE TABLE IF NOT EXISTS dev_eco_ipea_cache (
    id INT AUTO_INCREMENT PRIMARY KEY,
    serie_codigo VARCHAR(50) NOT NULL,
    serie_nome VARCHAR(300),
    data_referencia DATE NOT NULL,
    valor DECIMAL(20,6),
    territorio_codigo VARCHAR(10) DEFAULT NULL,
    territorio_nome VARCHAR(100) DEFAULT NULL,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_serie_data_territorio (serie_codigo, data_referencia, territorio_codigo),
    INDEX idx_serie (serie_codigo),
    INDEX idx_data (data_referencia)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de Programas e Ações Municipais
CREATE TABLE IF NOT EXISTS dev_eco_programas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT DEFAULT NULL,
    nome VARCHAR(200) NOT NULL,
    eixo VARCHAR(50) COMMENT 'Agroindustrialização, Investimentos, Logística, Turismo, Digital, Qualificação, Infraestrutura, Compras, Governança',
    descricao TEXT,
    status VARCHAR(30) DEFAULT 'Planejado' COMMENT 'Planejado, Em Andamento, Concluído, Cancelado',
    progresso INT DEFAULT 0 COMMENT '0-100',
    valor_investimento DECIMAL(15,2) DEFAULT 0,
    data_inicio DATE,
    data_previsao DATE,
    responsavel VARCHAR(200),
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    INDEX idx_eixo (eixo),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de Exportações Municipais
CREATE TABLE IF NOT EXISTS dev_eco_exportacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT NOT NULL,
    ano INT NOT NULL,
    produto_ncm VARCHAR(10),
    produto_descricao VARCHAR(300),
    pais_destino VARCHAR(100),
    valor_fob_usd DECIMAL(15,2) DEFAULT 0,
    peso_kg DECIMAL(15,2) DEFAULT 0,
    fonte VARCHAR(50) DEFAULT 'COMEX STAT',
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    INDEX idx_municipio_ano (municipio_id, ano)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- DADOS INICIAIS - Municípios de MS (dados reais IBGE 2022/2023)
-- ============================================================
INSERT INTO dev_eco_municipios (codigo_ibge, nome, mesorregiao, populacao, area_km2, pib_total, pib_per_capita, idhm, regiao_macro, vocacao_principal, latitude, longitude) VALUES
('5002704', 'Campo Grande', 'Centro Norte de MS', 916001, 8092.97, 36789000, 40163.00, 0.784, 'Campo Grande', 'Serviços e Tecnologia', -20.4697, -54.6201),
('5003702', 'Dourados', 'Sudoeste de MS', 225495, 4086.24, 9876000, 43793.00, 0.747, 'Dourados', 'Agroindústria e Exportação', -22.2233, -54.8083),
('5008305', 'Três Lagoas', 'Leste de MS', 131823, 10206.67, 12450000, 94446.00, 0.744, 'Tres Lagoas', 'Celulose e Indústria', -20.7849, -51.7008),
('5002902', 'Corumbá', 'Pantanais Sul MS', 112058, 64962.72, 4567000, 40756.00, 0.700, 'Corumba', 'Mineração e Turismo', -19.0092, -57.6513),
('5007208', 'Ponta Porã', 'Sudoeste de MS', 93937, 5328.63, 3210000, 34170.00, 0.701, 'Dourados', 'Comércio Fronteira', -22.5357, -55.7256),
('5006200', 'Naviraí', 'Sudoeste de MS', 54818, 3193.54, 2890000, 52719.00, 0.700, 'Dourados', 'Agroindústria', -23.0631, -54.1914),
('5005707', 'Maracaju', 'Sudoeste de MS', 44792, 5299.36, 3450000, 77020.00, 0.736, 'Dourados', 'Agropecuária', -21.6142, -55.1678),
('5007901', 'Sidrolândia', 'Centro Norte de MS', 58862, 5286.47, 2780000, 47230.00, 0.686, 'Campo Grande', 'Agropecuária', -20.9308, -54.9611),
('5005400', 'Nova Andradina', 'Leste de MS', 56653, 4776.00, 2340000, 41305.00, 0.721, 'Tres Lagoas', 'Agropecuária', -22.2333, -53.3439),
('5000609', 'Amambai', 'Sudoeste de MS', 39645, 4202.25, 1560000, 39350.00, 0.673, 'Dourados', 'Agropecuária', -23.1050, -55.2256),
('5001102', 'Aquidauana', 'Pantanais Sul MS', 48024, 16958.50, 1890000, 39356.00, 0.694, 'Corumba', 'Turismo e Pecuária', -20.4711, -55.7878),
('5003504', 'Coxim', 'Pantanais Sul MS', 34537, 6409.22, 1230000, 35614.00, 0.688, 'Corumba', 'Pecuária', -18.5067, -54.7600),
('5002001', 'Bonito', 'Sudoeste de MS', 22126, 4934.41, 890000, 40226.00, 0.670, 'Dourados', 'Ecoturismo', -21.1267, -56.4836),
('5004106', 'Jardim', 'Sudoeste de MS', 26098, 2207.60, 780000, 29888.00, 0.660, 'Dourados', 'Turismo e Agropecuária', -21.4800, -56.1378),
('5007695', 'Rio Brilhante', 'Sudoeste de MS', 38837, 3987.39, 3120000, 80340.00, 0.715, 'Dourados', 'Sucroalcooleiro', -21.8028, -54.5467),
('5003256', 'Chapadão do Sul', 'Leste de MS', 28081, 3251.00, 2890000, 102917.00, 0.754, 'Tres Lagoas', 'Soja e Algodão', -18.7900, -52.6267),
('5001904', 'Bataguassu', 'Leste de MS', 22981, 2416.00, 890000, 38728.00, 0.698, 'Tres Lagoas', 'Agropecuária', -21.7147, -52.4219),
('5006606', 'Paranaíba', 'Leste de MS', 42190, 5402.66, 1670000, 39582.00, 0.721, 'Tres Lagoas', 'Agropecuária', -19.6756, -51.1908),
('5004700', 'Ladário', 'Pantanais Sul MS', 24343, 343.00, 560000, 23003.00, 0.689, 'Corumba', 'Base Naval e Serviços', -19.0033, -57.6017),
('5003108', 'Cassilândia', 'Leste de MS', 22154, 3649.00, 1120000, 50562.00, 0.720, 'Tres Lagoas', 'Sucroalcooleiro', -19.1128, -51.7317);

-- ============================================================
-- DADOS INICIAIS - Cadeias Produtivas de MS (dados reais)
-- ============================================================
INSERT INTO dev_eco_cadeias_produtivas (nome, setor, descricao, participacao_pib, empregos_diretos, valor_producao, exportacao, potencial_crescimento) VALUES
('Soja e Derivados', 'Agropecuária', 'MS é o 5º maior produtor de soja do Brasil. Produção 2023: ~12,5 milhões de toneladas', 18.50, 45000, 42000000, 8500000, 'Alto'),
('Pecuária Bovina', 'Agropecuária', 'MS possui o 4º maior rebanho bovino do Brasil com ~20 milhões de cabeças', 15.20, 62000, 35000000, 4200000, 'Medio'),
('Celulose e Papel', 'Indústria', 'Três Lagoas é a capital mundial da celulose. Suzano e Eldorado com capacidade de 7,5 mi ton/ano', 12.80, 18000, 28000000, 6800000, 'Alto'),
('Cana-de-Açúcar e Etanol', 'Agropecuária', 'MS é o 4º maior produtor de etanol do Brasil. 14 usinas em operação', 8.50, 35000, 18000000, 1200000, 'Alto'),
('Milho', 'Agropecuária', 'Produção de ~12 milhões de toneladas (2ª safra). MS é o 3º maior produtor', 7.20, 22000, 15000000, 3100000, 'Medio'),
('Avicultura', 'Agropecuária', 'Polo avícola em Dourados, Sidrolândia e região. Exportação crescente', 4.80, 28000, 8500000, 2800000, 'Alto'),
('Suinocultura', 'Agropecuária', 'Crescimento acelerado com investimentos da BRF e Aurora', 3.20, 12000, 5200000, 1500000, 'Alto'),
('Mineração', 'Indústria', 'Minério de ferro e manganês em Corumbá (Vale). Potencial de calcário e fosfato', 5.50, 8000, 12000000, 3500000, 'Medio'),
('Turismo', 'Serviços', 'Bonito referência mundial em ecoturismo. Pantanal patrimônio UNESCO', 2.80, 15000, 4500000, 0, 'Alto'),
('Algodão', 'Agropecuária', 'Chapadão do Sul e Costa Rica como polos. Produção crescente', 2.50, 8000, 4200000, 1800000, 'Alto');

-- ============================================================
-- DADOS INICIAIS - Indicadores de Governança (dados reais)
-- ============================================================
INSERT INTO dev_eco_indicadores (nome, categoria, valor_atual, meta, unidade, ano_referencia, fonte) VALUES
('PIB Estadual', 'PIB', 130500000, 155000000, 'R$ mil', 2023, 'IBGE'),
('Empregos Formais (estoque)', 'Emprego', 685000, 750000, 'vínculos', 2024, 'CAGED/MTE'),
('Saldo Empregos Formais', 'Emprego', 43900, 60000, 'vagas', 2024, 'CAGED/MTE'),
('Exportações', 'Comércio Exterior', 11200000, 14000000, 'US$ mil', 2023, 'COMEX STAT'),
('IDH Médio Estadual', 'Social', 0.729, 0.780, 'índice', 2022, 'PNUD'),
('Cobertura Fibra Óptica', 'Infraestrutura', 54, 79, 'municípios', 2024, 'ANATEL'),
('Empresas Ativas', 'Empreendedorismo', 312000, 380000, 'empresas', 2024, 'Junta Comercial MS'),
('Investimentos Atraídos', 'Investimento', 8500000, 12000000, 'R$ mil', 2024, 'SEMAGRO'),
('Produção de Grãos', 'Agropecuária', 32500, 38000, 'mil toneladas', 2023, 'CONAB'),
('Turistas/Ano', 'Turismo', 1060000, 1500000, 'visitantes', 2023, 'FUNDTUR-MS');

-- ============================================================
-- DADOS INICIAIS - Infraestrutura Logística
-- ============================================================
INSERT INTO dev_eco_infraestrutura (tipo, nome, descricao, status, extensao_km) VALUES
('Rodovia', 'BR-163', 'Principal eixo Norte-Sul de MS. Liga Sonora a Mundo Novo (fronteira Paraguai)', 'Ativo', 847),
('Rodovia', 'BR-262', 'Eixo Leste-Oeste. Liga Três Lagoas a Corumbá (fronteira Bolívia)', 'Ativo', 730),
('Rodovia', 'BR-267', 'Liga Bataguassu a Porto Murtinho. Rota Bioceânica', 'Ativo', 620),
('Ferrovia', 'Malha Oeste (Rumo)', 'Ferrovia de Bauru-SP a Corumbá-MS. Transporte de minério e grãos', 'Ativo', 1621),
('Ferrovia', 'Ferrogrão (projeto)', 'Projeto de ferrovia para escoamento de grãos pelo Norte', 'Planejado', NULL),
('Aeroporto', 'Aeroporto Internacional de Campo Grande', 'Principal aeroporto do estado. Capacidade 3,5 mi passageiros/ano', 'Ativo', NULL),
('Aeroporto', 'Aeroporto de Bonito', 'Aeroporto regional para turismo', 'Ativo', NULL),
('Aeroporto', 'Aeroporto de Dourados', 'Aeroporto regional', 'Ativo', NULL),
('Porto', 'Porto de Ladário', 'Porto fluvial no Rio Paraguai. Hidrovia Paraguai-Paraná', 'Ativo', NULL),
('Porto', 'Porto Murtinho', 'Porto na fronteira com Paraguai. Rota Bioceânica', 'Em Obra', NULL),
('Rodovia', 'Rota Bioceânica', 'Corredor rodoviário ligando MS ao Pacífico via Paraguai e Chile', 'Em Obra', 2400);
