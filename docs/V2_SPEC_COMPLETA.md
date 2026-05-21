# Portal de Desenvolvimento Econômico Municipal — MS
# ESPECIFICAÇÃO COMPLETA V2 (para recriar do zero)

> **Objetivo deste documento:** Contém TUDO que é necessário para recriar o módulo de Desenvolvimento Econômico Municipal de Mato Grosso do Sul em outra máquina, usando Windsurf/Cascade. Cole este documento como prompt inicial e siga as instruções.

---

## 1. VISÃO GERAL DO PROJETO

### O que é
Portal web (Flask + MySQL + Jinja2) que centraliza dados econômicos dos **79 municípios de Mato Grosso do Sul**, incluindo:
- Dashboard interativo com mapa e gráficos (estilo Tableau)
- 10 abas temáticas (Diagnóstico, Agroindústria, Investimentos, Logística, Turismo, Inovação, Qualificação, Infraestrutura, Compras, Governança)
- **IAEM** — Índice de Antecipação Econômica Municipal (nowcasting com 6 componentes ponderados)
- **Gaps** — Mapa de Encadeamentos Produtivos Latentes (oportunidades industriais)
- **Simulador** de Impacto Econômico (multiplicadores de Leontief)
- Página de Metodologia explicando IAEM e Gaps
- Filtro global por município (propaga entre abas, mostra município + 4 vizinhos geográficos)

### Stack tecnológico
- **Backend:** Python 3.10+, Flask 2.2.5, mysql-connector-python 8.0.33
- **Frontend:** Jinja2 templates, Bootstrap 5, Chart.js, Leaflet.js (mapa)
- **Banco:** MySQL 8.0 (database: `supply_chain_system`)
- **Autenticação:** Session-based (Flask session)

### Dados
- **Municípios:** 79 municípios com dados reais do IBGE (Censo 2022, PIB Municipal 2021, IBGE Cidades 2022/2023)
- **IAEM:** Scores calculados via proxies (PIB per capita, população, PIB setorial) — em roadmap para dados reais
- **Gaps:** Encadeamentos gerados por fórmula baseada em vocação econômica + dados manuais para 11 municípios-chave
- **Cadeias produtivas:** 10 cadeias com dados reais (CONAB, IBGE, SEMAGRO)
- **Infraestrutura:** Rodovias, ferrovias, aeroportos, portos reais
- **Indicadores estaduais:** Dados reais (IBGE, CAGED, Comex Stat)

---

## 2. ESTRUTURA DE ARQUIVOS

```
SupplyChainSystem/
├── run.py                          # Entry point (python run.py)
├── config.py                       # Config base
├── requirements.txt                # Dependências Python
├── app/
│   ├── main_mysql.py               # App Flask principal (registra blueprints)
│   ├── auto_config.py              # Detecção automática local/produção
│   ├── config_local.py             # Config MySQL local
│   ├── config_production.py        # Config MySQL produção (AWS)
│   ├── db_config.py                # Módulo centralizado de conexão DB
│   ├── user_loader.py              # Carregamento de usuário
│   ├── routes/
│   │   └── dev_economico_routes.py # *** ARQUIVO PRINCIPAL — 840 linhas ***
│   ├── templates/
│   │   ├── base.html               # Template base do sistema
│   │   └── dev_economico/          # *** 18 templates do portal ***
│   │       ├── _filtro_banner.html
│   │       ├── _nav.html
│   │       ├── dashboard_dinamico.html
│   │       ├── diagnostico.html
│   │       ├── agroindustria.html
│   │       ├── investimentos.html
│   │       ├── logistica.html
│   │       ├── turismo.html
│   │       ├── inovacao.html
│   │       ├── qualificacao.html
│   │       ├── infraestrutura.html
│   │       ├── compras.html
│   │       ├── governanca.html
│   │       ├── iaem.html
│   │       ├── encadeamento.html
│   │       ├── simulador.html
│   │       ├── metodologia.html
│   │       └── dashboard.html (legado)
│   └── static/                     # CSS, JS, imagens
├── sql/
│   ├── dev_economico_schema.sql           # Schema base (municipios, empregos, cadeias, etc.)
│   ├── dev_economico_79_municipios.sql    # INSERT dos 79 municípios (dados IBGE reais)
│   ├── dev_economico_municipios_completos.sql  # Versão completa com PIB setorial
│   ├── dev_economico_premium.sql          # Schema + dados IAEM, Gaps, Simulador
│   ├── fix_iaem_v2.sql                    # Recálculo IAEM com proxies
│   ├── fix_encadeamentos_todos.sql        # Gera Gaps para todos os 79 municípios
│   └── fix_encadeamentos.sql              # Gaps manuais para municípios-chave
└── docs/
    ├── ROADMAP_PRODUCAO.md                # Roadmap para dados reais
    └── V2_SPEC_COMPLETA.md                # Este documento
```

