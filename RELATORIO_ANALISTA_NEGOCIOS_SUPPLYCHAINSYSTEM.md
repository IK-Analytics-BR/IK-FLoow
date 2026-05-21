# Relatório de Análise de Negócios – SupplyChainSystem

## 1. Contexto Geral do Sistema

O **SupplyChainSystem** é um sistema de gestão voltado para **cadeia de suprimentos industrial**, com foco em:

- Controle de **compras, estoque e financeiro**.
- Gestão de **manutenção de ativos (CMMS)** com planos, ordens de serviço e alertas.
- Apoio à **produção industrial** (previsão de produção, jornada de trabalho, capacidade por etapa, fichas técnicas).
- **Vendas e distribuição**, incluindo rotas de vendas, romaneios e um **PDV profissional** integrado ao financeiro e ao estoque.
- Em evolução, um módulo avançado de **DNA de Produto para correias industriais** e um sistema inteligente de **previsão de produção** já implementado.

O banco de dados central é o **MySQL** (schema `supply_chain_system`), com todos os módulos compartilhando a mesma base.

---

## 2. Visão por Módulo (Negócio)

### 2.1 Módulo Financeiro

- **Contas bancárias** (`bank_accounts`).
- **Contas a pagar** (`accounts_payable`) integradas a pedidos de compra e notas fiscais.
- **Contas a receber** (`accounts_receivable`) integradas a vendas e PDV.
- **Fluxo de caixa** (`cash_flow`) consolidando entradas e saídas.
- Integração com **transações financeiras** geradas pelo PDV e faturamento.

**Benefício de negócio:** consolida visão de caixa, compromissos e recebimentos em um único lugar, conectado à operação (compras/vendas).

#### Entradas (Inputs)

- Lançamentos provenientes de **pedidos de compra** e **notas fiscais de entrada**.
- Lançamentos provenientes de **vendas**, **PDV** e **notas fiscais de saída**.
- Cadastros manuais de **transações financeiras**, ajustes de saldo e conciliações.

#### Saídas (Outputs)

- Agenda de **contas a pagar** (por fornecedor, vencimento, centro de custo).
- Agenda de **contas a receber** (por cliente, documento, situação de cobrança).
- **Fluxo de caixa projetado** por período.
- Relatórios financeiros consolidados (entrada, saída, saldo por conta).

#### Atores Envolvidos

- **Financeiro** (tesouraria / contas a pagar / contas a receber).
- **Controladoria** (análise de resultado e centros de custo).
- **Diretoria** (acompanhamento de fluxo de caixa e endividamento).

#### Principais Telas / Rotas (alta visão)

- Listagem e cadastro de **contas a pagar** e **contas a receber**.
- Tela de **contas bancárias** e **conciliação**.
- Tela de **fluxo de caixa** diário e projetado.

#### Fluxo Típico (Passo a Passo)

1. Pedidos de compra e vendas são aprovados e geram **títulos financeiros**.
2. No financeiro, os títulos são revisados, categorizados e, se necessário, ajustados.
3. Conforme os pagamentos/recebimentos ocorrem, o usuário registra a **baixa**.
4. O sistema atualiza automaticamente o **fluxo de caixa** e saldos bancários.
5. Relatórios são usados para acompanhar **inadimplência**, **compromissos futuros** e **sobras de caixa**.

#### Riscos, Exceções e Pontos de Atenção

- Divergência entre **valores financeiros** e **documentos fiscais/operacionais** (compra/venda).
- Baixas registradas em contas erradas, distorcendo o fluxo de caixa.
- Falta de rotina de conciliação bancária sistemática.

#### Indicadores Sugeridos

- Saldo de **caixa e bancos** por dia/semana.
- **Prazo médio** de pagamento e recebimento.
- Percentual de **inadimplência**.
- **Projeção de caixa** (30/60/90 dias) vs saldo atual.

---

### 2.2 Módulo de Compras

- **Pedidos de compra** completos (`purchase_orders` e `purchase_order_items`):
  - Fornecedor, condições de pagamento, endereço de entrega.
  - Valores: subtotal, descontos, frete, seguro, impostos, total.
  - Status: rascunho, aprovado, recebido parcial, concluído, cancelado.
- **Recebimentos de compra** (`purchase_order_receipts` e `purchase_order_receipt_items`):
  - Controle de lote, validade, local de armazenamento.
