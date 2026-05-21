# Roadmap para Produção — IAEM e Gaps com Dados Reais

## Situação Atual (Demonstração)

| Componente IAEM | Proxy Usado Hoje | Fonte Real Confirmada |
|---|---|---|
| **score_pix** (25%) | Faixas de PIB per capita | BACEN Pix Dados Abertos |
| **score_empresas** (20%) | Faixas de população | Receita Federal — Dados Abertos CNPJ |
| **score_emprego** (20%) | Faixas de PIB total | CAGED/Novo CAGED (MTE) |
| **score_uso_solo** (15%) | Razão PIB agro / PIB total | MapBiomas Downloads |
| **score_exportacao** (10%) | Razão PIB indústria / PIB total | Siscomex / Comex Stat (MDIC) |
| **score_logistica** (10%) | Faixas de população | Derivado de Comex (volume/peso) + CNPJ (setor H) |

**Gaps (Encadeamentos Latentes):** Hoje são 11 registros manuais. Em produção, calculados cruzando CNPJ (CNAEs presentes) × IBGE PAM/PPM (produção agrícola) × Comex Stat (importações regionais).

---

## Fontes de Dados Reais Confirmadas

### 1. Receita Federal — Dados Abertos CNPJ (score_empresas)

- **URL:** `https://arquivos.receitafederal.gov.br/dados/cnpj/dados_abertos_cnpj/2025-11/`
- **Formato:** ZIP → CSV (separador `;`)
- **Atualização:** Mensal (nova pasta por mês: `/2025-11/`, `/2025-12/`, etc.)
- **Acesso:** 100% público, download direto, sem autenticação
- **Arquivos relevantes:**
  - `Empresas*.zip` — CNPJ raiz, razão social, natureza jurídica, porte
  - `Estabelecimentos*.zip` — **O principal**: CNPJ completo, CNAE principal, CNAE secundário, município, UF, situação cadastral, data abertura
  - `Socios*.zip` — Quadro societário
  - `Simples*.zip` — Optantes Simples/MEI
  - `Cnaes.zip` — Tabela de códigos CNAE
  - `Municipios.zip` — Tabela de códigos de município
- **Campos do arquivo Estabelecimentos (mais importante):**
  ```
  CNPJ_BASICO; CNPJ_ORDEM; CNPJ_DV; IDENTIFICADOR_MATRIZ_FILIAL;
  NOME_FANTASIA; SITUACAO_CADASTRAL; DATA_SITUACAO_CADASTRAL;
  MOTIVO_SITUACAO_CADASTRAL; NOME_CIDADE_EXTERIOR; PAIS;
  DATA_INICIO_ATIVIDADE; CNAE_FISCAL_PRINCIPAL; CNAE_FISCAL_SECUNDARIA;
  TIPO_LOGRADOURO; LOGRADOURO; NUMERO; COMPLEMENTO; BAIRRO; CEP;
  UF; MUNICIPIO; ...
  ```
- **Tabela destino:** `dev_eco_empresas_dinamica` (já criada)
- **Mapeamento de campos:**

  | Campo CSV (Estabelecimentos) | Campo Tabela | Lógica |
  |---|---|---|
  | `MUNICIPIO` | `municipio_id` | Código IBGE → lookup `dev_eco_municipios.codigo_ibge` |
  | `CNAE_FISCAL_PRINCIPAL` | `cnae_secao` | Primeiros 2 dígitos = divisão CNAE |
  | `CNAE_FISCAL_PRINCIPAL` | `cnae_descricao` | Lookup na tabela `Cnaes.zip` |
  | `SITUACAO_CADASTRAL = 02` | `estoque_ativas` | COUNT WHERE situacao = 'Ativa' |
  | `DATA_INICIO_ATIVIDADE` no mês | `abertas` | COUNT novas no mês |
  | `DATA_SITUACAO_CADASTRAL` no mês + situacao != 02 | `fechadas` | COUNT baixadas no mês |
  | `abertas - fechadas` | `saldo` | Calculado |

- **ETL necessário:**
  ```python
  def etl_cnpj_receita(ano_mes='2025-11'):
      """
      1. Download dos ZIPs de Estabelecimentos (~4GB compactado)
      2. Descompactar e ler CSVs (encoding latin-1, sep=';')
      3. Filtrar UF = 'MS' (só Mato Grosso do Sul = ~200k registros)
      4. Agrupar por município × CNAE × mês
      5. Calcular abertas, fechadas, saldo, estoque_ativas
      6. INSERT/UPDATE em dev_eco_empresas_dinamica
      """
  ```