---

## 3. BANCO DE DADOS — SCHEMA COMPLETO

### 3.1 Tabelas base (dev_economico_schema.sql)

```sql
-- Tabela principal: 79 municípios de MS
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

-- PIB Municipal por Setor (série histórica)
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

-- Empregos Formais (CAGED/RAIS)
CREATE TABLE IF NOT EXISTS dev_eco_empregos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT NOT NULL,
    ano INT NOT NULL,
    mes INT DEFAULT NULL,
    setor_cnae VARCHAR(10),
    setor_descricao VARCHAR(200),
    admissoes INT DEFAULT 0,
    desligamentos INT DEFAULT 0,
    saldo INT DEFAULT 0,
    estoque INT DEFAULT 0,
    salario_medio DECIMAL(10,2) DEFAULT 0,
    fonte VARCHAR(20) DEFAULT 'CAGED',
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    INDEX idx_municipio_ano (municipio_id, ano),
    INDEX idx_setor (setor_cnae)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Cadeias Produtivas
CREATE TABLE IF NOT EXISTS dev_eco_cadeias_produtivas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    setor VARCHAR(50),
    descricao TEXT,
    participacao_pib DECIMAL(5,2) DEFAULT 0,
    empregos_diretos INT DEFAULT 0,
    empregos_indiretos INT DEFAULT 0,
    valor_producao DECIMAL(15,2) DEFAULT 0,
    exportacao DECIMAL(15,2) DEFAULT 0,
    municipios_principais TEXT,
    potencial_crescimento VARCHAR(20) DEFAULT 'Medio',
    ativo BOOLEAN DEFAULT TRUE,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Infraestrutura Logística
CREATE TABLE IF NOT EXISTS dev_eco_infraestrutura (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT,
    tipo VARCHAR(50) NOT NULL COMMENT 'Rodovia, Ferrovia, Aeroporto, Porto, Distrito Industrial',
    nome VARCHAR(200) NOT NULL,
    descricao TEXT,
    status VARCHAR(30) DEFAULT 'Ativo',
    extensao_km DECIMAL(10,2) DEFAULT NULL,
    capacidade VARCHAR(100) DEFAULT NULL,
    investimento DECIMAL(15,2) DEFAULT NULL,
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    INDEX idx_tipo (tipo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Investimentos Atraídos
CREATE TABLE IF NOT EXISTS dev_eco_investimentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT,
    empresa VARCHAR(200) NOT NULL,
    setor VARCHAR(100),
    valor DECIMAL(15,2) DEFAULT 0,
    empregos_gerados INT DEFAULT 0,
    ano INT,
    status VARCHAR(30) DEFAULT 'Confirmado',
    incentivo_fiscal TEXT,
    origem VARCHAR(50),
    descricao TEXT,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    INDEX idx_ano (ano),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Turismo
CREATE TABLE IF NOT EXISTS dev_eco_turismo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT,
    nome_destino VARCHAR(200) NOT NULL,
    tipo VARCHAR(50),
    visitantes_ano INT DEFAULT 0,
    receita_turistica DECIMAL(15,2) DEFAULT 0,
    empregos_diretos INT DEFAULT 0,
    atracoes TEXT,
    classificacao VARCHAR(20),
    descricao TEXT,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Indicadores de Governança
CREATE TABLE IF NOT EXISTS dev_eco_indicadores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT DEFAULT NULL,
    nome VARCHAR(200) NOT NULL,
    categoria VARCHAR(50),
    valor_atual DECIMAL(15,4) DEFAULT 0,
    meta DECIMAL(15,4) DEFAULT 0,
    unidade VARCHAR(30) DEFAULT '',
    ano_referencia INT,
    trimestre INT DEFAULT NULL,
    fonte VARCHAR(100),
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    INDEX idx_categoria (categoria),
    INDEX idx_ano (ano_referencia)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Programas e Ações Municipais
CREATE TABLE IF NOT EXISTS dev_eco_programas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT DEFAULT NULL,
    nome VARCHAR(200) NOT NULL,
    eixo VARCHAR(50) COMMENT 'Agroindustrialização, Investimentos, Logística, Turismo, Digital, Qualificação, Infraestrutura, Compras, Governança',
    descricao TEXT,
    status VARCHAR(30) DEFAULT 'Planejado',
    progresso INT DEFAULT 0,
    valor_investimento DECIMAL(15,2) DEFAULT 0,
    data_inicio DATE,
    data_previsao DATE,
    responsavel VARCHAR(200),
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    INDEX idx_eixo (eixo),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Exportações Municipais
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

-- Cache IPEA
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
```

