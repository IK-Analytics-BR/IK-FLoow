# Portal de Desenvolvimento Econômico Municipal — MS
## Guia de Implantação, Fontes de Dados e Instruções

---

## 1. Arquitetura do Portal

O portal foi integrado ao **IK Flow (SupplyChainSystem)** usando a mesma stack:

| Componente | Tecnologia |
|---|---|
| Backend | Flask (Python) + Blueprint `dev_economico` |
| Frontend | HTML5 + Bootstrap 5 + Chart.js + Font Awesome |
| Banco de Dados | MySQL (mesmo servidor do IK Flow) |
| Deploy | AWS EC2 (Nginx + Gunicorn) — mesma instância |

### Arquivos Criados

```
SupplyChainSystem/
├── sql/
│   └── dev_economico_schema.sql          # Schema MySQL + dados iniciais
├── app/
│   ├── routes/
│   │   └── dev_economico_routes.py       # Rotas Flask (Blueprint)
│   ├── templates/
│   │   └── dev_economico/
│   │       ├── dashboard.html            # Dashboard principal
│   │       ├── diagnostico.html          # Diagnóstico econômico
│   │       ├── agroindustria.html        # Agroindustrialização
│   │       ├── investimentos.html        # Atração de investimentos
│   │       ├── logistica.html            # Logística regional
│   │       ├── turismo.html              # Turismo
│   │       ├── inovacao.html             # Economia digital
│   │       ├── qualificacao.html         # Qualificação profissional
│   │       ├── infraestrutura.html       # Infraestrutura estratégica
│   │       ├── compras.html              # Compras governamentais
│   │       └── governanca.html           # Governança e indicadores
│   ├── static/
│   │   └── css/
│   │       └── dev_economico.css         # CSS específico do portal
│   └── scripts/
│       └── importar_dados_economicos.py  # Script de importação de dados
```

---

## 2. Etapas de Implantação

### Etapa 1: Criar as Tabelas no MySQL

```bash
# No servidor AWS (ou local)
mysql -u root -p supply_chain_system < sql/dev_economico_schema.sql
```

Isso cria as tabelas `dev_eco_*` e insere dados iniciais reais de 20 municípios.

### Etapa 2: Registrar o Blueprint no Flask

Adicionar no arquivo `app/main_mysql.py`:

```python
# No topo, junto com os outros imports de blueprints:
from routes.dev_economico_routes import dev_economico_bp

# Junto com os outros register_blueprint:
app.register_blueprint(dev_economico_bp)
```

### Etapa 3: Adicionar Menu na Sidebar

No `app/templates/base.html`, adicionar dentro do `<ul class="list-unstyled components">`:

```html
<!-- Desenvolvimento Econômico -->
<li>
    <a href="#devEconomicoSubmenu" data-bs-toggle="collapse" aria-expanded="false" class="dropdown-toggle">
        <i class="fas fa-chart-line"></i> Dev. Econômico
    </a>
    <ul class="collapse list-unstyled" id="devEconomicoSubmenu">
        <li><a href="/dev-economico/"><i class="fas fa-tachometer-alt"></i> Dashboard</a></li>
        <li><a href="/dev-economico/diagnostico"><i class="fas fa-stethoscope"></i> Diagnóstico</a></li>
        <li><a href="/dev-economico/agroindustria"><i class="fas fa-tractor"></i> Agroindústria</a></li>
        <li><a href="/dev-economico/investimentos"><i class="fas fa-hand-holding-usd"></i> Investimentos</a></li>
        <li><a href="/dev-economico/logistica"><i class="fas fa-truck"></i> Logística</a></li>
        <li><a href="/dev-economico/turismo"><i class="fas fa-umbrella-beach"></i> Turismo</a></li>
        <li><a href="/dev-economico/inovacao"><i class="fas fa-laptop-code"></i> Inovação</a></li>
        <li><a href="/dev-economico/qualificacao"><i class="fas fa-graduation-cap"></i> Qualificação</a></li>
        <li><a href="/dev-economico/infraestrutura"><i class="fas fa-hard-hat"></i> Infraestrutura</a></li>
        <li><a href="/dev-economico/compras"><i class="fas fa-shopping-bag"></i> Compras</a></li>
        <li><a href="/dev-economico/governanca"><i class="fas fa-landmark"></i> Governança</a></li>
    </ul>
</li>
```

### Etapa 4: Reiniciar o Serviço

```bash
sudo systemctl restart supplychain
```

### Etapa 5: Importar Dados Reais Completos

```bash
cd /home/ubuntu/SupplyChainSystem/app
python scripts/importar_dados_economicos.py
```

---

## 3. Fontes de Dados Reais — De Onde Colher

### 3.1 PIB Municipal (IBGE)

| Item | Detalhe |
|---|---|
| **Fonte** | IBGE — Produto Interno Bruto dos Municípios |
| **URL** | https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/9088-produto-interno-bruto-dos-municipios.html |
| **API** | https://servicodados.ibge.gov.br/api/v3/agregados/5938/periodos/2021/variaveis/37?localidades=N6[N3[50]] |
| **Periodicidade** | Anual (defasagem de ~2 anos) |
| **Dados** | PIB total, PIB por setor (agro, indústria, serviços, adm pública), PIB per capita |
| **Tabela MySQL** | `dev_eco_municipios` e `dev_eco_pib_municipal` |