- **Esforço:** ⭐⭐ Médio — Arquivos grandes mas estrutura simples, filtrar por UF=MS reduz muito

---

### 2. BACEN — Pix Dados Abertos (score_pix)

- **URL:** `https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/aplicacao`
- **API REST (OData):** Consulta via URL com parâmetros
- **Formato:** JSON
- **Atualização:** Trimestral (defasagem ~45 dias)
- **Acesso:** 100% público, sem autenticação
- **Endpoints relevantes:**
  - `EstatisticasTransacoesPix` — Volume e quantidade por município
  - `EstatisticasFraudesPix` — Dados de fraude (complementar)
- **Exemplo de consulta:**
  ```
  https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata/
  EstatisticasTransacoesPix?$format=json&$top=100
  &$filter=AnoMes eq '202501' and Municipio eq '5002704'
  ```
- **Campos disponíveis:**
  ```
  AnoMes, Municipio (cod IBGE), TipoPessoa (PF/PJ),
  TipoTransacao (enviada/recebida), Quantidade, Valor
  ```
- **Tabela destino:** `dev_eco_pix_fluxo` (já criada)
- **Mapeamento de campos:**

  | Campo API Pix | Campo Tabela | Lógica |
  |---|---|---|
  | `Municipio` | `municipio_id` | Código IBGE → lookup |
  | `AnoMes` | `ano_mes` | Formato YYYY-MM |
  | `Valor` WHERE TipoPessoa=PJ, Tipo=recebida | `volume_pj_recebido` | SUM |
  | `Valor` WHERE TipoPessoa=PJ, Tipo=enviada | `volume_pj_enviado` | SUM |
  | `Valor` WHERE TipoPessoa=PF, Tipo=recebida | `volume_pf_recebido` | SUM |
  | `Quantidade` WHERE TipoPessoa=PJ | `qtd_transacoes_pj` | SUM |
  | Calculado | `variacao_mensal` | (vol_atual - vol_anterior) / vol_anterior |
  | Calculado | `variacao_anual` | (vol_atual - vol_12m_atras) / vol_12m_atras |

- **ETL necessário:**
  ```python
  def etl_pix_bacen(ano_mes='2025-01'):
      """
      1. Para cada município MS (79 códigos IBGE):
         GET .../EstatisticasTransacoesPix?$filter=Municipio eq '{cod}'
      2. Agregar PF/PJ, enviado/recebido
      3. Calcular variações mensal e anual
      4. INSERT/UPDATE em dev_eco_pix_fluxo
      """
  ```
- **Limitação:** Dados são trimestrais (não mensais). Granularidade por município pode não estar disponível para todos — verificar na API.
- **Esforço:** ⭐⭐ Médio — API REST simples, mas precisa verificar granularidade municipal

---

### 3. Siscomex / Comex Stat — MDIC (score_exportacao)

- **URL:** `https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas/base-de-dados-bruta`
- **Formato:** CSV (separador `;`)
- **Atualização:** Mensal (dados até jan/2026 já disponíveis)
- **Acesso:** 100% público, download direto
- **Arquivos por município (os mais relevantes):**
  - **Exportação:** `https://balanca.economia.gov.br/balanca/bd/comexstat-bd/mun/EXP_{ANO}_MUN.csv`
  - **Importação:** `https://balanca.economia.gov.br/balanca/bd/comexstat-bd/mun/IMP_{ANO}_MUN.csv`
- **Layout CSV por Município:**
  ```
  CO_ANO; CO_MES; SH4; CO_PAIS; SG_UF_MUN; CO_MUN; KG_LIQUIDO; VL_FOB
  ```
  - `CO_ANO` — Ano
  - `CO_MES` — Mês
  - `SH4` — Código do produto (Sistema Harmonizado 4 dígitos)
  - `CO_PAIS` — País destino/origem
  - `SG_UF_MUN` — UF da empresa (filtrar `MS`)
  - `CO_MUN` — **Código município da empresa** (IBGE 7 dígitos)
  - `KG_LIQUIDO` — Peso em kg
  - `VL_FOB` — **Valor em US$ FOB**