### 3.2 Tabelas Premium (dev_economico_premium.sql)

```sql
-- Dados de fluxo Pix por município
CREATE TABLE IF NOT EXISTS dev_eco_pix_fluxo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT NOT NULL,
    ano_mes VARCHAR(7) NOT NULL COMMENT 'YYYY-MM',
    volume_pj_recebido DECIMAL(18,2) DEFAULT 0,
    volume_pj_enviado DECIMAL(18,2) DEFAULT 0,
    volume_pf_recebido DECIMAL(18,2) DEFAULT 0,
    volume_pf_enviado DECIMAL(18,2) DEFAULT 0,
    qtd_transacoes_pj INT DEFAULT 0,
    qtd_transacoes_pf INT DEFAULT 0,
    ticket_medio_pj DECIMAL(12,2) DEFAULT 0,
    variacao_mensal DECIMAL(8,4) DEFAULT 0,
    variacao_anual DECIMAL(8,4) DEFAULT 0,
    fonte VARCHAR(50) DEFAULT 'BCB',
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    UNIQUE KEY uk_mun_mes (municipio_id, ano_mes),
    INDEX idx_ano_mes (ano_mes)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Abertura/Fechamento de empresas
CREATE TABLE IF NOT EXISTS dev_eco_empresas_dinamica (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT NOT NULL,
    ano_mes VARCHAR(7) NOT NULL,
    cnae_secao VARCHAR(5),
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

-- Uso do solo (MapBiomas)
CREATE TABLE IF NOT EXISTS dev_eco_uso_solo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT NOT NULL,
    ano INT NOT NULL,
    classe VARCHAR(80) NOT NULL,
    area_hectares DECIMAL(12,2) DEFAULT 0,
    percentual_territorio DECIMAL(6,3) DEFAULT 0,
    variacao_anual_ha DECIMAL(12,2) DEFAULT 0,
    variacao_anual_pct DECIMAL(8,4) DEFAULT 0,
    fonte VARCHAR(50) DEFAULT 'MapBiomas',
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    UNIQUE KEY uk_mun_ano_classe (municipio_id, ano, classe),
    INDEX idx_classe (classe)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Emprego mensal (CAGED)
CREATE TABLE IF NOT EXISTS dev_eco_emprego_mensal (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT NOT NULL,
    ano_mes VARCHAR(7) NOT NULL,
    setor_ibge VARCHAR(5),
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

-- IAEM calculado
CREATE TABLE IF NOT EXISTS dev_eco_iaem (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT NOT NULL,
    data_calculo DATE NOT NULL,
    score_pix DECIMAL(6,2) DEFAULT 0,
    score_empresas DECIMAL(6,2) DEFAULT 0,
    score_emprego DECIMAL(6,2) DEFAULT 0,
    score_uso_solo DECIMAL(6,2) DEFAULT 0,
    score_exportacao DECIMAL(6,2) DEFAULT 0,
    score_logistica DECIMAL(6,2) DEFAULT 0,
    iaem_score DECIMAL(6,2) DEFAULT 0,
    iaem_classificacao VARCHAR(30),
    prob_crescimento_6m DECIMAL(6,2) DEFAULT 0,
    prob_crescimento_12m DECIMAL(6,2) DEFAULT 0,
    prob_crescimento_24m DECIMAL(6,2) DEFAULT 0,
    setor_destaque VARCHAR(100),
    tendencia VARCHAR(20),
    observacoes TEXT,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    UNIQUE KEY uk_mun_data (municipio_id, data_calculo),
    INDEX idx_score (iaem_score DESC),
    INDEX idx_classificacao (iaem_classificacao)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Encadeamentos Produtivos Latentes (Gaps)
CREATE TABLE IF NOT EXISTS dev_eco_encadeamento_latente (
    id INT AUTO_INCREMENT PRIMARY KEY,
    municipio_id INT NOT NULL,
    materia_prima VARCHAR(200) NOT NULL,
    producao_atual_ton DECIMAL(15,2) DEFAULT 0,
    valor_producao_atual DECIMAL(15,2) DEFAULT 0,
    industria_ausente VARCHAR(200) NOT NULL,
    cnae_potencial VARCHAR(10),
    demanda_estimada_ton DECIMAL(15,2) DEFAULT 0,
    importacao_regional DECIMAL(15,2) DEFAULT 0,
    gap_valor DECIMAL(15,2) DEFAULT 0,
    empregos_potenciais INT DEFAULT 0,
    investimento_estimado DECIMAL(15,2) DEFAULT 0,
    impacto_pib_estimado DECIMAL(15,2) DEFAULT 0,
    payback_estimado_anos DECIMAL(4,1) DEFAULT 0,
    viabilidade VARCHAR(20) DEFAULT 'Média',
    prioridade VARCHAR(20) DEFAULT 'Média',
    status VARCHAR(30) DEFAULT 'Identificado',
    observacoes TEXT,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    INDEX idx_viabilidade (viabilidade),
    INDEX idx_prioridade (prioridade)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Multiplicadores econômicos por setor
CREATE TABLE IF NOT EXISTS dev_eco_multiplicadores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setor VARCHAR(100) NOT NULL,
    cnae_secao VARCHAR(5),
    emprego_direto_por_milhao DECIMAL(8,2) DEFAULT 0,
    multiplicador_emprego DECIMAL(6,3) DEFAULT 1.5,
    multiplicador_pib DECIMAL(6,3) DEFAULT 1.8,
    multiplicador_renda DECIMAL(6,3) DEFAULT 1.4,
    multiplicador_tributo DECIMAL(6,3) DEFAULT 0.25,
    pix_estimado_por_emprego DECIMAL(12,2) DEFAULT 0,
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
    tipo_empreendimento VARCHAR(200) NOT NULL,
    setor VARCHAR(100) NOT NULL,
    investimento_total DECIMAL(15,2) NOT NULL,
    porte VARCHAR(30) DEFAULT 'Médio',
    area_m2 DECIMAL(12,2) DEFAULT 0,
    empregos_diretos INT DEFAULT 0,
    empregos_indiretos INT DEFAULT 0,
    empregos_totais INT DEFAULT 0,
    impacto_pib_anual DECIMAL(15,2) DEFAULT 0,
    impacto_renda_anual DECIMAL(15,2) DEFAULT 0,
    impacto_tributos_anual DECIMAL(15,2) DEFAULT 0,
    impacto_pix_mensal DECIMAL(15,2) DEFAULT 0,
    variacao_pib_municipal DECIMAL(8,4) DEFAULT 0,
    novo_ranking_estadual INT DEFAULT 0,
    ranking_anterior INT DEFAULT 0,
    viabilidade_score DECIMAL(6,2) DEFAULT 0,
    recomendacao TEXT,
    FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
    INDEX idx_municipio (municipio_id),
    INDEX idx_setor (setor)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 4. LÓGICA DE CÁLCULO DO IAEM

### 4.1 Fórmula do IAEM
```
IAEM = score_pix × 0.25 + score_empresas × 0.20 + score_emprego × 0.20 
     + score_uso_solo × 0.15 + score_exportacao × 0.10 + score_logistica × 0.10