- **Notas fiscais de entrada** (`invoices`, `invoice_items`) com importação de XML de NF-e.
- Integração com **estoque** (atualização automática na entrada) e **financeiro** (geração de contas a pagar).

**Fluxos de negócio atendidos:** aquisição de insumos/produtos para revenda, reposição de estoque e integração fiscal/financeira.

#### Entradas (Inputs)

- Requisições internas de compra (necessidade gerada por estoque, produção ou manutenção).
- Informações de **fornecedores**, condições de pagamento e prazos de entrega.
- **XML de NF-e** de entrada e dados de recebimento físico (quantidade, lote, validade).

#### Saídas (Outputs)

- **Pedidos de compra** aprovados, com todos os dados comerciais e logísticos.
- **Posição de recebimento** (o que foi entregue, pendente, atrasado).
- Geração de **títulos a pagar** e impactos no planejamento de caixa.

#### Atores Envolvidos

- **Comprador** / Suprimentos.
- **Solicitantes internos** (produção, manutenção, almoxarifado, vendas).
- **Financeiro** (validação de condições, programação de pagamentos).

#### Principais Telas / Rotas (alta visão)

- Lista e formulário de **pedidos de compra**.
- Tela de **recebimento de mercadorias** e conferência com NF-e.
- Consulta de **histórico de compras** por fornecedor/produto.

#### Exemplo de Fluxo Real (Passo a Passo)

1. Almoxarifado identifica item abaixo do **estoque mínimo** ou produção gera necessidade.
2. Comprador registra **pedido de compra** com fornecedor, preços, prazos e condições.
3. Na chegada da mercadoria, o almoxarifado registra o **recebimento** e confere com a NF-e.
4. O sistema atualiza o **estoque** e gera **contas a pagar**.
5. O financeiro programa os pagamentos de acordo com as condições negociadas.

#### Riscos, Exceções e Pontos de Atenção

- Diferenças entre **pedido** e **NF-e** (quantidade, preço, impostos).
- Recebimento físico sem registrar no sistema, gerando **estoque fantasma**.
- Compras emergenciais fora do fluxo padrão (não aprovadas/registradas).

#### Indicadores Sugeridos

- **Lead time médio** de fornecimento por fornecedor.
- Percentual de **atraso de entrega**.
- Percentual de **diferença entre pedido e recebimento** (quantidade/valor).
- **Participação de compras emergenciais** no total.

---

### 2.3 Módulo de Estoque

- **Posição de estoque atual** (`current_stock`).
- **Movimentações de estoque** (`stock_movements`): entradas, saídas, transferências, ajustes.
- **Locais de estoque** (`stock_locations`) e inventários físicos (`inventory_counts`).
- Integração com:
  - Compras (entrada por recebimento de pedidos/nota fiscal).
  - Vendas/PDV (baixa na saída).
  - CMMS (baixa de insumos/peças via ordens de serviço).

**Benefício:** visibilidade de materiais, insumos e produtos acabados, base para decisões de compra e atendimento de pedidos.

#### Entradas (Inputs)

- Movimentações originadas de **recebimentos** (compras, devoluções).
- Movimentações de **saída** (vendas, consumo em produção, manutenção, perdas).
- **Ajustes** de inventário (contagens físicas, correções de erros).

#### Saídas (Outputs)

- **Posição de estoque** por produto/local/lote.
- Históricos de **movimentações** (Kardex).
- Sinais de **estoque mínimo/máximo** para acionar compras.

#### Atores Envolvidos

- **Almoxarifado / Estoquista**.
- **Produção** (quando retira e devolve materiais).
- **Manutenção** (uso de peças de reposição).
- **Comercial/PDV** (baixas por vendas).

#### Principais Telas / Rotas (alta visão)

- Tela de **posição de estoque**.
- Tela de **movimentações** (entradas/saídas/transferências/ajustes).
- Telas de **inventário físico**.

#### Fluxo Típico de Reposição

1. Sistema identifica itens abaixo do **estoque mínimo**.
2. Compras é acionado para gerar **pedido de compra**.
3. Ao receber a mercadoria, o almoxarifado registra a **entrada** com lote/validade.
4. A partir daí, as saídas são lançadas (vendas, produção, manutenção) e o saldo é atualizado.

#### Riscos, Exceções e Pontos de Atenção

