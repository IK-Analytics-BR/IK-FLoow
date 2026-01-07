# Sistema de Gestão de Suprimentos Industriais

Sistema completo para gerenciamento de distribuição de insumos industriais, com foco em rastreamento de desgaste de peças e equipamentos. Este sistema foi desenvolvido para atender às necessidades de distribuidoras de insumos e fabricantes de equipamentos, permitindo o acompanhamento do ciclo de vida das peças e facilitando a comunicação entre fornecedores e clientes.

## IMPORTANTE: Configuração do Banco de Dados

### Banco de Dados Mestre: `supply_chain_system`

Este sistema utiliza o MySQL como banco de dados, com o esquema `supply_chain_system` como ambiente mestre para todas as operações. É **ESSENCIAL** que todas as tabelas sejam criadas e mantidas dentro deste ambiente.

**Configurações de Conexão:**
- **Host:** localhost
- **Usuário:** root
- **Senha:** aritana
- **Banco de Dados:** supply_chain_system

**ATENÇÃO:** 
- Todos os módulos do sistema estão configurados para ler e gravar dados exclusivamente neste banco de dados.
- Qualquer alteração na estrutura do banco deve ser feita através dos scripts fornecidos na pasta `app/scripts/`.
- Ao adicionar novos módulos, garanta que eles utilizem o mesmo banco de dados para manter a integridade do sistema.

## Sistema de Controle de Telas

O sistema implementa um controle de telas com IDs únicos para cada interface, facilitando a documentação, rastreabilidade e manutenção.

### Estrutura de IDs

Cada tela possui um identificador único no formato `SCRxxx`, onde xxx é um número sequencial de 3 dígitos (ex: SCR001, SCR002).

### Tabela de Controle

As informações sobre cada tela são armazenadas em:

1. **Documentação**: Arquivo detalhado em `docs/screen_documentation.md`
2. **Banco de Dados**: Tabela `screen_documentation` no banco `supply_chain_system`

### Informações Armazenadas

Para cada tela, são registradas as seguintes informações:

- **ID**: Identificador único da tela
- **Nome da Tela**: Nome descritivo
- **Função**: Descrição da funcionalidade
- **Tabelas Relacionadas**: Tabelas do banco de dados utilizadas
- **Banco de Dados**: Nome do banco de dados (supply_chain_system)
- **Arquivo HTML**: Nome do arquivo de template
- **Rota**: Endpoint da API
- **Operações**: Tipos de operações realizadas (Leitura, Criação, Atualização, Exclusão)

### Scripts de Manutenção

Para gerenciar o sistema de controle de telas:

- `app/scripts/create_screens_table.sql`: Script SQL para criar a tabela
- `app/scripts/create_screens_table.py`: Script Python para executar o SQL

### Como Atualizar

Ao adicionar novas telas ao sistema:

1. Atualize o arquivo `docs/screen_documentation.md`
2. Adicione o registro na tabela `screen_documentation` no banco de dados
3. Siga o padrão de IDs sequenciais

## Funcionalidades

### Módulo Financeiro
- Gerenciamento de contas bancárias
- Controle de contas a pagar e receber
- Fluxo de caixa com projeções e simulações
- Relatórios financeiros detalhados

### Módulo de Compras
- Gerenciamento de pedidos de compra
  - Cabeçalho completo com dados do fornecedor, condições de pagamento e entrega
  - Itens do pedido com controle de quantidade, preço e desconto
  - Totais do pedido com subtotal, descontos, frete, seguro e impostos
  - Integração com estoque para recebimento de mercadorias
  - Integração com financeiro para geração de contas a pagar
- Controle de notas fiscais
  - Importação de XML de NF-e
  - Vinculação com pedidos de compra
  - Validação automática de valores e quantidades
- Integração com estoque
  - Atualização automática do estoque no recebimento
  - Controle de lotes e validades
  - Rastreabilidade completa

### Módulo de Estoque
- Controle de posição de estoque
- Movimentações de estoque (entradas, saídas, ajustes, transferências)
- Configuração de estoque mínimo e máximo
- Relatórios de estoque

### Módulo de Relatórios
- Relatórios financeiros
- Relatórios de compras
- Relatórios de estoque
- Relatório consolidado

### Módulo de Usuários e Permissões
- Gerenciamento de usuários
- Controle de permissões
- Perfil de usuário
- Log de atividades

### Módulo de Manutenção de Ativos (CMMS)
- Horímetro e controle de uso
- Planos de manutenção
- Ordens de serviço
- Alertas e notificações
- Dashboards e relatórios
- Integrações (ERP/IoT)

### Módulo de Técnicos
- Cadastro de técnicos
- Atribuição de técnicos a ordens de serviço
- Registro de horas trabalhadas
- Dashboard de técnicos

### Módulo de Romaneio de Vendas
- Cadastro de vendedores
- Rotas de vendas
- Romaneio de vendas
- Integração com clientes e produtos

