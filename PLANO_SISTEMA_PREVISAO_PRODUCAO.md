# Sistema de Previsão de Produção Inteligente

## Visão Geral

Sistema para calcular automaticamente a previsão de conclusão de produção e entrega, considerando:
- ✅ Jornada de trabalho (turnos, horários, dias úteis)
- ✅ Tempo médio de cada etapa para cada produto
- ✅ Fila atual de produção (o que está aguardando)
- ✅ Progresso atual (o que já foi produzido)
- ✅ Capacidade por etapa (gargalos)

**Data de Implementação:** 26/12/2025

---

## FASE A: Estrutura de Dados Base ✅ CONCLUÍDA

### A1. Jornada de Trabalho ✅
**NOTA:** Usa tabelas EXISTENTES do módulo de Jornada de Trabalho:
- `jornadas_trabalho` - Jornadas por empresa
- `jornada_horarios` - Horários por dia/turno

**Estrutura `jornada_horarios`:**
```sql
- jornada_id (FK para jornadas_trabalho)
- dia_semana (ENUM: 'Segunda', 'Terça', etc)
- turno (ENUM: 'Manhã', 'Tarde', 'Noite', 'Integral')
- hora_inicio (TIME)
- hora_fim (TIME)
```

### A2. Tabela `produtos_tempo_etapa` ✅
Tempo padrão/médio de cada produto em cada etapa.

```sql
- produto_id (FK products)
- etapa_id (FK producao_etapas)
- tempo_padrao_minutos (definido manualmente)
- tempo_medio_historico (calculado do histórico)
- tempo_minimo_historico
- tempo_maximo_historico
- qtd_amostras (quantas OPs usadas no cálculo)
- ajuste_manual (1 se admin editou)
- ultima_atualizacao_historico
- observacao
```

### A3. Tabela `config_feriados` ✅
Feriados e dias não úteis.

```sql
- empresa_id (NULL = todas as empresas)
- data (DATE)
- descricao (VARCHAR 100)
- tipo (ENUM: feriado, folga, manutencao, outro)
- recorrente_anual (1 = repete todo ano)
```
**Dados pré-carregados:** Feriados nacionais 2025/2026

### A4. Tabela `config_capacidade_etapa` ✅
Capacidade de processamento por etapa.

```sql
- empresa_id
- etapa_id
- capacidade_diaria_lotes (default 10)
- capacidade_simultanea (default 1)
- tempo_setup_minutos (default 0)
- prioridade_gargalo (1-10)
- observacao
```

### A5. Tabela `log_calculo_previsao` ✅
Log de cálculos para auditoria.

### A6. Views ✅
- `vw_fila_producao_completa` - Fila de produção com posição e tempo na fila
- `vw_resumo_etapas_producao` - Resumo por etapa com indicador de gargalo

### A7. Funções SQL ✅
- `fn_minutos_uteis_dia()` - Calcula minutos úteis em um dia
- `fn_is_dia_util()` - Verifica se é dia útil

### A8. Stored Procedure ✅
- `sp_calcular_tempos_historicos()` - Recalcula tempos do histórico de produção

---

## FASE B: Telas de Administração ✅ CONCLUÍDA

### B1. Configuração de Jornada de Trabalho ✅
**Rota:** `/industria/jornada-trabalho` (módulo existente)

- Usa módulo existente de Jornada de Trabalho
- Menu: Indústria > Jornada de Trabalho

### B2. Configuração de Tempos por Produto ✅
**Rota:** `/industria/config/tempos-producao`
**Template:** `config_tempos_producao.html`

- Lista de produtos com tempo por etapa
- Coluna "Tempo Padrão" (editável)
- Coluna "Tempo Médio Histórico" (calculado)
- Coluna "Amostras" (quantas OPs)
- Botão "Recalcular do Histórico"
- Filtros: produto, etapa

### B3. Configuração de Feriados ✅
**Rota:** `/industria/config/feriados`
**Template:** `config_feriados.html`

- Lista de feriados por ano
- Adicionar/Editar/Excluir feriados
- Marcar como recorrente anual
- Filtro por empresa