```

### 4.2 Scores por componente (proxy atual)
Cada score vai de 0 a 100:

| Componente | Peso | Proxy usado | Lógica |
|---|---|---|---|
| score_pix | 25% | PIB per capita | ≥80k→90, ≥50k→80, ≥30k→70, ≥20k→60, ≥15k→50, else→35 |
| score_empresas | 20% | População | ≥500k→82, ≥100k→75, ≥50k→68, ≥20k→58, ≥10k→48, else→35 |
| score_emprego | 20% | PIB total | ≥10M→85, ≥3M→75, ≥1M→65, ≥500k→55, else→40 |
| score_uso_solo | 15% | PIB agro / PIB total | ≥40%→88, ≥25%→78, ≥15%→65, else→45 |
| score_exportacao | 10% | PIB indústria / PIB total | ≥35%→90, ≥20%→75, ≥10%→60, else→35 |
| score_logistica | 10% | População | ≥200k→82, ≥50k→70, ≥20k→58, else→40 |

Cada score recebe ±4-5 pontos de variação aleatória (RAND) para simular flutuação.

### 4.3 Classificação
| Faixa IAEM | Classificação |
|---|---|
| ≥ 78 | Expansão Forte |
| ≥ 62 | Expansão |
| ≥ 48 | Estável |
| < 48 | Retração |

### 4.4 Probabilidades de crescimento
```sql
prob_crescimento_6m  = LEAST(95, iaem_score × 1.08)
prob_crescimento_12m = LEAST(92, iaem_score × 0.98)
prob_crescimento_24m = LEAST(88, iaem_score × 0.88)
```

### 4.5 Tendência
| Faixa IAEM | Tendência |
|---|---|
| ≥ 70 | Alta |
| ≥ 50 | Estável |
| < 50 | Baixa |

---

## 5. LÓGICA DOS GAPS (Encadeamentos Produtivos Latentes)

### 5.1 Conceito
Gap = matéria-prima local produzida + indústria de transformação ausente = oportunidade de investimento

### 5.2 Geração automática por vocação
Para cada município, gera 2-3 gaps baseados na vocação:

**Municípios agropecuários** (vocação LIKE '%Pecu%', '%Agro%', '%Soja%'):
- Gap: Bovinos/Leite → Frigorífico (PIB agro > 500k) ou Laticínio (> 200k) ou Cooperativa
- CNAE: 10.11, 10.51, 10.99

**Municípios industriais** (PIB indústria > 100k):
- Gap: Matéria-prima industrial → Fábrica de Papel (Celulose), Pelotização (Mineração), Bioplásticos (Cana)
- CNAE: 17.21, 24.11, 20.29

**Municípios de serviços** (PIB serviços > 80k):
- Gap: Turismo → Resort, TI → Data Center, Fronteira → Centro de Distribuição
- CNAE: 55.10, 63.11, 52.11

### 5.3 Dados manuais para 11 municípios-chave
Além dos gaps automáticos, há 11 registros manuais com dados mais detalhados:
- Três Lagoas: Celulose → Papel Tissue (gap R$ 3.5bi)
- Dourados: Soja → Esmagadora/Biodiesel (gap R$ 5.8bi) — PRIORIDADE CRÍTICA
- Bonito: Frutas → Polpas/Sucos (gap R$ 120mi)
- Maracaju: Milho → Ração Premium (gap R$ 1.8bi)
- Corumbá: Minério → Pelotização (gap R$ 6.5bi)
- Sidrolândia: Frango → Processados (gap R$ 2.1bi) — PRIORIDADE CRÍTICA
- Aquidauana: Leite → Queijos Especiais (gap R$ 380mi)
- Naviraí: Mandioca → Fécula/Amido (gap R$ 450mi)
- Campo Grande: TI → Data Center (gap R$ 3.2bi) — PRIORIDADE CRÍTICA
- Ponta Porã: Fronteira → Zona de Processamento (gap R$ 2.5bi)
- Rio Brilhante: Cana → Biogás/Biometano (gap R$ 480mi)
- Costa Rica: Algodão → Fiação/Tecelagem (gap R$ 1.8bi)

---

## 6. ROTAS DO BACKEND (dev_economico_routes.py)

### 6.1 Blueprint
```python
dev_economico_bp = Blueprint('dev_economico', __name__, url_prefix='/dev-economico')
```

### 6.2 Helpers essenciais

**`_nearby_ids(mun_id, limit=4)`** — Retorna o município selecionado + N vizinhos mais próximos por distância euclidiana (lat/lng). Usado em todas as abas quando há filtro de município.

**`query_db(sql, params, fetchone)`** — Executa query MySQL e retorna dicts. Converte Decimal para float automaticamente.

**`load_municipio_filtro()`** — before_request que carrega `g.municipio_id` e `g.municipio_filtrado` da URL para todos os templates.

### 6.3 Rotas de página (todas requerem @login_required)

| Rota | Template | Dados passados |
|---|---|---|
| `/` | dashboard_dinamico.html | municipios_json (todos com IAEM, JSON) |
| `/diagnostico` | diagnostico.html | municipios, pib_setorial, cadeias, top_pib, top_percapita |
| `/agroindustria` | agroindustria.html | cadeias, programas, municipios, encadeamentos |
| `/investimentos` | investimentos.html | investimentos, programas |
| `/logistica` | logistica.html | rodovias, ferrovias, aeroportos, portos, programas |
| `/turismo` | turismo.html | destinos, municipios, programas |
| `/inovacao` | inovacao.html | programas |
| `/qualificacao` | qualificacao.html | programas, empregos |
| `/infraestrutura` | infraestrutura.html | projetos, programas |
| `/compras` | compras.html | programas |
| `/governanca` | governanca.html | indicadores, programas, resumo_eixos |
| `/iaem` | iaem.html | ranking, classificação, médias, totais |
| `/encadeamento` | encadeamento.html | oportunidades, totais |
| `/simulador` | simulador.html | municipios, multiplicadores, simulacoes |
| `/metodologia` | metodologia.html | (nenhum dado dinâmico) |

### 6.4 APIs JSON

| Rota | Auth | Retorno |
|---|---|---|
| `/api/municipios` | login | Lista completa com IAEM |
| `/api/pib-setorial` | login | PIB agregado por setor |
| `/api/cadeias-produtivas` | login | Cadeias produtivas ativas |
| `/api/indicadores` | login | Indicadores de governança |
| `/api/municipio/<id>` | login | Detalhe + empregos + investimentos |
| `/api/ranking` | login | Top 20 por critério (pib, percapita, pop, idhm) |
| `/api/iaem/ranking` | login | Ranking IAEM completo |
| `/api/debug-iaem` | **público** | Todos municípios com IAEM (fallback) |
| `/api/municipios` | login | Lista completa para filtros |
| `/api/municipio/<id>/completo` | **público** | Painel do secretário (município + IAEM + gaps + vizinhos) |
| `/api/oportunidades-estado` | **público** | Top 20 gaps do estado |
| `/api/visao-geral` | login | Dados agregados estaduais |
| `/api/simular` (POST) | login | Salvar simulação |

### 6.5 Comportamento do filtro de município
Quando `municipio_id` está na URL:
1. Carrega dados do município selecionado
2. Busca 4 vizinhos geográficos mais próximos via `_nearby_ids()`
3. Mostra dados do município + vizinhos nas tabelas
4. Destaca o município selecionado com `is_selected` flag (background amarelo + ícone estrela)
5. Títulos mudam para "Município e Região" em vez de "Estado"
6. Gráficos de barras colorem o município selecionado diferente

Para abas sem dados municipais (logística, inovação, infraestrutura, compras, governança):
- Mostra header contextual com nome do município
- Nota "Dados apresentados são de âmbito estadual"

---

## 7. TEMPLATES — PADRÕES E COMPORTAMENTOS

### 7.1 Navegação (_nav.html)
Barra lateral com ícones para todas as 15 abas. Propaga `municipio_id` via query string em todos os links.

### 7.2 Filtro banner (_filtro_banner.html)
Banner no topo mostrando município filtrado com botão para limpar filtro.

### 7.3 Dashboard dinâmico (dashboard_dinamico.html)
- Mapa Leaflet com marcadores dos 79 municípios (cor por classificação IAEM)
- Gráficos Chart.js: PIB setorial (doughnut), distribuição IAEM (bar), top municípios
- Filtros interativos: região, faixa IAEM, busca por nome
- Painel lateral com detalhes ao clicar no município
- Dados carregados via JSON inline (municipios_json)

### 7.4 Padrão de contextualização por município
Cada template que suporta filtro segue o padrão:
```html
{% if municipio_filtrado %}
    <h2>{{ municipio_filtrado.nome }} — [Título da Aba]</h2>
    <!-- KPIs do município -->
    <div class="row">
        <div class="col-md-3"><div class="card">PIB: R$ {{ municipio_filtrado.pib_total|format_number }}</div></div>
        ...
    </div>
{% else %}
    <h2>[Título da Aba] — Mato Grosso do Sul</h2>
    <!-- KPIs estaduais -->
{% endif %}
```

### 7.5 Destaque do município selecionado nas tabelas
```html
<tr class="{% if item.is_selected %}table-warning{% endif %}">
    <td>{% if item.is_selected %}⭐{% endif %} {{ item.nome }}</td>
    ...