### Módulo PDV (Ponto de Venda) Profissional ⭐ NOVO
- **PDV moderno e responsivo** com identidade visual IK Analytics
- **Múltiplas empresas** - Seleção dinâmica com logo e configurações específicas
- **Controle de caixa integrado** - Abertura/fechamento obrigatório
- **Busca inteligente de produtos** - Por código, barras ou nome (modal F6)
- **Carrinho completo** - Grade com atualização em tempo real
- **Sistema de descontos por item (F4)** - Percentual ou valor, com preview
- **Cancelamento múltiplo (F5)** - Seleção com checkboxes de vários itens
- **Gestão de clientes (F2)** - Busca e vinculação à venda
- **Finalização avançada (F9)** - Múltiplas formas de pagamento simultâneas
  - Dinheiro, Débito, Crédito, PIX, Boleto
  - Cálculo automático de troco
  - Grid de 5 pagamentos em linha única (1500px)
- **Integração financeira completa** - Lançamentos automáticos em:
  - Contas a receber (por pagamento)
  - Fluxo de caixa
  - Transações financeiras
- **Atalhos de teclado** - F2 a F11 para operações rápidas
- **Limpeza automática** - Carrinho limpo ao abrir/fechar PDV
- **45+ configurações** - Tabela pdv_settings por empresa
- **Logs detalhados** - Debug completo de operações

📄 **Documentação Completa:** `FUNCIONALIDADES_PDV_COMPLETO.md`

## Requisitos

- Python 3.8+
- MySQL 8.0+
- Bibliotecas Python listadas em requirements.txt

## Instalação

1. Clone o repositório ou descompacte o arquivo do projeto

2. Crie um ambiente virtual Python:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

4. Configure o banco de dados MySQL:
   - Crie um banco de dados chamado `supply_chain_system`
   - O usuário padrão é `root` com senha `aritana`
   - Se necessário, altere as configurações de conexão no arquivo `.env`

5. Configure as variáveis de ambiente:
   - Um arquivo `.env` já foi criado na pasta `app/`
   - Verifique se as configurações de banco de dados estão corretas:
     ```
     DB_HOST=localhost
     DB_USER=root
     DB_PASSWORD=aritana
     DB_NAME=supply_chain_system
     ```
   - A variável `SECRET_KEY` já está definida

6. Inicialize o banco de dados executando os scripts SQL:
   ```
   cd app/scripts
   python create_database.py
   python verify_all_database_tables.py
   ```
   Isso criará todas as tabelas necessárias no banco de dados e um usuário administrador com as seguintes credenciais:
   - Username: admin
   - Senha: admin

7. Execute o aplicativo:
   ```
   cd app
   python main_mysql.py
   ```

8. Acesse o sistema pelo navegador em `http://localhost:8080`

## Estrutura do Projeto

```
 SupplyChainSystem/
├── app/
│   ├── database/       # Conexão com o banco de dados
│   ├── routes/         # Rotas da aplicação
│   │   ├── pdv_profissional_routes.py  # ⭐ PDV completo
│   │   └── ...         # Outras rotas
│   ├── scripts/        # Scripts SQL e utilitários
│   ├── static/         # Arquivos estáticos (CSS, JS)
│   │   ├── css/        # Folhas de estilo
│   │   ├── js/         # Scripts JavaScript
│   │   └── images/     # Logos e imagens
│   │       └── logo_sistema.png  # Logo IK Analytics
│   ├── templates/      # Templates HTML
│   │   ├── auth/       # Templates de autenticação
│   │   ├── financial/  # Templates do módulo financeiro
│   │   ├── inventory/  # Templates do módulo de estoque
│   │   ├── purchase/   # Templates do módulo de compras
│   │   ├── reports/    # Templates do módulo de relatórios
│   │   ├── users/      # Templates do módulo de usuários
│   │   └── venda_pdv_profissional.html  # ⭐ PDV interface
│   ├── .env            # Variáveis de ambiente
│   └── main_mysql.py   # Script principal da aplicação
├── docs/               # Documentação detalhada
│   ├── screen_documentation.md  # Documentação das telas
│   └── README.md       # Documentação geral do CMMS
├── _ARQUIVOS_OBSOLETOS/  # Arquivos históricos (não usar)
│   ├── 01_duplicados_raiz/
│   ├── 02_rotas_antigas/
│   ├── 03_templates_obsoletos/
│   ├── 04_scripts_teste/
│   ├── 05_correcoes_executadas/
│   ├── 06_documentacao_correcoes/
│   └── README.md       # Índice de arquivos obsoletos
├── FUNCIONALIDADES_PDV_COMPLETO.md  # ⭐ Documentação PDV
├── requirements.txt    # Dependências do projeto
└── README.md           # Este arquivo
```

## Banco de Dados

O sistema utiliza MySQL para armazenamento de dados no banco `supply_chain_system`, com os seguintes módulos e tabelas principais:

### Módulo Financeiro
- `bank_accounts`: Contas bancárias
- `accounts_payable`: Contas a pagar
- `accounts_receivable`: Contas a receber
- `cash_flow`: Fluxo de caixa