- Movimentações **não registradas** (uso real sem baixa no sistema).
- Duplicidade de cadastros de produtos ou unidades de medida inconsistentes.
- Falta de rastreio de **lotes/validades** em indústrias sensíveis (alimentos, químicos, farmacêuticos).

#### Indicadores Sugeridos

- **Giro de estoque** por família de produto.
- **Cobertura de estoque** (dias de estoque) para itens críticos.
- Percentual de **rupturas** (faltas) por período.
- Valor de estoque total e por categoria.

---

### 2.4 Usuários e Permissões

- Cadastro de **usuários**, permissões e logs de atividades (`users`, `permissions`, `user_permissions`, `activity_logs`).
- Possibilidade de **perfis distintos** (admin, usuários operacionais, etc.).

**Ponto de negócio:** permite separar responsabilidades por área (compras, financeiro, indústria, vendas, manutenção).

#### Entradas (Inputs)

- Dados cadastrais de usuários (nome, e-mail, login, role).
- Definição de **perfis e permissões** por módulo/ação.

#### Saídas (Outputs)

- Lista de usuários com perfis e status (ativo/inativo).
- **Logs de atividade** para auditoria básica.

#### Atores Envolvidos

- **Administrador do sistema / TI interna**.
- Em alguns casos, **gestores de área** (aprovam acessos específicos).

#### Principais Telas / Rotas (alta visão)

- Tela de **cadastro de usuários**.
- Tela de **permissões** por módulo/tela/ação.
- Relatórios simples de **log de acesso/atividade**.

#### Riscos e Pontos de Atenção

- Usuários com permissões **acima da necessidade** (risco de fraudes ou erros graves).
- Falta de política de **desativação** rápida quando alguém sai da empresa.

#### Indicadores Sugeridos

- Número de usuários **ativos** por área/módulo.
- Quantidade de **eventos críticos** (exclusões, alterações de cadastro financeiro) por usuário.

---

### 2.5 Módulo de Manutenção de Ativos (CMMS)

- **Equipamentos** (`equipment`) vinculados a clientes/plantas.
- **Planos de manutenção** (`maintenance_plans`) por equipamento/insumo:
  - Gatilhos por tempo (dias) ou horas de operação.
- **Ordens de serviço** (`service_orders`, `service_order_items`, `service_order_labor`):
  - Abertura manual ou a partir de planos.
  - Itens (peças/insumos), horas de técnico, custo total.
- **Horímetro** (`hour_meter_readings`) para controle de uso.
- **Técnicos** (`technicians`) com especialidades e horas registradas.
- **Alertas** (`alerts`) gerados por desgaste, estoque baixo, manutenção programada, abertura/atribuição/conclusão de OS.

**Fluxo típico:**

1. Cadastra-se equipamento + plano de manutenção.
2. Leituras de horímetro e/ou data disparam **alertas**.
3. Gera-se **ordem de serviço** com técnico, peças e tempo estimado.
4. Após execução, registra-se mão de obra, consumo de peças e tempo de parada.
5. Painéis e relatórios podem analisar custos de manutenção, disponibilidade e desempenho.

#### Entradas (Inputs)

- Cadastro de **equipamentos**, localização, criticidade e histórico.
- **Planos de manutenção** preventivos (por tempo/horas) e corretivos.
- Leituras de **horímetro** e eventos de falha.

#### Saídas (Outputs)

- Lista de **ordens de serviço** abertas, em andamento e concluídas.
- Histórico de manutenção por equipamento (custos, tempo de parada, tipo de manutenção).
- **Alertas** de manutenção pendente, desgaste e estoque baixo de peças.

#### Atores Envolvidos

- **Gestor de Manutenção**.
- **Planejador de Manutenção** (em empresas maiores, pode ser diferente do gestor).
- **Técnicos de manutenção** (campo e/ou fábrica).
- **Almoxarifado** (suprimento de peças).

#### Principais Telas / Rotas (alta visão)

- Cadastro de **equipamentos** e planos de manutenção.
- Lista e formulário de **ordens de serviço**.
- Tela de **horímetro**.
- Tela/listas de **alertas**.

#### Casos de Uso por Persona

- **Gestor de Manutenção**:
  - Visualiza backlog de OS por criticidade e área.
  - Analisa equipamentos com maior custo de manutenção.
  - Revisa planos de manutenção preventivos.
