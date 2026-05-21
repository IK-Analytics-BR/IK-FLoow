# Relatório – Analista de Sistemas / Consultor Funcional ERP

## 1. Arquitetura Funcional Geral

- Backend em **Flask** (`app/main_mysql.py`) com múltiplos **blueprints** por módulo.
- Banco de dados **MySQL 8** usando o schema único `supply_chain_system`.
- Scripts de criação e verificação de estrutura em `app/scripts/` (`create_database.py`, `verify_all_database_tables.py`, scripts SQL específicos como `032_SISTEMA_PREVISAO_PRODUCAO.sql`).
- Conexão centralizada em `app/database.py` (classe `Database` + `get_db()`), usando autocommit e reconexão resiliente.
- Organização por domínio:
  - `routes/*.py` – rotas HTTP e lógica de aplicação.
  - `services/*.py` – serviços de negócio (previsão produção, NFe, NFCe, notificações, integração, etc.).
  - `templates/` – telas HTML organizadas por módulo.
  - `static/` – assets front-end (CSS, JS, imagens).

---

## 2. Mapeamento Módulo → Tabelas Principais

### 2.1 Financeiro

- `bank_accounts` – contas bancárias.
- `accounts_payable` – contas a pagar.
- `accounts_receivable` – contas a receber (integra PDV, vendas e faturamento).
- `cash_flow` – fluxo de caixa consolidado.
- `financial_transactions` – granularidade de lançamentos.
- Rotas principais:
  - `routes.bank_account_routes`.
  - `routes.accounts_payable_routes`.
  - `routes.accounts_receivable_routes`.
  - `routes.cash_flow_routes`.
  - `routes.chart_of_accounts_routes`.
  - `routes.payment_config_routes`.

### 2.2 Compras e Fiscal de Entrada

- `purchase_orders`, `purchase_order_items`, `purchase_order_receipts`, `purchase_order_receipt_items`.
- `payment_terms`, `payment_methods` – condições e meios de pagamento.
- `invoices`, `invoice_items` – notas fiscais de entrada.
- Integração com NFe:
  - `routes.importar_nfe`, `routes.importar_nfe_entrada`, `routes.importar_nfe_upload`.
  - Serviços `nfe_service.py`, `validador_xsd.py`, `sefaz_service.py`, `sefaz_webservices.py`, `nfe_xml_builder.py`.
- Rotas de compras: `routes.purchase_order_routes_fixed` (+ variantes `*_new`, `*_simple`, `*_integrated`).

### 2.3 Estoque

- Tabelas principais (conforme README):
  - `stock_locations` – locais físicos.
  - `current_stock` – saldos atuais.
  - `stock_movements` – movimentações (entrada/saída/transferência/ajuste).
  - `inventory_counts` – inventários físicos.
- Rotas:
  - `routes.inventory_routes`.
  - `routes.kardex_routes`.
- Integrações funcionais:
  - Baixas por PDV (`pdv_profissional_routes`), vendas (`venda_routes`), OS de manutenção (`service_order_routes`), produção (`ordem_producao_routes`).

### 2.4 Usuários, Segurança e Permissões

- `users`, `permissions`, `user_permissions`, `activity_logs`.
- Autenticação principal via `flask_login` em `main_mysql.py` (classe `User`, `load_user`).
- Rotas:
  - `routes.users_routes` (administração).
  - `routes.usuario_routes_mysql` (versão legada/compatibilidade).
  - `routes.permissoes_routes` (permissões).
- `APP_MODE` (`global`, `industrial`, `varejo`) controla escopo de módulos ativos.

### 2.5 CMMS – Manutenção de Ativos

- Tabelas (README):
  - `equipment`, `maintenance_plans`, `service_orders`, `service_order_items`, `service_order_labor`, `hour_meter_readings`, `alerts`, `technicians`.
- Rotas:
  - `routes.equipamento_routes_mysql`.
  - `routes.maintenance_plan_routes`.
  - `routes.service_order_routes`.
  - `routes.hour_meter_routes`.
  - `routes.technician_routes`.
  - `routes.alert_routes`.
- Serviço de **notificações**: `services.notification_service.NotificationService` (gera e-mails e registros em `alerts`).

### 2.6 Comercial – Vendas, Rotas e Romaneios

- Tabelas principais (além das de estoque/financeiro):
  - `sellers`, `sales_routes`, `route_customer`.
  - `romaneios` e tabelas relacionadas (carregamento, entregas).
  - `sales`, `sale_items` (PDV).
- Rotas:
  - `routes.vendedor_routes`.
  - `routes.rota_vendas_routes`.
  - `routes.romaneio_routes`.
  - `routes.venda_routes`.
  - `routes.orcamento_routes`, `routes.orcamento_dna_routes` (orçamentos padrão e com DNA).

### 2.7 PDV Profissional

- Tabelas:
  - `empresas` (multi-empresa, campos específicos para uso no PDV).
  - `pdv_settings` – cerca de 45 colunas por empresa (configurações de estoque, descontos, interface, atalhos, impressão).
  - `sales`, `sale_items`, `cash_register`, `accounts_receivable`, `cash_flow`, `financial_transactions`.
- Rotas:
  - `routes.pdv_profissional_routes` (tela `/vendas/pdv` e APIs auxiliares).
  - `routes.pdv_config_routes` (parametrização).
  - `routes.cash_register_routes` (caixa).
- Integrações técnicas:
  - Estoque (via helper `estoque_helper.registrar_movimentacao`).
  - Fiscal (NF-e/NFC-e) através dos serviços em `services/`.

### 2.8 Indústria – Produção e Previsão Inteligente

Com base em `PLANO_SISTEMA_PREVISAO_PRODUCAO.md` e código existente:

