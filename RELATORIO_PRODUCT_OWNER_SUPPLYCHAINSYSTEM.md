# Relatório – Visão de Produto (Product Owner / Product Manager)

## 1. Proposta de Valor do SupplyChainSystem

O **SupplyChainSystem** é um produto voltado para **indústrias e distribuidoras de insumos industriais**, oferecendo em uma única plataforma:

- **ERP transacional** (compras, estoque, financeiro, fiscal, usuários/permissões).
- **Operação comercial completa** (orçamentos, vendas, PDV profissional, rotas de vendas, romaneio).
- **Módulo industrial avançado** (previsão de produção, gargalos, fichas técnicas dinâmicas, jornada, capacidade).
- **CMMS** (manutenção de ativos com planos, OS, horímetro, técnicos, alertas e notificações).
- Roadmap em andamento para **DNA de produto de correias** e **comparação de custo template vs real da produção**.

Posicionamento: **plataforma especialista para indústria/distribuição de médio porte**, com foco em rastreabilidade técnica e visão integrada de operação + financeiro.

---

## 2. Segmentos e Personas Atendidas

### 2.1 Segmentos

- Distribuidoras de **correias, rolamentos, componentes industriais**.
- Fabricantes que possuem **produção sob encomenda** e precisam prometer prazos (produção + expedição).
- Indústrias que precisam de **manutenção estruturada** em campo ou dentro da planta (CMMS).
- Operações com ponto de venda físico para **varejo técnico / balcão industrial** (PDV Profissional).

### 2.2 Personas Principais

- **Diretor Industrial / de Operações** – quer previsibilidade de produção e prazos.
- **Planejador de Produção** – usa o módulo de previsões, capacidade e dashboard de gargalos.
- **Gestor de Manutenção** – usa CMMS (planos, OS, horímetro, alertas, técnicos).
- **Gestor Comercial** – usa orçamentos, vendas, rotas, romaneios e PDV.
- **Gestor Financeiro** – usa contas a pagar/receber, bancos, fluxo de caixa, NFe/NFCe.
- **Engenharia de Produto** – usa fichas técnicas, DNA de produto, anexos técnicos.

---

## 3. Mapa de Funcionalidades (Backbone de Produto)

### 3.1 Já Entregue e Estável

- **Financeiro**: contas a pagar/receber, bancos, fluxo de caixa, plano de contas.
- **Compras**: pedidos completos, recebimento, integração com estoque e financeiro.
- **Estoque**: saldo atual, movimentos, inventários, Kardex.
- **Fiscal**: NFe/NFCe (emissão, importação, validação, DANFE/DANFCE, certificado digital, SEFAZ).
- **Usuários e Permissões**: controle de acesso por role, auditoria básica.

### 3.2 Módulos Avançados já Implementados

- **CMMS**: equipamentos, planos de manutenção, OS, horímetro, técnicos, alerts + `NotificationService`.
- **Indústria – Previsão de Produção** (segundo `PLANO_SISTEMA_PREVISAO_PRODUCAO.md`):
  - Estrutura de dados (jornadas, feriados, capacidade, tempos por produto/etapa, views, SPs).
  - Serviço Python `previsao_producao_service.py` completo.
  - Telas de configuração (`/industria/config/...`), dashboard de gargalos e integração com orçamentos/OPs.
- **Fichas Técnicas Dinâmicas**:
  - CRUD completo de fichas.
  - Histórico de produção e tempos reais alimentando o template.

### 3.3 Diferenciais Competitivos

- **Previsão de produção em profundidade**, com cálculo de datas considerando fila, capacidade, feriados e jornada.
- **CMMS integrado** ao restante do ERP (compras, estoque, técnicos, alertas).
- **PDV profissional** com forte integração fiscal/financeira e recursos avançados.
- **Visão futura de DNA de produto** para correias industriais, com matching e derivação.

---

## 4. Métricas de Produto Desejadas

Para gerir o produto, recomenda-se acompanhar:

- **Adoção por módulo** (número de empresas/usuários usando cada módulo).
- **Frequência de uso**: sessões/dia nos módulos chave (produção, manutenção, PDV, financeiro).
- **Tempo de ciclo**:
  - Cotação → Pedido → Entrega.
  - Abertura → Conclusão de OS de manutenção.
  - Criação → Conclusão de OP.
- **Indicadores de valor**:
  - Redução de atrasos de produção (via módulo de previsão).
  - Diminuição de rupturas de estoque.
  - Uso do CMMS (percentual de manutenções planejadas vs corretivas).

Implementar telemetria mínima (logs de uso por rota/tela) faz parte do roadmap de produto.

---

## 5. Roadmap Proposto

### 5.1 Curto Prazo (0–3 meses)

- Consolidar **uso dos módulos já entregues**:
  - Guias de implantação por pacote (Financeiro+Compras+Estoque, CMMS, Indústria, PDV).
  - Checklists de configuração mínima.
- Refinar **dashboard de produção** com feedback de clientes piloto.
- Melhorar **experiência do PDV** (atalhos, performance, logs e debug mais claros).

### 5.2 Médio Prazo (3–9 meses)

- **DNA de Produto – Fase 1 e 2**:
  - Implementar `produto_especificacoes_tecnicas` + `produto_anexos` na interface de produto.
  - Gerar código DNA automaticamente e permitir consulta/matching inicial.
- **Qualidade básica integrada** à produção e manutenção:
  - Registro simples de não conformidades (produto/OP/equipamento).
  - Vincular NCs a lotes, OPs e equipamentos.
- **KPIs industriais básicos**:
  - Painel com OPs atrasadas, tempo médio de ciclo, lead time promessa vs entrega.

### 5.3 Longo Prazo (9–18 meses)

- **DNA de Produto – Fases 3 e 4**:
  - Implementar matching derivável e fluxo de derivação de produtos em produção.
- **Comparativo de custo template vs real** (Fase G do plano de previsão):
  - Cálculo de custo real por OP.
  - Variações (%), alertas e sugestões de ajuste de ficha técnica.
- **WMS leve**:
  - Endereçamento simples, conferência básica, suporte a coletores/QR.
- **Camada de BI/Analytics**:
  - Views consolidadas e integração com ferramentas externas (Power BI, Metabase, etc.).

---

## 6. Estratégia de Go-to-Market por Pacotes

Recomendação de empacotamento para venda/implantação:

1. **Pacote Essencial ERP**  
   Finanças + Compras + Estoque + Fiscal + Usuários.

2. **Pacote CMMS**  
   Equipamentos + Planos + OS + Horímetro + Técnicos + Alertas.

3. **Pacote Indústria**  
   Previsão de Produção + OP + Fichas Técnicas Dinâmicas + Dashboard de Gargalos.

4. **Pacote Comercial Avançado**  
   Orçamentos + Rotas + Romaneio + PDV Profissional.

5. **Pacote Inteligência de Produto (Correias)**  
   DNA de Produto + Matching + Derivação + anexos técnicos.

Essa segmentação permite **vender e implantar de forma incremental**, reduzindo risco e acelerando o time-to-value.

---

## 7. Principais Riscos de Produto

- **Complexidade funcional alta**: risco de baixa adoção se não houver guias e onboarding forte.
- **Dependência de infraestrutura fiscal (SEFAZ, certificados)** para NFe/NFCe.
- **Módulos avançados pouco explorados** (previsão, fichas técnicas dinâmicas, DNA): exigem clientes mais maduros.

Mitigações sugeridas:

- Criar **“modos de operação”** via `APP_MODE` (apenas backoffice, backoffice+CMMS, completo industrial) para simplificar interface.
- Investir em **templates de configuração rápida** (ex.: jornada padrão 8h, capacidade default, exemplos de fichas técnicas).
- Construir **documentação de negócio** por módulo alinhada à tabela `screen_documentation`.

Este relatório deve orientar decisões de priorização e posicionamento do SupplyChainSystem nos próximos ciclos de produto.