- **Técnico de Manutenção**:
  - Recebe lista de OS atribuídas.
  - Registra início/fim de execução, materiais usados e horas trabalhadas.
  - Alimenta observações técnicas para histórico.

#### Cenário 1 – Parada Crítica de Equipamento

1. Equipamento crítico falha inesperadamente (parada de produção).
2. Técnico ou gestor registra **OS corretiva de emergência** no sistema.
3. O sistema sinaliza **criticidade** e, se configurado, gera alerta para gestores.
4. Técnico executa intervenção e registra **tempo de parada** e causa raiz.
5. Posteriormente, gestor avalia se é necessário **ajustar plano preventivo** (aumentar frequência, incluir inspeções específicas).

#### Cenário 2 – Falta de Peça em Manutenção

1. Ao abrir/atender uma OS, técnico identifica que a peça necessária está **sem estoque**.
2. O registro de OS informa o componente e o sistema pode disparar **alerta de estoque baixo**.
3. Compras é acionado para gerar pedido; manutenção decide se a OS será aguardada ou se aplica solução paliativa.

#### Riscos, Exceções e Pontos de Atenção

- OS resolvidas "por fora" sem registro, quebrando o histórico.
- Falta de padronização na classificação de **falhas e causas**.
- Planos de manutenção não revisados periodicamente, gerando excesso ou falta de intervenções.

#### Indicadores Sugeridos

- Percentual de **manutenção preventiva** vs **corretiva**.
- **MTBF** (tempo médio entre falhas) por equipamento crítico.
- **MTTR** (tempo médio para reparo).
- Custo de manutenção por equipamento/linha de produção.

---

### 2.6 Módulo Técnicos

- Cadastro de técnicos, especialidades e **status ativo/inativo**.
- Atribuição a ordens de serviço.
- Registro de **horas trabalhadas** em cada OS.

**Valor:** permite enxergar produtividade, carga de trabalho e especializações críticas.

#### Entradas (Inputs)

- Dados cadastrais dos **técnicos** (nome, especialidade, carga horária, status).
- Informações de **alocação em OS** e horas apontadas.

#### Saídas (Outputs)

- Lista de técnicos com **status de carga** (OS em aberto, horas trabalhadas).
- Relatórios de **produtividade** (horas produtivas vs disponíveis).

#### Atores Envolvidos

- **Gestor de Manutenção**.
- **RH/Administrativo** (apoio em dados de jornada, se integrado).

#### Indicadores Sugeridos

- Horas trabalhadas por técnico por período.
- Quantidade de OS concluídas por técnico.
- Balanceamento de carga entre técnicos.

---

### 2.7 Módulo Comercial – Rotas, Romaneio e Vendas

- **Rotas de vendas** (`sales_routes`, `route_customer`) com frequência, vendedor responsável e ordem de visita.
- **Romaneio de vendas** (`romaneio_routes` e tabelas relacionadas) para planejar carregamento/entrega.
- **Vendas/Orçamentos** (`orcamento_routes`, `venda_routes`) conectados a clientes, produtos, preços e condições de pagamento.

**Benefício:** estrutura o trabalho do time comercial (campo e interno), ligando pedidos, entregas e rotas.

#### Entradas (Inputs)

- Cadastro de **clientes** e **vendedores**.
- Definição de **rotas de vendas** e frequência de visita.
- Pedidos/orçamentos registrados pelo time comercial.

#### Saídas (Outputs)

- Agenda de visitas por rota/vendedor.
- Romaneios de carregamento e entregas planejadas.
- Pedidos faturados/entregues por rota e período.

#### Atores Envolvidos

- **Vendedor externo** (rota).
- **Vendedor interno** / atendimento.
- **Supervisor Comercial**.
- **Logística/Expedição** (para romaneios).

#### Principais Telas / Rotas (alta visão)

- Cadastro e listagem de **rotas de vendas**.
- Cadastro de **romaneios** e vínculo com pedidos/clientes.
- Telas de **orçamentos** e **pedidos de venda**.

#### Exemplo de Fluxo Real – Rota de Vendas

1. Supervisor define **rota** com lista de clientes e ordem de visita.
2. Vendedor planeja o dia baseando-se na rota e romaneio de produtos.
3. Ao visitar clientes, registra **pedidos/orçamentos**.
4. Pedidos são enviados ao ERP, disparando **separação de mercadorias** e expedição.
5. Entregas são associadas ao romaneio e posteriormente faturadas.

