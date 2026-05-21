# Relatório – UX/UI do SupplyChainSystem

## 1. Visão Geral de UX

O **SupplyChainSystem** é um sistema web baseado em Flask com templates HTML organizados em `app/templates/` (auth, financial, inventory, purchase, reports, users, industria, produtos, comercial, etc.). A navegação é tipicamente feita via menu lateral/topo comum (template base), com cada módulo expondo diversas telas especializadas.

Do ponto de vista de UX:

- Abrange **muitos domínios** (ERP, produção, manutenção, PDV, NFe/NFCe) na mesma interface.
- Atende perfis bem diferentes (comprador, estoquista, técnico, planejador, vendedor, financeiro, gestor industrial).
- Usa majoritariamente **telas de formulário e listas** (CRUD clássico) com templates separados por módulo.

---

## 2. Personas e Jornadas Principais

### 2.1 Comprador

- Navega por módulos de **compras** e **estoque**.
- Principais tarefas:
  - Consultar estoque mínimo/máximo e necessidades.
  - Criar/editar **pedidos de compra**.
  - Acompanhar recebimentos e notas fiscais.

### 2.2 Estoquista / Almoxarife

- Usa telas de **estoque**, **Kardex** e movimentações.
- Tarefas:
  - Lançar entradas/saídas/transferências.
  - Fazer inventário físico.
  - Conferir romaneios e separação de pedidos.

### 2.3 Técnico de Manutenção

- Usa módulos **CMMS**: OS, planos, horímetro, técnicos.
- Tarefas:
  - Visualizar lista de OS abertas.
  - Registrar horas, materiais utilizados e conclusão.
  - Consultar histórico de equipamento.

### 2.4 Planejador de Produção / Engenharia

- Usa módulo **Indústria** (`/industria/...`) e **fichas técnicas**.
- Tarefas:
  - Configurar tempos por produto/etapa.
  - Analisar **dashboard de gargalos**.
  - Ver previsões de conclusão para OPs e orçamentos.
  - Manter fichas técnicas atualizadas com dados reais.

### 2.5 Operador de PDV

- Usa a tela `/vendas/pdv` (PDV profissional).
- Tarefas:
  - Abrir caixa, registrar vendas, aplicar descontos, fechar caixa.
  - Pesquisar produtos rapidamente por código/barras/nome.
  - Selecionar clientes e formas de pagamento.

### 2.6 Financeiro / Contábil

- Usa módulos **financeiros** (accounts_payable, accounts_receivable, bank, cash_flow).
- Tarefas:
  - Acompanhar contas a pagar/receber.
  - Conciliar bancos e caixa.
  - Gerar relatórios financeiros.

---

## 3. Padrões de Interface Existentes

- **Templates por domínio** (`templates/financial`, `inventory`, `purchase`, `industria`, `produtos`, `comercial`, etc.).
- Menus e header comuns definidos em `base.html` (menções no plano de previsão e fichas técnicas).
- Padrão clássico **lista + formulário**:
  - Lista com filtros no topo (por cliente, produto, status, período).
  - Ações: novo, editar, visualizar, excluir.
- No módulo **Indústria**:
  - Uso de **cards** e **timeline Gantt** para o dashboard de produção.
  - Telas de configuração com tabelas responsivas para jornadas, feriados, capacidade, tempos por produto.
- No **PDV Profissional**:
  - Tela full-screen, com grade de itens do carrinho, painel de pagamento, atalhos de teclado.
  - Feedback visual forte para abertura de caixa e reset do carrinho.

---

## 4. Pontos Fortes de UX

- **Separação clara por módulos** (arquitetura de templates ajuda o usuário a entender domínio por domínio).
- **PDV** com foco em produtividade:
  - Carrinho limpo na abertura.
  - Verificações de caixa aberto.
  - Uso de teclado e atalhos.
- **Dashboard de produção** com visão gráfica de timeline e cores por status (verde/amarelo/vermelho), facilitando a leitura rápida por gestores.
- Fichas técnicas com visão de **histórico e KPIs** agregados, úteis para análise rápida.

---

## 5. Oportunidades de Melhoria

### 5.1 Navegação e Descobribilidade

- Alto número de telas e rotas (ver `main_mysql.py`), o que aumenta a **carga cognitiva**.
- Suggestões:
  - Criar **home pages por persona** (ex.: "Painel do Comprador", "Painel do Planejador", "Painel do Técnico").
  - Agrupar menus por **fluxo de trabalho**, não só por módulo técnico (ex.: "Abastecimento", "Vendas", "Produção", "Manutenção").

### 5.2 Fluxos Guiados (Wizards)

Cenários complexos se beneficiam de **passos guiados**:

- Cadastro de **novo produto** com DNA e anexos.
- Criação de **ordem de produção** a partir de orçamento.
- Criação de **plano de manutenção** (equipment + gatilho + insumo + instruções).

Em vez de telas monolíticas, dividir o processo em passos com indicação visual do progresso.

### 5.3 Formulários e Validação

- Muitos formulários têm **diversos campos**; sem uma análise profunda, é comum haver campos opcionais misturados com obrigatórios.
- Melhorias sugeridas:
  - Destacar campos obrigatórios visualmente.
  - Mensagens de erro consistentes e posicionadas próximas ao campo.
  - Pré-preenchimento inteligente (ex.: datas padrão, condição de pagamento, empresa padrão, etc.).

### 5.4 Consistência Visual entre Módulos

- Garantir que botões básicos (`Salvar`, `Cancelar`, `Voltar`) sigam **padrão de cor e posição** em todos os templates.
- Reutilizar componentes (filtros, grids, modais) em vez de múltiplas variações ligeiramente diferentes.

### 5.5 Feedback e Estado do Sistema

- Para operações longas (importar NF-e, cálculos de previsão, emissão fiscal), garantir feedback claro:
  - Spinners, barras de progresso ou mensagens "Processando...".
  - Logs acessíveis em tela (além do terminal) para suporte.
- No PDV, manter sempre visível o **status do caixa** (aberto/fechado, saldo inicial) e usuário logado.

---

## 6. Recomendações de UX Prioritárias

### 6.1 Curto Prazo

- Padronizar **componentes de formulário e tabelas** (usando um conjunto de classes CSS comum).
- Revisar telas de uso intenso (PDV, ordens de serviço, ordens de produção, previsões) para garantir:
  - Foco em campos críticos.
  - Ações primárias destacadas.
  - Mensagens de erro claras.

### 6.2 Médio Prazo

- Implementar **painéis iniciais por persona** (landing pages com atalhos para tarefas frequentes e indicadores básicos).
- Criar **wizards** para processos complexos (novo produto com DNA, nova OP com previsão, novo plano de manutenção).

### 6.3 Longo Prazo

- Introduzir uma **design system** interno (biblioteca de componentes) com documentação, para garantir consistência visual e acelerar criação de novas telas.
- Incorporar **testes de usabilidade** com usuários reais de indústria e revisões periódicas.

Este relatório é um ponto de partida para evoluir a experiência do usuário do SupplyChainSystem, mantendo a potência funcional e reduzindo fricções na operação diária.