</tr>
```

---

## 8. DADOS INICIAIS — MULTIPLICADORES DO SIMULADOR

```sql
INSERT INTO dev_eco_multiplicadores VALUES
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
```

---

## 9. DADOS INICIAIS — CADEIAS PRODUTIVAS

```sql
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
```

---

## 10. DADOS INICIAIS — INFRAESTRUTURA

```sql
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
```

---

## 11. DADOS INICIAIS — INDICADORES ESTADUAIS

```sql
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
```

---

## 12. ORDEM DE EXECUÇÃO DOS SQLs

Para recriar o banco do zero:

```bash
# 1. Criar schema base (tabelas)
mysql -u root -p supply_chain_system < sql/dev_economico_schema.sql

# 2. Inserir 79 municípios com dados IBGE reais
mysql -u root -p supply_chain_system < sql/dev_economico_municipios_completos.sql

# 3. Criar tabelas premium (IAEM, Gaps, Simulador) + dados iniciais
mysql -u root -p supply_chain_system < sql/dev_economico_premium.sql

# 4. Recalcular IAEM com proxies (sobrescreve dados do passo 3)
mysql -u root -p supply_chain_system < sql/fix_iaem_v2.sql

# 5. Gerar Gaps para todos os 79 municípios (sobrescreve dados do passo 3)
mysql -u root -p supply_chain_system < sql/fix_encadeamentos_todos.sql
```

---

## 13. CONFIGURAÇÃO DO AMBIENTE

### 13.1 requirements.txt
```
Flask==2.2.5
Flask-Login==0.6.2
Flask-SQLAlchemy==3.0.3
Flask-WTF==1.1.1
mysql-connector-python==8.0.33
SQLAlchemy==1.4.46
Werkzeug==2.2.3
WTForms==3.0.1
python-dotenv==1.0.0
email-validator==2.0.0
Jinja2==3.1.2
MarkupSafe==2.1.3
itsdangerous==2.1.2
click==8.1.3
markdown==3.5.2
```

### 13.2 config_local.py
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'SUA_SENHA_AQUI',
    'database': 'supply_chain_system',
    'port': 3306,
    'autocommit': True,
    'buffered': True,
    'connection_timeout': 120,
    'ssl_disabled': True,
    'pool_name': 'mypool',
    'pool_size': 10,
    'pool_reset_session': True,
    'use_pure': True,
    'auth_plugin': 'mysql_native_password',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'sql_mode': '',
    'raise_on_warnings': False,
    'get_warnings': False,
    'consume_results': True
}
DEBUG = True
FLASK_ENV = 'development'
SECRET_KEY = 'chave_secreta_do_sistema_local'
```