- **Tabela destino:** `dev_eco_comex` (a criar)
- **Schema proposto:**
  ```sql
  CREATE TABLE dev_eco_comex (
      id INT AUTO_INCREMENT PRIMARY KEY,
      municipio_id INT NOT NULL,
      ano_mes VARCHAR(7) NOT NULL,
      tipo ENUM('EXP','IMP') NOT NULL,
      sh4 VARCHAR(4),
      sh4_descricao VARCHAR(200),
      pais_codigo INT,
      kg_liquido DECIMAL(18,2) DEFAULT 0,
      vl_fob_usd DECIMAL(18,2) DEFAULT 0,
      FOREIGN KEY (municipio_id) REFERENCES dev_eco_municipios(id),
      INDEX idx_mun_mes (municipio_id, ano_mes),
      INDEX idx_tipo (tipo)
  );
  ```
- **Mapeamento de campos:**

  | Campo CSV Comex | Campo Tabela | Lógica |
  |---|---|---|
  | `CO_MUN` | `municipio_id` | Código IBGE → lookup |
  | `CO_ANO`-`CO_MES` | `ano_mes` | Formato YYYY-MM |
  | Arquivo EXP/IMP | `tipo` | 'EXP' ou 'IMP' |
  | `SH4` | `sh4` | Direto |
  | `KG_LIQUIDO` | `kg_liquido` | Direto |
  | `VL_FOB` | `vl_fob_usd` | Direto |

- **Para score_exportacao:**
  ```python
  def calcular_score_exportacao(municipio_id):
      # Total exportado nos últimos 12 meses
      # Variação vs 12 meses anteriores
      # Diversificação (qtd de SH4 distintos)
      # Volume relativo à média estadual
  ```
- **Esforço:** ⭐ Baixo — CSV simples, download direto, filtrar SG_UF_MUN = 'MS'

---

### 4. MapBiomas — Uso do Solo (score_uso_solo)

- **URL:** `https://brasil.mapbiomas.org/downloads/`
- **Formato:** XLSX / CSV / GeoTIFF (raster)
- **Atualização:** Anual (coleção atualizada ~outubro)
- **Acesso:** 100% público, download após cadastro gratuito
- **Dados disponíveis:**
  - Estatísticas de cobertura e uso do solo por município
  - Classes: Soja, Cana, Pastagem, Eucalipto/Silvicultura, Floresta, Área Urbana, etc.
  - Área em hectares por classe por município por ano
  - Transições de uso (o que mudou de um ano para outro)
- **Tabela destino:** `dev_eco_uso_solo` (já criada)
- **Mapeamento de campos:**

  | Campo MapBiomas | Campo Tabela | Lógica |
  |---|---|---|
  | Código município | `municipio_id` | Código IBGE → lookup |
  | Ano da coleção | `ano` | Direto |
  | Classe de uso | `classe` | Nome da classe (Soja, Pastagem, etc.) |
  | Área (ha) | `area_hectares` | Direto |
  | Área / Área total município | `percentual_territorio` | Calculado |
  | Diferença vs ano anterior | `variacao_anual_ha` | Calculado |

- **Para score_uso_solo:**
  ```python
  def calcular_score_uso_solo(municipio_id):
      # % do território em uso produtivo (agro + silvicultura)
      # Variação anual de área agrícola (expansão = positivo)
      # Diversificação de culturas
      # Proporção pastagem degradada vs produtiva
  ```
- **Esforço:** ⭐⭐ Médio — Download anual, parsing de planilha, cadastro necessário

---

## Mapeamento Completo: Fonte → Tabela → Score IAEM