### B4. Configuração de Capacidade por Etapa ✅
**Rota:** `/industria/config/capacidade-etapas`
**Template:** `config_capacidade_etapas.html`

- Lista de etapas com capacidade
- Capacidade diária (lotes/dia)
- Capacidade simultânea
- Tempo de setup

---

## FASE C: Cálculo de Previsão ✅ CONCLUÍDA

**Arquivo:** `app/services/previsao_producao_service.py`

### C1. Funções de Jornada ✅
- `get_jornada_dia()` - Busca jornada de um dia específico
- `get_minutos_uteis_dia()` - Calcula minutos úteis por dia
- `is_dia_util()` - Verifica se é dia útil (considera feriados)
- `get_proximos_dias_uteis()` - Lista próximos N dias úteis

### C2. Funções de Tempo por Produto ✅
- `get_tempo_produto_etapa()` - Tempo de um produto em uma etapa
- `get_tempos_todas_etapas_produto()` - Todos os tempos de um produto
- `get_tempo_total_produto()` - Soma de todas as etapas

### C3. Funções de Fila ✅
- `get_fila_etapa()` - Lotes na fila de uma etapa
- `get_posicao_na_fila()` - Posição de um lote na fila
- `get_tempo_fila_estimado()` - Tempo de espera na fila

### C4. Funções de Previsão ✅
- `calcular_tempo_restante_lote()` - Tempo restante para um lote
- `calcular_previsao_lote()` - Data/hora prevista de um lote
- `calcular_previsao_op()` - Previsão de conclusão de uma OP
- `calcular_previsao_orcamento()` - Previsão para um orçamento
- `adicionar_minutos_uteis()` - Adiciona minutos úteis a uma data

### C5. Funções de Gargalos ✅
- `get_analise_gargalos()` - Análise de gargalos por etapa
- `get_previsao_escoamento_fila()` - Quando fila será zerada

---

## FASE D: Dashboard de Gargalos ✅ IMPLEMENTADO

### D1. Dashboard de Produção ✅
**Rota:** `/industria/config/dashboard`
**Template:** `dashboard_producao.html`
**Menu:** Indústria > Dashboard Gargalos

**Visualizações Implementadas:**
1. ✅ **Timeline Gantt**: Barras horizontais por OP mostrando início até previsão
2. ✅ **Marcador de Progresso**: Círculo com % mostrando posição atual
3. ✅ **Cards Resumo**: Aguardando, Em Produção, Total, Atrasados
4. ✅ **Linha "AGORA"**: Linha vermelha vertical indicando momento atual
5. ✅ **Cores por Status**: Verde (ok), Amarelo (atenção), Vermelho (atrasado)

### D2. Indicadores ✅

| Indicador | Descrição |
|-----------|-----------|
| **Aguardando** | Qtd de lotes aguardando |
| **Em Produção** | Lotes sendo trabalhados |
| **Total** | Total de lotes ativos |
| **Atrasados** | OPs com data prevista ultrapassada |

### D3. Alertas Visuais ✅

- 🔴 **Atrasado**: Círculo vermelho pulsante + barra vermelha
- 🟠 **Atenção**: Círculo amarelo (menos de 24h para prazo)
- 🟢 **No Prazo**: Círculo verde + barra verde

---

## FASE E: Integração com Orçamentos 🔄 PENDENTE

### E1. Ao Criar/Editar Orçamento

1. Para cada item do orçamento:
   - Buscar `produtos_tempo_etapa` do produto
   - Somar tempos de todas as etapas
   - Multiplicar pela quantidade
   
2. Consultar fila atual de produção
   - Somar tempo estimado de tudo que está na frente
   
3. Calcular data de conclusão
   - Usar `adicionar_minutos_uteis()`
   
4. Calcular data de entrega
   - Conclusão + dias de transporte

### E2. Atualização em Tempo Real

- Quando lote avança de etapa → recalcular previsões
- Quando OP é concluída → recalcular previsões das próximas
- Job noturno para recálculo geral

---

## Estrutura de Arquivos