### Módulo de Compras
- `purchase_orders`: Pedidos de compra com informações completas de cabeçalho
  - Dados do fornecedor, datas, condições de pagamento, endereço de entrega
  - Valores financeiros: subtotal, descontos, frete, seguro, impostos, total
  - Status do pedido: rascunho, aprovado, recebido parcial, concluído, cancelado
- `purchase_order_items`: Itens de pedidos de compra
  - Produto, quantidade, preço unitário, descontos, impostos, total
  - Status do item: pendente, recebido parcial, recebido total
  - Controle de lote e número de série
- `purchase_order_receipts`: Recebimentos de pedidos de compra
  - Vinculação com pedido de compra e nota fiscal
  - Data de recebimento, responsável, observações
- `purchase_order_receipt_items`: Itens recebidos
  - Quantidade recebida, lote, validade, local de armazenamento
- `payment_terms`: Condições de pagamento
  - Nome, dias de pagamento (30, 60, 30/60/90), descrição
- `payment_methods`: Formas de pagamento
  - Boleto, PIX, transferência, cartão de crédito, dinheiro
- `invoices`: Notas fiscais
  - Dados completos da NF-e, vinculação com pedido de compra
  - Valores, impostos, datas, status
- `invoice_items`: Itens de notas fiscais
  - Produto, quantidade, preço, impostos, total

### Módulo de Estoque
- `stock_locations`: Locais de estoque
- `current_stock`: Posição atual de estoque
- `stock_movements`: Movimentações de estoque
- `inventory_counts`: Inventários físicos

### Módulo de Usuários e Permissões
- `users`: Usuários do sistema
- `permissions`: Permissões do sistema
- `user_permissions`: Relação entre usuários e permissões
- `activity_logs`: Logs de atividades dos usuários

### Módulo CMMS
- `equipment`: Equipamentos
- `maintenance_plans`: Planos de manutenção
- `service_orders`: Ordens de serviço
- `service_order_items`: Itens de ordens de serviço
- `service_order_labor`: Mão de obra em ordens de serviço
- `hour_meter_readings`: Leituras de horímetro
- `alerts`: Alertas do sistema
- `technicians`: Técnicos

### Módulo de Controle de Telas
- `screen_documentation`: Documentação das telas do sistema

### Módulo PDV (Ponto de Venda) ⭐
- `empresas`: Empresas (com campos `usar_no_pdv`, `logo_path`)
- `pdv_settings`: Configurações do PDV por empresa (45 colunas)
  - Estoque, quantidade, preço, desconto
  - Cliente, pagamento, interface
  - Atalhos de teclado, segurança, impressão
- `sales`: Vendas (com `company_id`, `payment_method`, descontos)
- `sale_items`: Itens de vendas (com desconto por item)
- `cash_register`: Caixas (abertura/fechamento por usuário)
- `accounts_receivable`: Contas a receber (por pagamento)
- `cash_flow`: Fluxo de caixa (entradas de vendas)
- `financial_transactions`: Transações financeiras

## Credenciais de Acesso

Para acessar o sistema, utilize as seguintes credenciais:

- **Usuário:** admin
- **Senha:** admin

## Scripts de Manutenção do Banco

- `create_database.py`: Verifica e cria o banco de dados `supply_chain_system`
- `verify_all_database_tables.py`: Verifica e cria todas as tabelas necessárias

Para garantir que o sistema funcione corretamente, execute estes scripts na seguinte ordem:

```
cd C:\Users\arita\CascadeProjects\SupplyChainSystem\app\scripts
python create_database.py
python verify_all_database_tables.py
```

Em seguida, reinicie a aplicação para aplicar as alterações.

## Como Testar

### Testar o módulo de horímetro:

1. Acesse o sistema em `http://localhost:8080`
2. Faça login com suas credenciais
3. No menu lateral, clique em "Horímetro"
4. Para registrar uma nova leitura, clique em "Nova Leitura"
5. Selecione um equipamento, informe a data e o valor em horas
6. Clique em "Salvar"

### Testar o módulo de técnicos:

1. Acesse o sistema em `http://localhost:8080`
2. Faça login com suas credenciais
3. No menu lateral, clique em "Técnicos"
4. Para cadastrar um novo técnico, clique em "Novo Técnico"
5. Preencha os campos obrigatórios e clique em "Salvar"
6. Para atribuir um técnico a uma ordem de serviço, acesse o módulo "Ordens de Serviço" e selecione o técnico desejado

## Solução de Problemas

### Erro de Conexão com o MySQL

Se você encontrar erros de conexão com o MySQL, verifique:
1. Se o servidor MySQL está em execução
2. Se as credenciais no arquivo `.env` estão corretas
3. Se o usuário tem permissão para criar bancos de dados e tabelas

### Erro ao Criar Tabelas

Se ocorrerem erros ao criar as tabelas, verifique:
1. Se o banco de dados `supply_chain_system` existe
2. Se o usuário tem permissão para criar tabelas
3. Se não há conflitos de nome com tabelas existentes

### Outros Problemas

Para outros problemas, verifique os logs do servidor Flask que são exibidos no console durante a execução do sistema.

## Suporte

Para suporte técnico ou dúvidas sobre o sistema, entre em contato pelo email: suporte@exemplo.com
