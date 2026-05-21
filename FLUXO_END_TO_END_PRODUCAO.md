# Fluxo End-to-End de Produção – Visão Macro e Cobertura no Sistema

Este documento consolida a visão de fluxo **end-to-end** da operação industrial e mapeia o que já está contemplado no **SupplyChainSystem** e o que ainda falta implementar.

---

## 1. Visão Macro do Fluxo (7 Etapas)

1. **Pedido Comercial (Input)**  
   - Entrada da demanda de produto final (cru, frito, embalado 1kg/400g).  
   - Quantidade em unidade, kg ou pacote.  
   - Semana de referência.  
   - **Sistema:** apenas registra a demanda, não produz nada aqui.

2. **Programação Semanal (substitui aba "PROG SEM")**  
   - Consolida tudo que será produzido na **semana seguinte**.  
   - Entidades: semana (data início/fim), produto, tipo de produção, quantidade planejada.  
   - Regras: sempre vinculada a uma semana, congela após aprovação, pode ter versões (v1, v2...).  
   - Aqui nasce o **Plano Mestre de Produção (PMP)**.

3. **Conversões e Explosão de Produção (MRP)**  
   - Lógica central hoje espalhada em fórmulas de planilha.  
   - Exemplo de explosão: Produto Final → Unidades Base → Kg Produzidos → Massa → Recheio.  
   - Tudo calculado automaticamente pelo sistema.  
   - Saídas: totais em unidades e kg, necessidade de massa, recheio, caldo, óleo, embalagem etc.  
   - Gera ordens internas (necessidades), ainda **não é produção executada**.

4. **Planejamento Diário**  
   - Define o que será produzido em **cada dia** da semana.  
   - Considera restrições: capacidade de massa, fritura, equipe, equipamentos.  
   - Regra crítica: **nem todo produto pode ser feito todo dia**.  
   - Objetivo: evitar gargalo antes de acontecer.

5. **Execução da Produção**  
   - Transforma planejamento em **Ordens de Produção (OP)**.  
   - Cada OP: produto, quantidade planejada, tipo (cru/frito), data.  
   - Etapas: massa, modelagem, fritura, congelamento, embalagem.

6. **Apontamento do Realizado**  
   - Substitui a coluna "REALIZADO" da planilha.  
   - Para cada OP: quantidade produzida, quebras, perdas, reprocesso, tempo real.  
   - Permite ver eficiência e corrigir desvios.

7. **Fechamento Semanal**  
   - Resultado da semana: Planejado x Produzido, sobra, falta, custo real, faturamento real.  
   - Gera relatórios gerenciais e alimenta ajuste da próxima programação.

---

## 2. Regras de Negócio (10 Regras)

1. **Produto não é receita**  
   - Produto final ≠ ficha técnica.  
   - Cada produto tem unidade base (un, kg), peso unitário e tipo de processamento.

2. **Conversão obrigatória e centralizada**  
   - Nenhuma tela calcula "na mão".  
   - Se tipo = 1kg → converter para unidades → converter para kg usando cadastro.  
   - Conversão vem sempre do **cadastro**, nunca do usuário.

3. **Programação é semanal e imutável após aprovação**  
   - Antes de aprovar: editável.  
   - Depois de aprovar: só ajustes com justificativa e histórico.

4. **Pedido ≠ Produção**  
   - Pedido é comercial.  
   - Produção é industrial.  
   - Sistema pode produzir diferente do pedido, se necessário.

5. **Explosão de insumo sempre parte do produto final**  
   - Nunca planejar massa "solta".  
   - Sempre: Produto → Massa → Recheio → Matéria-prima.

6. **Planejado ≠ Realizado (sempre)**  
   - Sistema deve aceitar diferença.  
   - Diferença gera perda, sobra, ajuste de estoque.

7. **Capacidade limita programação**  
   - Exemplo: fritadeira suporta 300 kg/dia → sistema não aceita 350 kg no mesmo dia.  
   - Excel hoje não impede isso; o sistema deve impedir.

8. **Tudo gera histórico**  
   - Nada é sobrescrito: programação, produção, conversão, ajustes.  
   - Sempre manter trilha de auditoria.

9. **Sistema funciona mesmo com zero**  
   - Produto não produzido = 0.  
   - Relatórios e cálculos nunca quebram com valores zerados.

10. **PROG SEM é entidade, não planilha**  
    - Deve virar tabela principal de programação semanal, relacionada a: semana, produto, tipo, quantidade, status.

---

## 3. Mapa de Cobertura – Etapas do Fluxo x Sistema Atual

Legenda de status:  
- ✅ Implementado  
- 🟡 Parcialmente implementado  
- ❌ Não implementado

### 3.1 Tabela – Etapas do Fluxo