```
app/
├── routes/
│   └── config_producao_routes.py      # ✅ Rotas de configuração e APIs
├── services/
│   └── previsao_producao_service.py   # ✅ Serviço de cálculo (553 linhas)
├── templates/
│   └── industria/
│       ├── config_tempos_producao.html    # ✅ Tela tempos produto
│       ├── config_feriados.html           # ✅ Tela feriados
│       ├── config_capacidade_etapas.html  # ✅ Tela capacidade
│       └── dashboard_producao.html        # ❌ PENDENTE - Dashboard gargalos
└── scripts/
    └── 032_SISTEMA_PREVISAO_PRODUCAO.sql  # ✅ Script SQL completo
```

---

## APIs Disponíveis ✅

| Endpoint | Descrição |
|----------|-----------|
| `GET /industria/config/api/previsao/lote/<id>` | Previsão de um lote |
| `GET /industria/config/api/previsao/op/<id>` | Previsão de uma OP |
| `GET /industria/config/api/previsao/orcamento/<id>` | Previsão para orçamento |
| `GET /industria/config/api/gargalos` | Análise de gargalos |

---

## Status de Implementação (Atualizado: 26/12/2025 12:23)

### ✅ FASES CONCLUÍDAS

| Fase | Descrição | Status |
|------|-----------|--------|
| **A1** | Jornada de trabalho (módulo existente) | ✅ |
| **A2** | Tabela `produtos_tempo_etapa` | ✅ |
| **A3** | Tabela `config_feriados` + dados 2025/2026 | ✅ |
| **A4** | Tabela `config_capacidade_etapa` | ✅ |
| **A5** | Tabela `log_calculo_previsao` | ✅ |
| **A6** | Views de fila e resumo | ✅ |
| **A7** | Funções SQL | ✅ |
| **A8** | Stored procedure histórico | ✅ |
| **B1** | Config jornada (módulo existente) | ✅ |
| **B2** | Tela config tempos | ✅ |
| **B3** | Tela config feriados | ✅ |
| **B4** | Tela config capacidade | ✅ |
| **C1-C5** | Funções de cálculo (service Python) | ✅ |
| **D1** | Dashboard Timeline Gantt | ✅ |
| **D2** | Indicadores visuais | ✅ |
| **D3** | Cores por status (ok/atenção/atrasado) | ✅ |

### ✅ FASE E - Integração com Orçamentos (IMPLEMENTADA 26/12/2025)

| Item | Descrição | Status |
|------|-----------|--------|
| **E1** | API `/api/previsao/calcular` - cálculo em tempo real | ✅ |
| **E2** | Botão "Calcular" no formulário de orçamento | ✅ |
| **E3** | JavaScript para chamar API e preencher campos | ✅ |
| **E4** | Cálculo automático de `data_prevista` ao criar OP | ✅ |

---

## O QUE JÁ PODE TESTAR

### Scripts SQL (executar se ainda não fez)
```sql
SOURCE app/scripts/032_SISTEMA_PREVISAO_PRODUCAO.sql;
SOURCE app/scripts/033_RESET_JORNADA_PADRAO_8H.sql;
SOURCE app/scripts/035_FIX_COLUNAS_DATETIME.sql;
```

### URLs Disponíveis

| URL | Descrição |
|-----|-----------|
| `/industria/config/dashboard` | ✅ Dashboard Timeline Gantt |
| `/industria/config/tempos-producao` | ✅ Configurar tempos por produto |
| `/industria/config/feriados` | ✅ Configurar feriados |
| `/industria/config/capacidade-etapas` | ✅ Configurar capacidade |
| `/industria/jornada-trabalho` | ✅ Jornada de trabalho |

### Dashboard Timeline - O que mostra:
- **Cards resumo**: Aguardando, Em Produção, Total, Atrasados
- **Colunas de dias**: Ontem, HOJE, +1, +2, +3, +4
- **Linhas por OP**: Número + Produto (compactas, 28px)
- **Barra horizontal**: Do início até fim previsto
- **Círculo**: Posição atual (baseado no progresso %)
- **Cores**: Verde (ok), Amarelo (<24h), Vermelho (atrasado)
- **Linha vermelha**: Momento atual (AGORA)