#### Riscos e Pontos de Atenção

- Rotas desatualizadas, com clientes que já não são ativos.
- Falta de feedback da expedição, gerando divergência entre **pedido entregue** e **planejado**.

#### Indicadores Sugeridos

- **Cobertura de rota** (quantos clientes da rota foram visitados).
- Taxa de conversão **visita → pedido**.
- Volume de vendas por rota/vendedor/período.

---

### 2.8 Módulo PDV Profissional

- Tela de **PDV moderno** (`/vendas/pdv`) para operação de balcão/loja.
- Controle de **caixa** (`cash_register`): abertura, fechamento e saldo.
- Venda com:
  - Múltiplas formas de pagamento por venda.
  - Descontos por item e totais.
  - Integração automática com **estoque** (baixa dos itens).
  - Integração com **financeiro** (contas a receber, fluxo de caixa, transações financeiras).
- Suporte a **múltiplas empresas** via tabela `empresas` + `pdv_settings` por empresa.

**Fluxo típico:** abertura de caixa → operação de vendas → emissão fiscal (NF-e/NFC-e) → integração financeira.

#### Entradas (Inputs)

- Cadastro de **empresas**, produtos, clientes e configurações do PDV.
- Abertura de **caixa** com saldo inicial.
- Itens adicionados ao **carrinho** (leitura por código/barras/nome).

#### Saídas (Outputs)

- **Vendas** registradas (sales, sale_items).
- Lançamentos em **contas a receber**, **fluxo de caixa** e transações financeiras.
- Documentos fiscais (NF-e/NFC-e), quando integrados.

#### Atores Envolvidos

- **Operador de PDV**.
- **Gerente de loja / responsável financeiro**.

#### Principais Telas / Rotas (alta visão)

- Tela principal do **PDV** (`/vendas/pdv`).
- Tela de **abertura/fechamento de caixa**.
- Telas de **configuração** do PDV (atalhos, políticas de desconto, etc.).

#### Exemplo de Fluxo Real – Venda no PDV

1. Operador realiza **login** e abre o **caixa**.
2. Cliente chega ao balcão; operador adiciona produtos ao carrinho.
3. Aplica descontos, se autorizado.
4. Seleciona formas de pagamento (uma ou múltiplas).
5. Conclui a venda; o sistema registra **baixa de estoque**, **títulos a receber** e **movimentação de caixa**.
6. Se configurado, emite documento fiscal correspondente.

#### Riscos e Pontos de Atenção

- Caixas abertos sem fechamento apropriado, dificultando **conciliação**.
- Descontos concedidos além das políticas definidas.

#### Indicadores Sugeridos

- Ticket médio por dia/operador.
- Volume de vendas por forma de pagamento.
- Diferença entre **saldo teórico de caixa** e **contagem física**.

---

### 2.9 Módulo Indústria – Produção e Previsão Inteligente

- **Jornada de trabalho** (`jornadas_trabalho`, `jornada_horarios`).
- **Feriados e dias não úteis** (`config_feriados`).
- **Capacidade por etapa de produção** (`config_capacidade_etapa`).
- **Tempos por produto/etapa** (`produtos_tempo_etapa`).
- **Ordens de produção** (`ordens_producao` e tabelas associadas).
- **Serviço de previsão de produção** (`previsao_producao_service.py`):
  - Calcula tempo restante de lotes/OPs.
  - Gera previsão de conclusão/entrega considerando jornada, fila e capacidade.
- **Dashboard de gargalos** (`/industria/config/dashboard`) com visão de timeline tipo Gantt.
- **Fichas técnicas dinâmicas** (`/produtos/fichas-tecnicas`) com composição de serviços, matérias-primas e consumos internos, alimentadas por histórico real de produção.

**Benefício:**

- Permite prometer prazos de entrega mais realistas.
- Dá visibilidade clara de gargalos e capacidade.
- Integra engenharia de produto (ficha técnica) com execução real (tempos e custos).

#### Entradas (Inputs)

- **Ordens de produção** (associadas a orçamentos e fichas técnicas).
- Cadastros de **jornadas de trabalho**, **feriados** e **capacidade por etapa**.
- Tempos de produção registrados historicamente por **etapa/produto**.

#### Saídas (Outputs)