| # | Etapa | Status atual | Como está hoje no sistema | Próximo passo sugerido |
|---|-------|--------------|---------------------------|-------------------------|
| 1 | Pedido Comercial | ✅ | Módulos de **Vendas / Orçamentos / PDV** já registram pedidos comerciais (`orcamentos`, `orcamento_itens`, PDV). Integração com produção via `orcamento_op_itens` e `ordens_producao`. | Criar visão específica de **demanda para produção** (filtro por semana, tipo de produto, status) que alimente diretamente a Programação Semanal. |
| 2 | Programação Semanal (PMP / PROG SEM) | 🟡 | Tela `/industria/ordem-producao/planejamento` + template `planejamento_producao_semana_v2.html` permitem **simulação** de quantidades planejadas por produto final, usando pacotes padrão de planejamento quando existentes. Não há tabela persistindo a programação semanal com status/versão. | Modelar tabelas `programacao_semanal` e `programacao_semanal_itens` com: semana referência, versão, status (rascunho/aprovado/fechado), vínculo a produtos e pacotes padrão. Adaptar a tela atual para salvar/abrir versões em vez de ser só simulação. |
| 3 | Conversões e Explosão de Produção (MRP) | ✅ (como cálculo) | Funções em `ordem_producao_routes.planejamento_producao_semana` já convertem **quantidade planejada de pacotes** → unidades, e depois usam `produto_templates_producao` + `produto_template_itens` para explodir MASSA, RECHEIO, EMPACOTAMENTO e matérias-primas. Há também integração com fichas técnicas e templates de produção. | Extrair essa lógica para um **serviço reutilizável** (ex.: `explosao_producao_service`) e usá-lo tanto no planejamento semanal quanto na geração de OPs e no planejamento diário. Centralizar conversões em um único ponto. |
| 4 | Planejamento Diário | ❌ | Não há hoje uma entidade/tela de plano diário que distribua a programação semanal por dia respeitando capacidade. Existem **configurações de capacidade** (`config_capacidade_etapas`) e previsão de produção (previsao_producao_service), mas não um plano diário estruturado. | Criar modelo `planejamento_diario` ligado à `programacao_semanal`, com distribuição por dia e uso das capacidades por etapa para validar/limitar carga. Tela tipo calendário/grade por dia x produto. |
| 5 | Execução da Produção | ✅ | Módulo de **Ordens de Produção** (`ordens_producao`, `op_lotes`, `producao_etapas`, `vw_ordens_producao_resumo`) já gerencia OPs, lotes, etapas e integra com estoque (quando configurado). Telas Gantt/Kanban (`/industria/ordem-producao/producao/gantt*`). | Conectar geração de OPs diretamente a partir do **Planejamento Diário**, mantendo vínculo para depois comparar Planejado x Realizado por dia/semana. |
| 6 | Apontamento do Realizado | ✅ | Lotes (`op_lotes`) armazenam quantidades, etapas, datas de início/fim, pausas (`producao_pausas`, `op_lotes_etapas_log`). Previsão de produção já consome esse histórico para tempos médios. | Padronizar campos de **quantidade planejada x realizada x perdas/reprocesso** por OP/lote, e criar telas simples de apontamento focadas na operação (input rápido). |
| 7 | Fechamento Semanal | 🟡 | Há dados de produção, tempos, consumo de insumos e previsão, mas **não há um fechamento consolidado por semana** com visão Planejado x Realizado, sobras/faltas, custo real e faturamento. Alguns relatórios financeiros/estoque cobrem partes disso. | Implementar um **relatório de Fechamento Semanal de Produção**, consumindo: programação semanal, OPs executadas, apontamentos de perdas, movimentos de estoque e faturamento. Salvar snapshots semanais para histórico. |

---

## 4. Mapa de Cobertura – Regras de Negócio