### 13.3 Executar
```bash
cd SupplyChainSystem
pip install -r requirements.txt
python run.py
# Acessa em http://localhost:8080/dev-economico/
```

---

## 14. ROADMAP PARA DADOS REAIS (PRODUÇÃO)

### Fontes confirmadas (todas 100% públicas):
1. **Receita Federal CNPJ** → score_empresas — `arquivos.receitafederal.gov.br/dados/cnpj/dados_abertos_cnpj/` (mensal)
2. **BACEN Pix** → score_pix — `olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/` (trimestral)
3. **Comex Stat** → score_exportacao — `balanca.economia.gov.br/balanca/bd/comexstat-bd/mun/` (mensal)
4. **MapBiomas** → score_uso_solo — `brasil.mapbiomas.org/downloads/` (anual)
5. **CAGED/MTE** → score_emprego — `bi.mte.gov.br/bgcaged/` (mensal)
6. **IBGE SIDRA** → PIB, PAM/PPM — `apisidra.ibge.gov.br/` (anual)

### Fontes já processadas (ETL simplificado):
- **IBGE SIDRA API** — JSON pronto, 1 chamada HTTP
- **IBGE CEMPRE** (SIDRA t/6450) — Empresas ativas por município, já agregado
- **Base dos Dados** (basedosdados.org) — CAGED, Comex, CNPJ já tratados via BigQuery gratuito
- **Comex Stat CSV** — Download direto, filtrar SG_UF_MUN = 'MS'