```
┌──────────────────────────────────────────────────────────────────┐
│                    FONTES DE DADOS REAIS                         │
│                                                                  │
│  Receita Federal    BACEN Pix     Comex Stat     MapBiomas      │
│  (CNPJ mensal)     (API OData)   (CSV mensal)   (anual)        │
│  ↓                  ↓              ↓              ↓              │
│  Estabelecimentos   Estatísticas   EXP/IMP_MUN   Cobertura     │
│  + Empresas.zip     TransacoesPix  .csv           uso solo      │
└────────┬──────────────┬──────────────┬──────────────┬───────────┘
         │              │              │              │
    Filtrar UF=MS   Query por      Filtrar         Download
    ~200k registros  79 municípios  SG_UF_MUN=MS   por município
         │              │              │              │
         ▼              ▼              ▼              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    BANCO DE DADOS (MySQL)                        │
│                                                                  │
│  dev_eco_empresas_dinamica  ← CNPJ (abertas/fechadas/CNAE)     │
│  dev_eco_pix_fluxo          ← Pix (volume PJ/PF)               │
│  dev_eco_comex (NOVA)       ← Comex (exp/imp por SH4)          │
│  dev_eco_uso_solo           ← MapBiomas (área por classe)       │
│  dev_eco_emprego_mensal     ← CAGED (admissões/desligamentos)  │
└────────┬──────────────┬──────────────┬──────────────┬───────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    CÁLCULO IAEM REAL                             │
│                                                                  │
│  score_empresas (20%)  ← saldo abertas-fechadas, estoque ativas │
│  score_pix (25%)       ← variação volume Pix PJ, tendência 6m  │
│  score_exportacao (10%)← VL_FOB total, variação, diversificação │
│  score_uso_solo (15%)  ← % uso produtivo, expansão agrícola     │
│  score_emprego (20%)   ← saldo CAGED, estoque, salário médio   │
│  score_logistica (10%) ← derivado de Comex (kg) + CNPJ setor H │
│                                                                  │
│  IAEM = 0.25×pix + 0.20×empresas + 0.20×emprego                │
│       + 0.15×uso_solo + 0.10×exportacao + 0.10×logistica        │
└──────────────────────────────────────────────────────────────────┘
```

---

## Cálculo dos Gaps com Dados Reais

Com os dados do CNPJ (CNAEs presentes) + Comex Stat (importações), podemos calcular Gaps automaticamente:

```python
def calcular_gaps_automatico(municipio_id):
    """
    Cruza:
    1. CNPJ → quais CNAEs existem no município (indústrias presentes)
    2. Comex Stat IMP → o que o município/região importa (demanda não atendida)
    3. IBGE PAM/PPM → o que o município produz de matéria-prima
    
    Gap = matéria-prima local + importação do produto acabado + ausência da indústria
    """
    
    # 1. CNAEs industriais presentes (seção C = Indústria de Transformação)
    cnaes_presentes = query_db("""
        SELECT DISTINCT cnae_secao, cnae_descricao, estoque_ativas
        FROM dev_eco_empresas_dinamica
        WHERE municipio_id = %s AND cnae_secao LIKE 'C%' AND estoque_ativas > 0
    """, (municipio_id,))
    
    # 2. Importações da região (município + vizinhos)
    importacoes = query_db("""
        SELECT sh4, SUM(vl_fob_usd) as total_imp
        FROM dev_eco_comex
        WHERE municipio_id IN (SELECT id FROM dev_eco_municipios WHERE regiao_macro = 
            (SELECT regiao_macro FROM dev_eco_municipios WHERE id = %s))
        AND tipo = 'IMP'
        GROUP BY sh4 ORDER BY total_imp DESC
    """, (municipio_id,))
    
    # 3. Mapear SH4 importado → CNAE industrial necessário
    # Se CNAE não existe no município → é um Gap
    # Valor do Gap = volume importado que poderia ser produzido localmente
```

---

## Infraestrutura Técnica

### Pipeline ETL (Celery + Redis)

```python
# app/etl/scheduler.py
from celery import Celery
from celery.schedules import crontab

app = Celery('etl', broker='redis://localhost:6379/0')

app.conf.beat_schedule = {
    # Mensal: dia 15 de cada mês (dados do mês anterior já disponíveis)
    'etl-cnpj-mensal': {
        'task': 'etl.cnpj_receita',
        'schedule': crontab(day_of_month='15', hour=3),
    },
    'etl-comex-mensal': {
        'task': 'etl.comex_stat',
        'schedule': crontab(day_of_month='15', hour=4),
    },
    # Trimestral: Pix BACEN
    'etl-pix-trimestral': {
        'task': 'etl.pix_bacen',
        'schedule': crontab(day_of_month='1', month_of_year='1,4,7,10', hour=3),
    },
    # Anual: MapBiomas (outubro)
    'etl-mapbiomas-anual': {
        'task': 'etl.mapbiomas',
        'schedule': crontab(day_of_month='1', month_of_year='11', hour=3),
    },
    # Após cada ETL: recalcular IAEM
    'recalcular-iaem': {
        'task': 'etl.calcular_iaem',
        'schedule': crontab(day_of_month='16', hour=5),
    },
}
```

### Dependências adicionais
```
# requirements_etl.txt
celery>=5.3
redis>=5.0
requests>=2.31
pandas>=2.0
openpyxl>=3.1       # para MapBiomas XLSX
scikit-learn>=1.3   # para modelo ML futuro
xgboost>=2.0        # para modelo ML futuro
```

---