- **Previsões de conclusão** de OPs, lotes e orçamentos.
- Dashboard de **gargalos** por etapa.
- Indicadores de **tempo estimado vs realizado**.

#### Atores Envolvidos

- **Planejador de Produção / PCP**.
- **Gestor Industrial / Produção**.
- **Engenharia de Produto** (fichas técnicas).

#### Casos de Uso por Persona

- **Planejador de Produção / PCP**:
  - Consulta a previsão de conclusão de novas OPs antes de prometer prazo ao cliente.
  - Ajusta a sequência de OPs para reduzir gargalos.
- **Gestor de Produção**:
  - Acompanha o dashboard de gargalos para decidir horas extras, terceirização ou replanejamento.
  - Analisa atrasos recorrentes em determinadas etapas.
- **Engenharia de Produto**:
  - Usa dados de **tempo real** (via fichas técnicas dinâmicas) para refinar o tempo padrão dos produtos.

#### Cenário 1 – Atraso de OP

1. Uma nova OP é criada com base em um orçamento aprovado.
2. O serviço de previsão calcula uma **data prevista de conclusão** considerando fila e capacidade.
3. No decorrer da produção, algumas etapas atrasam (paradas, retrabalhos).
4. O sistema recalcula a previsão; OP passa a aparecer como **atrasada** no dashboard.
5. PCP e gestor de produção avaliam ações corretivas (reordenação de fila, alocação de mais recursos, divisão de lotes).

#### Cenário 2 – Ajuste de Previsão por Mudança de Jornada

1. A empresa decide alterar a **jornada de trabalho** (incluir turno extra ou reduzir horas).
2. As configurações de jornada são atualizadas no módulo Indústria.
3. O serviço de previsão passa a considerar a nova disponibilidade de minutos úteis por dia.
4. As previsões de OPs em aberto são recalculadas, alterando prazos de entrega previstos.

#### Riscos, Exceções e Pontos de Atenção

- Dados de **tempo de produção** não alimentados corretamente, distorcendo médias.
- Jornada, feriados e capacidade desatualizados, gerando previsões irreais.

#### Indicadores Sugeridos

- Percentual de OPs entregues **no prazo** vs atrasadas.
- **Tempo médio de ciclo** (ordem de produção) por família de produto.
- Utilização de capacidade por etapa (gargalo xciência).

---

### 2.10 Módulo DNA de Produto – Correias Industriais (em evolução)

Com base no plano `PLANO_DNA_PRODUTO_CORREIAS.md`:

- Estrutura de **especificações técnicas detalhadas** de correias (`produto_especificacoes_tecnicas`).
- **Anexos** de desenho técnico, fotos, datasheets (`produto_anexos`).
- Regras de **matching** por DNA (`produto_matching_regras`) e processo de **derivação** de produtos (`produto_derivacoes`, `derivacao_etapas`).
- Integração planejada com orçamentos para sugerir produtos compatíveis em estoque.

**Valor de negócio esperado:** melhor aproveitamento de estoque, redução de perdas e capacidade de encontrar alternativas técnicas compatíveis rapidamente.

#### Entradas (Inputs)

- Dados técnicos das **correias** (dimensões, materiais, perfil, dureza, lonas, tipo de emenda, aplicação, normas).
- **Anexos** (desenhos técnicos, datasheets, certificações, fotos).

#### Saídas (Outputs)

- **Código DNA** de cada produto.
- Lista de **produtos compatíveis** (match exato, derivável, parcial) para um pedido.
- Registros de **derivação** (produto origem/destino/sobra).

#### Atores Envolvidos

- **Engenharia de Produto**.
- **Vendas técnicas** (que precisam propor alternativas ao cliente).
- **Planejamento de produção** (quando há derivação).

#### Exemplo de Fluxo Real (Futuro)

1. Vendedor lança um pedido de correia com determinadas especificações.
2. O sistema consulta o **DNA** e procura itens em estoque compatíveis.
3. Se encontrar produto **derivável**, sugere corte e gera fluxo de derivação (consumo do rolo maior e criação de novo item sobrante).
4. O vendedor decide usar o derivado ou produzir do zero, com impacto em prazo/custo.

#### Indicadores Sugeridos (Fase Madura)

- Percentual de pedidos atendidos com **match de estoque existente**.
- Redução de **perdas de material** por melhor aproveitamento.
- Tempo médio de resposta para propostas técnicas complexas.