**Como baixar:**
1. Acesse https://sidra.ibge.gov.br/tabela/5938
2. Selecione: UF = Mato Grosso do Sul, Todos os municípios
3. Variáveis: PIB a preços correntes, VA por setor
4. Exporte em CSV
5. Use o script `importar_dados_economicos.py` para carregar no MySQL

### 3.2 Empregos Formais (CAGED / Novo CAGED)

| Item | Detalhe |
|---|---|
| **Fonte** | Ministério do Trabalho — Novo CAGED |
| **URL** | https://bi.mte.gov.br/bgcaged/ |
| **API** | http://pdet.mte.gov.br/novo-caged |
| **Periodicidade** | Mensal |
| **Dados** | Admissões, desligamentos, saldo, estoque por município e setor CNAE |
| **Tabela MySQL** | `dev_eco_empregos` |

**Como baixar:**
1. Acesse https://bi.mte.gov.br/bgcaged/
2. Selecione: UF = MS, Período desejado
3. Baixe microdados ou use o painel BI
4. Alternativa: RAIS (dados anuais mais completos) em http://pdet.mte.gov.br/rais

### 3.3 Dados Econômicos (IPEA Data)

| Item | Detalhe |
|---|---|
| **Fonte** | IPEA — Instituto de Pesquisa Econômica Aplicada |
| **URL** | http://www.ipeadata.gov.br/ |
| **API OData** | http://www.ipeadata.gov.br/api/odata4/ |
| **Periodicidade** | Variável (mensal, trimestral, anual) |
| **Dados** | PIB estadual, inflação, taxa de juros, indicadores sociais |
| **Tabela MySQL** | `dev_eco_ipea_cache` |

**Séries úteis:**
- `PIB_ESTms` — PIB de MS
- `POPTOT` — População total
- `PREam_IPCAG` — IPCA mensal

### 3.4 Comércio Exterior (COMEX STAT)

| Item | Detalhe |
|---|---|
| **Fonte** | MDIC — Ministério do Desenvolvimento |
| **URL** | https://comexstat.mdic.gov.br/ |
| **Periodicidade** | Mensal |
| **Dados** | Exportações e importações por município, NCM, país |
| **Tabela MySQL** | `dev_eco_exportacoes` |

**Como baixar:**
1. Acesse https://comexstat.mdic.gov.br/pt/municipio
2. Filtro: UF = MS, Ano desejado
3. Exporte em CSV

### 3.5 População (IBGE Cidades)

| Item | Detalhe |
|---|---|
| **Fonte** | IBGE Cidades |
| **URL** | https://cidades.ibge.gov.br/ |
| **API** | https://servicodados.ibge.gov.br/api/v3/malhas/estados/50?formato=application/vnd.geo+json |
| **Dados** | População estimada, área, densidade demográfica |
| **Tabela MySQL** | `dev_eco_municipios` |

### 3.6 IDH Municipal (PNUD/Atlas Brasil)

| Item | Detalhe |
|---|---|
| **Fonte** | Atlas do Desenvolvimento Humano |
| **URL** | http://www.atlasbrasil.org.br/ |
| **Dados** | IDHM, IDHM Educação, IDHM Longevidade, IDHM Renda |
| **Tabela MySQL** | `dev_eco_municipios` (coluna `idhm`) |

### 3.7 Turismo (FUNDTUR-MS)

| Item | Detalhe |
|---|---|
| **Fonte** | Fundação de Turismo de MS |
| **URL** | https://www.fundtur.ms.gov.br/ |
| **Dados** | Fluxo turístico, receita, destinos, segmentos |
| **Tabela MySQL** | `dev_eco_turismo` |

### 3.8 Agropecuária (CONAB / PAM-IBGE)

| Item | Detalhe |
|---|---|
| **Fonte** | CONAB + IBGE PAM |
| **URL CONAB** | https://www.conab.gov.br/info-agro/safras |
| **URL PAM** | https://sidra.ibge.gov.br/pesquisa/pam/tabelas |
| **Dados** | Produção agrícola por município, área plantada, produtividade |
| **Tabela MySQL** | `dev_eco_cadeias_produtivas` |

---

## 4. Fluxo de Atualização de Dados

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  Fontes Oficiais │────▶│  Script Python│────▶│  MySQL      │
│  IBGE, IPEA,     │     │  importar_    │     │  dev_eco_*  │
│  CAGED, COMEX    │     │  dados.py     │     │  tabelas    │
└─────────────────┘     └──────────────┘     └──────┬──────┘
                                                      │
                                                      ▼
                                              ┌──────────────┐
                                              │  Flask Routes │
                                              │  + Templates  │
                                              │  HTML/Chart.js│
                                              └──────────────┘
```

### Frequência recomendada:
- **PIB Municipal**: Anual (quando IBGE publicar)
- **CAGED/Empregos**: Mensal
- **Exportações**: Mensal
- **População**: Anual (estimativa IBGE)
- **Turismo**: Trimestral/Anual
- **Indicadores IPEA**: Conforme disponibilidade

---

## 5. Próximos Passos

1. ✅ Schema MySQL criado com dados iniciais reais
2. ✅ Rotas Flask (Blueprint) criadas
3. ✅ Templates HTML (Dashboard + Diagnóstico) criados
4. ✅ CSS específico do portal criado
5. ⬜ Completar os 79 municípios no MySQL (script de importação)
6. ⬜ Registrar blueprint no `main_mysql.py`
7. ⬜ Adicionar menu na sidebar do `base.html`
8. ⬜ Criar templates restantes (agroindustria, investimentos, etc.)
9. ⬜ Executar script de importação de dados reais
10. ⬜ Deploy na AWS