### O que falta implementar:
1. Pipeline ETL para popular tabelas reais (dev_eco_pix_fluxo, dev_eco_empresas_dinamica, etc.)
2. Tabela `dev_eco_comex` (única nova)
3. Motor de cálculo que use dados reais em vez de proxies
4. Modelo ML (XGBoost/LightGBM) para probabilidades calibradas

---

## 15. PROMPT PARA RECRIAR NO WINDSURF

Cole o seguinte prompt no Windsurf de outra máquina:

```
Preciso que você crie um Portal de Desenvolvimento Econômico Municipal para Mato Grosso do Sul.

STACK: Flask 2.2.5 + MySQL 8.0 + Jinja2 + Bootstrap 5 + Chart.js + Leaflet.js

O projeto é um Blueprint Flask chamado 'dev_economico' com url_prefix='/dev-economico'.

BANCO DE DADOS: MySQL database 'supply_chain_system' com as seguintes tabelas:
[Cole toda a seção 3 deste documento]

DADOS: 79 municípios de MS com dados reais do IBGE (Censo 2022, PIB Municipal 2021).
[Cole os SQLs de dev_economico_municipios_completos.sql]

IAEM: Índice de Antecipação Econômica Municipal com 6 componentes ponderados:
[Cole toda a seção 4 deste documento]

GAPS: Encadeamentos Produtivos Latentes:
[Cole toda a seção 5 deste documento]

ROTAS: 15 páginas + 12 APIs JSON:
[Cole toda a seção 6 deste documento]

TEMPLATES: Dashboard interativo com mapa Leaflet, gráficos Chart.js, filtro global por município que propaga entre abas mostrando município + 4 vizinhos geográficos.
[Cole toda a seção 7 deste documento]

DADOS INICIAIS:
[Cole seções 8-11]

ORDEM DE EXECUÇÃO SQL:
[Cole seção 12]
```

---

## 16. NOTAS IMPORTANTES

1. O módulo dev_economico é um Blueprint dentro de um sistema maior (SupplyChainSystem/IK Flow). Para V2 standalone, basta criar o Blueprint + um app Flask mínimo que o registre.

2. A autenticação usa `session['username']`. Para V2 standalone, pode simplificar removendo @login_required ou criando um login básico.

3. O `main_mysql.py` é o app Flask principal que registra TODOS os blueprints do sistema. Para V2, só precisa registrar o `dev_economico_bp`.

4. Os dados dos 79 municípios são REAIS (IBGE). Os scores IAEM e Gaps são estimativas baseadas em proxies.

5. O dashboard dinâmico (dashboard_dinamico.html) é o template mais complexo (~33k). Usa Leaflet para mapa + Chart.js para gráficos + JavaScript vanilla para interatividade.

6. Todos os templates herdam de `base.html` do sistema principal. Para V2 standalone, criar um base.html mínimo com Bootstrap 5 + CDN do Chart.js e Leaflet.