---

## 3. Fluxos End-to-End Principais

### 3.1 Fluxo de Abastecimento (Compras → Estoque → Financeiro)

1. Identificação de necessidade (estoque mínimo, pedido de venda, planejamento de produção ou manutenção).
2. Criação de **pedido de compra** com condições comerciais.
3. Recebimento físico + conferência com **nota fiscal** (importação XML opcional).
4. Atualização automática do **estoque** (quantidade, lote, validade, localização).
5. Geração de **contas a pagar** e impactos no **fluxo de caixa**.

---

### 3.2 Fluxo de Venda / PDV (Comercial → Estoque → Fiscal → Financeiro)

1. Criação de orçamento/pedido ou venda direta via **PDV**.
2. Reserva/baixa de estoque dos produtos.
3. Emissão de **NF-e/NFC-e** (quando aplicável).
4. Geração de **contas a receber** e registros no **fluxo de caixa**.
5. Possibilidade de análise posterior por rota de vendas e romaneios.

---

### 3.3 Fluxo de Manutenção (CMMS)

1. Cadastro de **equipamentos** e **planos de manutenção** (por tempo/horas).
2. Registro de **leituras de horímetro**.
3. Geração de **alertas** e **ordens de serviço**.
4. Execução da OS (técnicos, materiais, horas, tempo de parada).
5. Atualização de **indicadores de manutenção** e custos.

---

### 3.4 Fluxo de Produção (Orçamento → OP → Execução → Entrega)

1. Aprovação de **orçamento** com itens de produção.
2. Geração de **ordem de produção** (OP) com base em ficha técnica.
3. Uso da **previsão de produção** para estimar conclusão considerando fila, jornada, capacidade.
4. Execução das etapas, registro de tempos e consumos reais.
5. Entrada de produto acabado em estoque e posterior expedição.

---

## 4. Pontos Fortes de Negócio

- **Visão integrada** de compras, estoque, produção, manutenção, vendas e financeiro.
- **CMMS robusto** com planos, horímetro, técnicos e alertas.
- **Módulo industrial avançado** com previsão de produção, jornada, capacidade e fichas técnicas dinâmicas.
- **PDV profissional** alinhado ao backoffice financeiro e fiscal.
- Conceito de **DNA de produto** para correias, alinhado à realidade de fabricantes/distribuidores industriais.

---

## 5. Lacunas e Riscos (Visão de Negócio)

- **Gestão da qualidade** ainda não aparece como módulo dedicado (não conformidades, inspeções, laudos por lote).
- **WMS avançado** (endereçamento, conferência por coletores, estratégias de picking) não está detalhado na documentação.
- **KPI executivos consolidados** (OTIF, OEE, giro de estoque, nível de serviço) dependem de relatórios e dashboards adicionais.
- O módulo de **DNA de Produto** ainda está em fase de plano e precisa ser concluído para gerar valor pleno.
- A **complexidade funcional** é alta; risco de adoção parcial se não houver treinamento e governança de processos.

---

## 6. Recomendações de Negócio

1. **Formalizar mapa de processos TO-BE** por macro-área:
   - Compras/Abastecimento.
   - Estoque/Logística.
   - Vendas/PDV/Rotas.
   - Manutenção (CMMS).
   - Produção (incluindo previsão e fichas técnicas).
2. **Definir indicadores-chave (KPIs)** e garantir que o sistema os suporte nativamente:
   - Nível de serviço, prazo médio de entrega, giro/ruptura de estoque, custo de manutenção por equipamento, aderência ao prazo de produção.
3. **Priorizar conclusão dos módulos estratégicos** já iniciados:
   - Sistema de previsão de produção (já implementado, focar em uso e calibração).
   - DNA de Produto para correias (implementar Fase 1–3 primeiro).
4. **Segmentar o uso por perfil de cliente** (distribuidora de insumos, fabricante, indústria de processo/discreta) utilizando o `APP_MODE` (`global`, `industrial`, `varejo`) para ligar/desligar módulos.
5. **Investir em treinamento e documentação** por área, usando o próprio controle de telas (IDs `SCRxxx`) para mapear responsabilidades, entradas, saídas e regras de negócio de cada tela.

Este relatório serve de base para os outros relatórios (funcional, produto, UX e evolução industrial), que detalham o mesmo sistema sob diferentes perspectivas.