| Regra | Status atual | Como está hoje | Próximo passo sugerido |
|-------|--------------|----------------|------------------------|
| 1. Produto não é receita | ✅ | Estrutura separa `products` de `produto_templates_producao` e `produto_template_itens` (fichas técnicas). Produto final tem unidade base e templates definem insumos/processo. | Garantir que todas as telas de planejamento/execução usem **sempre** o template associado, nunca quantidade de insumo digitada "na mão". |
| 2. Conversão obrigatória e centralizada | 🟡 | Conversão de pacotes → unidades já é usada em `planejamento_producao_semana_v2` (via `produto_pacotes` com `unidades_por_pacote`). Explosão de ficha técnica parte da unidade base. Ainda há telas/relatórios onde conversão pode ser manual. | Criar camada de serviço (ex.: `conversao_unidades_service`) para: produto base ↔ kg ↔ pacote, e reutilizar em todas as rotas de produção/planejamento. Remover cálculos duplicados em templates. |
| 3. Programação semanal imutável após aprovação | ❌ | Não existe entidade de programação semanal com status; apenas simulação pontual. | Ao criar `programacao_semanal`, incluir campos `status` (rascunho/aprovada/fechada), usuário/data de aprovação e travar edição quando aprovada (somente ajustes com justificativa registrada em log). |
| 4. Pedido ≠ Produção | ✅ | Pedido comercial mora em módulos de vendas/orçamentos. Produção usa `ordens_producao`, ligando opcionalmente OP ↔ orçamento (`orcamento_op_itens`). Sistema já aceita produzir diferente do pedido. | Expor claramente nas telas de OP a diferença **Pedido x Produção**, com indicadores e possíveis motivos (ajuste de lote mínimo, capacidade etc.). |
| 5. Explosão parte do produto final | ✅ | Tanto no planejamento semanal quanto na criação de templates/OPs, a explosão sempre começa do **produto final** (`produto_templates_producao`). Massa/recheio são derivados, não planejados avulsos. | Formalizar essa regra em serviços/API e validar que nenhuma rota permita cadastrar consumo de massa/recheio sem vínculo a um produto final ou OP. |
| 6. Planejado ≠ Realizado | 🟡 | Estrutura de OPs e lotes já permite registrar quantidades reais diferentes das planejadas, pausas, reprocessos. Porém não há um painel consolidado Planejado x Realizado por semana/produto. | padronizar campos de planejamento (origem: programação semanal/diária) e construir relatórios e dashboards de **desvios** (quantidade, tempo, custo). |
| 7. Capacidade limita programação | 🟡 | Tabelas de capacidade (`config_capacidade_etapas`) e serviços de previsão já existem (PLANO_SISTEMA_PREVISAO_PRODUCAO). Mas a tela de programação semanal não impede excesso de carga. | Integrar `config_capacidade_etapas` ao novo **Planejamento Diário**: ao exceder capacidade de uma etapa/dia, bloquear gravação ou exigir justificativa explícita. |
| 8. Tudo gera histórico | 🟡 | Diversas tabelas de log já existem (`op_lotes_etapas_log`, `log_calculo_previsao`, `activity_logs`). Porém não há histórico de versões de programação semanal/diária, nem de ajustes de programação. | Ao criar entidades `programacao_semanal` e `planejamento_diario`, adicionar tabelas de log/versão (ex.: `programacao_semanal_historico`) com quem alterou, quando e quais campos. |
| 9. Sistema funciona com zero | ✅ | Diversos trechos de código usam `COALESCE`, `NULLIF` e tratam quantidades/custos zerados sem quebrar. Em planejamento de produção, produtos sem template ou sem quantidade entram com zero e são ignorados no cálculo. | Manter essa regra como requisito de teste: sempre que criar nova tela/relatório, validar comportamento com semana sem produção ou produtos com demanda zero. |
| 10. PROG SEM é entidade, não planilha | ❌ | Hoje a "PROG SEM" é apenas simulada em memória (POST da tela de planejamento semanal). Nenhuma tabela específica armazena programações com status/versão. | Modelar tabelas dedicadas para programação semanal (cabeçalho + itens) e migrar a lógica da tela de simulação para trabalhar em cima dessa entidade persistida.

---

## 5. Próximos Passos Recomendados

1. **Modelar Programação Semanal (PROG SEM como entidade)**  
   - Tabelas `programacao_semanal` (cabeçalho) e `programacao_semanal_itens` (linhas por produto/tipo).  
   - Campos-chave: semana (data início/fim), versão, status, usuário de criação/aprovação, vínculo opcional a pedidos comerciais consolidados.

2. **Criar Planejamento Diário baseado na Programação Semanal + Capacidade**  
   - Distribuir automaticamente a carga semanal por dia, respeitando `config_capacidade_etapas`.  
   - Interface para o planejador ajustar manualmente, com alertas de excesso de capacidade.

3. **Extrair Explosão/Conversão para um Serviço Central (MRP)**  
   - Serviço reutilizável para: pacotes → unidades → kg → insumos (massa, recheio, MP).  
   - Usar o mesmo serviço em: programação semanal, planejamento diário, geração de OPs e relatórios de consumo.

4. **Integrar Programação ↔ Execução ↔ Fechamento**  
   - Geração de OPs a partir do planejamento diário, mantendo vínculos fortes (chaves estrangeiras).  
   - Relatório de **Fechamento Semanal** consolidando Planejado x Realizado (quantidade, tempo, custo, faturamento).  
   - Uso desse fechamento como base para ajuste da próxima programação.

Este documento deve ser o ponto de referência para evoluir o módulo industrial em direção ao fluxo end-to-end descrito acima.