### APIs de Previsão (já prontas):
```
GET /industria/config/api/previsao/lote/<id>
GET /industria/config/api/previsao/op/<id>
GET /industria/config/api/previsao/orcamento/<id>
GET /industria/config/api/gargalos
```

---

## FASE E - IMPLEMENTAÇÃO CONCLUÍDA

### O que foi implementado:

**E1. API de Cálculo em Tempo Real:**
- Endpoint: `POST /industria/config/api/previsao/calcular`
- Recebe lista de itens (produto_id, quantidade) + dias_transporte
- Retorna: previsão de produção, previsão de entrega, tempo estimado
- Considera: tempos por etapa, fila atual, jornada de trabalho

**E2. Formulário de Orçamento:**
- Botão "Calcular" na seção de Previsões
- Campo "Tempo Est." mostrando dias de produção
- JavaScript que chama a API e preenche automaticamente:
  - Data de Previsão de Produção
  - Data de Previsão de Entrega
- Checkbox "Manual" para desativar cálculo automático

**E3. Criação de OP:**
- Se `data_prevista` não for informada, calcula automaticamente
- Usa o serviço de previsão para estimar conclusão
- Considera tempo do produto × quantidade

**Arquivos Modificados:**
- `app/routes/config_producao_routes.py` - Nova API `/api/previsao/calcular`
- `app/templates/comercial/partials/_orcamento_tab_dados.html` - Botão Calcular
- `app/templates/comercial/orcamento_form.html` - Função JavaScript
- `app/routes/ordem_producao_routes.py` - Cálculo automático ao criar OP

---

---

## FASE F: Ficha Técnica Dinâmica ✅ IMPLEMENTADA (26/12/2025)

### F1. CRUD Completo de Fichas Técnicas ✅
**Rota:** `/produtos/fichas-tecnicas`
**Template:** `produtos/ficha_tecnica_*.html`
**Menu:** Produtos e Estoque > Fichas Técnicas

**Funcionalidades:**
- ✅ Listar fichas técnicas com filtros
- ✅ Criar nova ficha técnica
- ✅ Editar ficha técnica existente
- ✅ Visualizar ficha técnica detalhada
- ✅ Duplicar ficha técnica
- ✅ Excluir ficha técnica

### F2. Composição da Ficha Técnica ✅
Cada ficha técnica contém 3 tipos de itens:

| Tipo | Descrição |
|------|-----------|
| **Serviço** | Mão de obra / tempo de produção |
| **Matéria-Prima** | Insumos principais do produto |
| **Consumo Interno** | Materiais auxiliares (cola, adesivos, etc) |

### F3. Histórico de Produção Dinâmico ✅
**Seção na visualização/edição da ficha técnica:**

- ✅ **Cards Resumo**: Total OPs, Unidades Produzidas, Tempo Total, Tempo/Unidade
- ✅ **Tabela Tempo por Etapa**: Mínimo, Médio, Máximo de cada etapa
- ✅ **Lista Últimas 10 OPs**: Com link para visualização da OP
- ✅ **Cálculo Automático**: Tempo por unidade = Tempo Total / Quantidade Produzida

### F4. Atualização com Tempo Real ✅
**Botão "Atualizar Ficha com Tempo Real":**

1. Calcula tempo médio por unidade das últimas 10 OPs concluídas
2. Atualiza campo `tempo_producao_horas` da ficha técnica
3. Sincroniza item de serviço principal com o tempo calculado
4. Recalcula custo total automaticamente
5. Registra observação com data/hora da atualização

**API:** `POST /produtos/fichas-tecnicas/<id>/atualizar-tempo-real`

### F5. Arquivos Criados/Modificados ✅

| Arquivo | Descrição |
|---------|-----------|
| `app/routes/ficha_tecnica_routes.py` | Blueprint completo com CRUD + API |
| `app/templates/produtos/ficha_tecnica_lista.html` | Lista de fichas |
| `app/templates/produtos/ficha_tecnica_form.html` | Formulário criar/editar |
| `app/templates/produtos/ficha_tecnica_view.html` | Visualização detalhada |
| `app/main_mysql.py` | Registro do blueprint |
| `app/templates/base.html` | Menu "Fichas Técnicas" |