- Tabelas de base:
  - `jornadas_trabalho`, `jornada_horarios` – jornada e turnos.
  - `produtos_tempo_etapa` – tempos padrão e históricos por produto/etapa.
  - `config_feriados` – feriados e dias não úteis.
  - `config_capacidade_etapa` – capacidade de cada etapa produtiva.
  - `log_calculo_previsao` – trilha de auditoria de cálculos.
  - Views: `vw_fila_producao_completa`, `vw_resumo_etapas_producao`.
- Serviço: `services.previsao_producao_service.py`:
  - Funções de jornada, fila, tempos por produto, previsão de OP/orçamento, análise de gargalos.
- Rotas:
  - `routes.config_producao_routes` – telas de configuração (`/industria/config/...`) e API `/api/previsao/calcular`.
  - `routes.ordem_producao_routes` – criação/gestão de OPs.
  - `routes.jornada_trabalho_routes`, `routes.producao_pausas_routes`.
  - `routes.ficha_tecnica_routes` – CRUD de fichas técnicas e integração com tempos reais.

### 2.9 DNA de Produto – Correias (planejado/implantação gradual)

De acordo com `PLANO_DNA_PRODUTO_CORREIAS.md`:

- Tabelas propostas:
  - `produto_especificacoes_tecnicas` – dimensões, materiais, perfil, dureza, lonas, aplicação, código DNA.
  - `produto_anexos` – desenho técnico, fotos, datasheets, certificados.
  - `produto_matching_regras` – regras de equivalência e derivação.
  - `produto_derivacoes`, `derivacao_etapas` – controle de derivação a partir de produto base.
- Rotas/arquivos planejados:
  - `routes.produto_especificacoes_routes`.
  - `services.produto_matching_service`.
  - Templates dedicados em `templates/produtos/`.

Funcionalmente, este módulo adiciona uma **camada técnica avançada** sobre `products`, permitindo matching inteligente de estoque.

---

## 3. Parametrizações e Cadastros de Apoio

- **Condições de pagamento** (`payment_terms`) e **formas de pagamento** (`payment_methods`).
- **Configurações de PDV** (`pdv_settings`) por empresa.
- **Configurações de jornada/capacidade/feriados** no módulo indústria.
- **Screen control**:
  - Tabela `screen_documentation` para documentar telas (ID `SCRxxx`, nome, função, tabelas relacionadas, rota, operações CRUD).
- **Listas auxiliares**:
  - NCM (`ncm_routes`), CFOP (`cfop_routes`), moedas (`currency_routes`), segmentos (`segment_routes`), empresas (`empresa_routes`), transportadoras (`transportadora_routes`).

Do ponto de vista funcional, boa parte do comportamento pode ser ajustado por **configuração**, evitando customização de código para vários clientes.

---

## 4. Integrações e Serviços Técnicos

- **NFe / NFCe**:
  - Geração XML, assinatura digital, comunicação com SEFAZ, impressão de DANFE/DANFCE, envio de e-mails.
  - Arquivos chave: `nfe_service.py`, `nfce_service.py`, `danfe_generator*`, `danfce_generator.py`, `certificado_digital.py`, `sefaz_service.py`.
- **Integração ERP externo / legado**:
  - `erp_integration_service.py` – pontos de integração com outros ERPs/sistemas.
- **Integração IoT**:
  - `iot_integration_service.py` – previsto para conectar sensores (por exemplo, horímetro automático ou monitoramento de equipamentos).
- **Notificações**:
  - `notification_service.py` – criação de alertas e envio de e-mails automáticos.
- **Câmbio**:
  - `exchange_rate_service.py` – atualização de taxas de câmbio.

---

## 5. Avaliação de Aderência ERP × Processo

- **Pontos fortes funcionais**:
  - Estrutura típica de **ERP industrial**: compras, estoque, financeiro, fiscal, produção, manutenção, PDV.
  - Modelagem de dados rica para **produção** (tempos por etapa, capacidade, jornada, fichas técnicas, logs de histórico).
  - **CMMS** bem representado em tabelas e rotas.
  - Preparação para cenários complexos de produto (DNA, derivação, anexos técnicos).
- **Pontos de atenção**:
  - É necessário disciplinar o uso de cadastros-mestre (produtos, clientes, fornecedores) para evitar inconsistências.
  - Módulos avançados (DNA produto, comparativo custo template vs real) ainda estão em evolução;
    importante gerenciar feature flags e migração de dados.
  - Integrações externas (IoT, ERPs terceiros) precisam de contratos e documentação claros para garantir estabilidade.

---

## 6. Recomendações Funcionais

1. **Governança de dados mestres**:
   - Formalizar responsáveis por `products`, `customers`, `suppliers`, `equipment`, `technicians`.
   - Implementar validações e workflows de aprovação onde necessário.
2. **Catálogo de parametrizações**:
   - Documentar todas as tabelas de configuração (PDV, produção, feriados, capacidade, condições de pagamento) em um único guia funcional.
3. **Pacotes de implementação modular**:
   - Pacote "Financeiro + Compras + Estoque".
   - Pacote "Fiscal (NFe/NFCe)".
   - Pacote "CMMS".
   - Pacote "Indústria (previsão, OP, fichas técnicas)".
   - Pacote "DNA Produto".
4. **Controle de telas (screen_documentation)**:
   - Atualizar a tabela e a documentação para refletir o estado atual de todos os blueprints e templates.
   - Usar esse controle como base para treinamento, suporte e testes.
5. **Minimalizar customizações específicas de cliente**:
   - Sempre que possível, resolver variações de processo via **configuração** (tabelas auxiliares, flags) e não via forks de código.

Este relatório deve ser usado como mapa para implantação, parametrização e análise de aderência funcional do SupplyChainSystem em novos clientes industriais.