## Modelo de Machine Learning (Probabilidades)

Hoje as probabilidades são derivadas linearmente:
```sql
prob_crescimento_6m = LEAST(95, iaem_score * 1.08)
```

Em produção, com séries históricas dos dados reais:

### Modelo Proposto
- **Tipo:** Gradient Boosting (XGBoost ou LightGBM)
- **Target:** Crescimento do PIB municipal nos próximos 6/12/24 meses
- **Features:**
  - Série temporal Pix PJ (6 trimestres)
  - Saldo CAGED (6 meses)
  - Saldo abertura/fechamento empresas CNPJ (6 meses)
  - Variação uso do solo (anual)
  - Exportações FOB (6 meses)
  - Variáveis macroeconômicas (Selic, câmbio, IPCA)
- **Treino:** Dados históricos 2020-2025 (Comex tem desde 1997!)
- **Validação:** Walk-forward validation (treina em t, prevê t+1)

---

## Cronograma Estimado

| Fase | Descrição | Fonte | Prazo | Esforço |
|---|---|---|---|---|
| **Fase 1** | ETL CNPJ Receita Federal | `arquivos.receitafederal.gov.br` | 2-3 semanas | 1 dev |
| **Fase 2** | ETL Comex Stat por município | `balanca.economia.gov.br` | 1-2 semanas | 1 dev |
| **Fase 3** | ETL Pix BACEN | `olinda.bcb.gov.br` | 1-2 semanas | 1 dev |
| **Fase 4** | ETL MapBiomas uso do solo | `brasil.mapbiomas.org` | 1-2 semanas | 1 dev |
| **Fase 5** | Recálculo IAEM com dados reais | — | 2 semanas | 1 dev |
| **Fase 6** | Cálculo automático de Gaps (CNPJ × Comex) | — | 2-3 semanas | 1 dev |
| **Fase 7** | Modelo ML para probabilidades | — | 3-4 semanas | 1 dev/DS |
| **Fase 8** | Scheduler automático + monitoramento | — | 1-2 semanas | 1 dev |

**Total estimado: 3-4 meses com 1 desenvolvedor dedicado**

---

## Acessos Necessários

| Fonte | URL | Acesso | Convênio? |
|---|---|---|---|
| Receita Federal CNPJ | `arquivos.receitafederal.gov.br/dados/cnpj/dados_abertos_cnpj/` | **Público** | Não |
| BACEN Pix | `olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/` | **Público** | Não |
| Comex Stat (MDIC) | `balanca.economia.gov.br/balanca/bd/comexstat-bd/mun/` | **Público** | Não |
| MapBiomas | `brasil.mapbiomas.org/downloads/` | **Público** (cadastro) | Não |
| CAGED/MTE | `bi.mte.gov.br/bgcaged/` | **Público** | Não |
| IBGE SIDRA | `apisidra.ibge.gov.br/` | **Público** | Não |

**Todas as 4 fontes principais que você identificou são 100% públicas. Não precisa de nenhum convênio.**

---

## Resumo Executivo

| Item | Hoje (Demo) | Produção (Dados Reais) |
|---|---|---|
| **score_empresas** | Proxy: faixas de população | Real: CNPJ Receita Federal (abertas/fechadas/CNAE) |
| **score_pix** | Proxy: faixas de PIB per capita | Real: API Pix BACEN (volume PJ/PF) |
| **score_exportacao** | Proxy: razão PIB indústria | Real: Comex Stat (VL_FOB por município) |
| **score_uso_solo** | Proxy: razão PIB agro | Real: MapBiomas (hectares por classe) |
| **score_emprego** | Proxy: faixas de PIB total | Real: CAGED (admissões/desligamentos) |
| **score_logistica** | Proxy: faixas de população | Real: Comex (kg_liquido) + CNPJ (setor H) |
| **Gaps** | 11 registros manuais | Automático: CNPJ × Comex × IBGE para 79 municípios |
| **Probabilidades** | Fórmula linear | Modelo ML com séries históricas |
| **Atualização** | Manual (SQL scripts) | Automática (ETL mensal/trimestral/anual) |

**A estrutura do banco de dados já está pronta.** O que falta:
1. **Pipeline ETL** para baixar e processar dados das 4 fontes públicas
2. **Tabela `dev_eco_comex`** (única tabela nova necessária)
3. **Motor de cálculo** que use dados reais em vez de proxies
4. **Modelo ML** para probabilidades calibradas (fase futura)