### F6. Script de Teste ✅
**Arquivo:** `app/scripts/045_TESTE_FICHA_TECNICA_HISTORICO.sql`

Cenário completo de teste com:
- 10 orçamentos aprovados
- 10 OPs concluídas com tempos variados
- 10 lotes com status concluído
- 140 logs de etapas (14 por OP)
- Template completo com serviço, matéria-prima e consumo interno

---

## FASE G: Comparativo Custo Template vs Real 🆕 NOVA FUNCIONALIDADE

### G1. Objetivo
Comparar o custo previsto na ficha técnica com o custo real apurado após produção.

### G2. Funcionalidades Planejadas

| Item | Descrição | Status |
|------|-----------|--------|
| **G1** | Calcular custo real da OP (tempo × custo hora) | 🔄 Pendente |
| **G2** | Mostrar variação % entre template e real | 🔄 Pendente |
| **G3** | Alertar quando variação > 15% | 🔄 Pendente |
| **G4** | Gráfico histórico de variação | 🔄 Pendente |
| **G5** | Sugestão automática de ajuste no template | 🔄 Pendente |

### G3. Campos a Adicionar

```sql
-- Na tabela ordens_producao
ALTER TABLE ordens_producao ADD COLUMN custo_template DECIMAL(15,2);
ALTER TABLE ordens_producao ADD COLUMN custo_real DECIMAL(15,2);
ALTER TABLE ordens_producao ADD COLUMN variacao_custo_percent DECIMAL(5,2);

-- View comparativa
CREATE VIEW vw_comparativo_custos AS
SELECT 
    op.id,
    op.numero_op,
    p.name as produto,
    op.quantidade,
    op.custo_template,
    op.custo_real,
    op.variacao_custo_percent,
    CASE 
        WHEN ABS(op.variacao_custo_percent) > 15 THEN 'ALERTA'
        WHEN ABS(op.variacao_custo_percent) > 10 THEN 'ATENÇÃO'
        ELSE 'OK'
    END as status_variacao
FROM ordens_producao op
JOIN products p ON p.id = op.produto_id
WHERE op.status = 'concluida';
```

---

## SISTEMA COMPLETO - TODAS AS FASES

| Fase | Descrição | Status |
|------|-----------|--------|
| **A** | Estrutura de Dados Base | ✅ Concluída |
| **B** | Telas de Administração | ✅ Concluída |
| **C** | Cálculo de Previsão | ✅ Concluída |
| **D** | Dashboard de Gargalos | ✅ Concluída |
| **E** | Integração com Orçamentos | ✅ Concluída |
| **F** | Ficha Técnica Dinâmica | ✅ Concluída |
| **G** | Comparativo Custo Template vs Real | 🆕 Nova |

O Sistema de Previsão de Produção está **100% implementado** com as fases A-F:
- ✅ Estrutura de dados
- ✅ Telas de administração
- ✅ Serviço de cálculo
- ✅ Dashboard Timeline Gantt
- ✅ Integração com Orçamentos
- ✅ **Ficha Técnica Dinâmica com Histórico de Produção**

---

## URLs Completas do Sistema

| URL | Descrição |
|-----|-----------|
| `/industria/config/dashboard` | Dashboard Timeline Gantt |
| `/industria/config/tempos-producao` | Configurar tempos por produto |
| `/industria/config/feriados` | Configurar feriados |
| `/industria/config/capacidade-etapas` | Configurar capacidade |
| `/industria/jornada-trabalho` | Jornada de trabalho |
| `/produtos/fichas-tecnicas` | **Lista de Fichas Técnicas** |
| `/produtos/fichas-tecnicas/novo` | **Criar Ficha Técnica** |
| `/produtos/fichas-tecnicas/<id>` | **Visualizar Ficha Técnica** |
| `/produtos/fichas-tecnicas/<id>/editar` | **Editar Ficha Técnica** |

---

**Última Atualização:** 26/12/2025 18:00
