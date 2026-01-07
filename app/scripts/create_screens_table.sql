-- Script para criar a tabela de controle de telas no banco de dados
-- Esta tabela armazena informações sobre cada tela do sistema, suas funções e relacionamentos

-- Verificar se a tabela já existe e removê-la se necessário
DROP TABLE IF EXISTS screen_documentation;

-- Criar a tabela de documentação de telas
CREATE TABLE screen_documentation (
    id VARCHAR(10) PRIMARY KEY,
    screen_name VARCHAR(100) NOT NULL,
    function_description TEXT NOT NULL,
    related_tables TEXT,
    database_name VARCHAR(50) DEFAULT 'supply_chain_system',
    html_file VARCHAR(100),
    route VARCHAR(100),
    operations VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Inserir dados das telas
INSERT INTO screen_documentation (id, screen_name, function_description, related_tables, html_file, route, operations) VALUES
('SCR001', 'Login', 'Autenticação de usuários para acesso ao sistema', 'users', 'login.html', '/login', 'Leitura'),
('SCR002', 'Dashboard', 'Visão geral do sistema com indicadores e gráficos', 'customers, products, supplies, suppliers, service_orders, equipment', 'dashboard.html', '/dashboard', 'Leitura'),
('SCR003', 'Lista de Clientes', 'Gerenciamento de clientes', 'customers', 'customer_list.html', '/clientes', 'Leitura, Exclusão'),
('SCR004', 'Formulário de Cliente', 'Cadastro/edição de clientes', 'customers', 'customer_form.html', '/clientes/novo, /clientes/editar/<id>', 'Criação, Atualização'),
('SCR005', 'Visualização de Cliente', 'Detalhes de um cliente específico', 'customers, equipment, service_orders', 'customer_view.html', '/clientes/visualizar/<id>', 'Leitura'),
('SCR006', 'Lista de Fornecedores', 'Gerenciamento de fornecedores', 'suppliers', 'supplier_list.html', '/fornecedores', 'Leitura, Exclusão'),
('SCR007', 'Formulário de Fornecedor', 'Cadastro/edição de fornecedores', 'suppliers', 'supplier_form.html', '/fornecedores/novo, /fornecedores/editar/<id>', 'Criação, Atualização'),
('SCR008', 'Visualização de Fornecedor', 'Detalhes de um fornecedor específico', 'suppliers, products, supplies', 'supplier_view.html', '/fornecedores/visualizar/<id>', 'Leitura'),
('SCR009', 'Lista de Produtos', 'Gerenciamento de produtos', 'products', 'product_list.html', '/produtos', 'Leitura, Exclusão'),
('SCR010', 'Formulário de Produto', 'Cadastro/edição de produtos', 'products, suppliers', 'product_form.html', '/produtos/novo, /produtos/editar/<id>', 'Criação, Atualização'),
('SCR011', 'Visualização de Produto', 'Detalhes de um produto específico', 'products, suppliers', 'product_view.html', '/produtos/visualizar/<id>', 'Leitura'),
('SCR012', 'Lista de Insumos', 'Gerenciamento de insumos', 'supplies', 'supply_list.html', '/insumos', 'Leitura, Exclusão'),
('SCR013', 'Formulário de Insumo', 'Cadastro/edição de insumos', 'supplies, suppliers', 'supply_form.html', '/insumos/novo, /insumos/editar/<id>', 'Criação, Atualização'),
('SCR014', 'Visualização de Insumo', 'Detalhes de um insumo específico', 'supplies, suppliers', 'supply_view.html', '/insumos/visualizar/<id>', 'Leitura'),
('SCR015', 'Lista de Equipamentos', 'Gerenciamento de equipamentos', 'equipment', 'equipment_list.html', '/equipamentos', 'Leitura, Exclusão'),
('SCR016', 'Formulário de Equipamento', 'Cadastro/edição de equipamentos', 'equipment, customers', 'equipment_form.html', '/equipamentos/novo, /equipamentos/editar/<id>', 'Criação, Atualização'),
('SCR017', 'Visualização de Equipamento', 'Detalhes de um equipamento específico', 'equipment, customers, maintenance_plans, hour_meter_readings', 'equipment_view.html', '/equipamentos/visualizar/<id>', 'Leitura'),
('SCR018', 'Lista de Planos de Manutenção', 'Gerenciamento de planos de manutenção', 'maintenance_plans', 'maintenance_plan_list.html', '/planos-manutencao', 'Leitura, Exclusão'),
('SCR019', 'Formulário de Plano de Manutenção', 'Cadastro/edição de planos de manutenção', 'maintenance_plans, equipment, customers', 'maintenance_plan_form.html', '/planos-manutencao/novo, /planos-manutencao/editar/<id>', 'Criação, Atualização'),
('SCR020', 'Visualização de Plano de Manutenção', 'Detalhes de um plano de manutenção específico', 'maintenance_plans, equipment, customers', 'maintenance_plan_view.html', '/planos-manutencao/visualizar/<id>', 'Leitura'),
('SCR021', 'Lista de Ordens de Serviço', 'Gerenciamento de ordens de serviço', 'service_orders', 'service_order_list.html', '/ordens-servico', 'Leitura, Exclusão'),
('SCR022', 'Formulário de Ordem de Serviço', 'Cadastro/edição de ordens de serviço', 'service_orders, customers, equipment, technicians, maintenance_plans', 'service_order_form.html', '/ordens-servico/novo, /ordens-servico/editar/<id>', 'Criação, Atualização'),
('SCR023', 'Visualização de Ordem de Serviço', 'Detalhes de uma ordem de serviço específica', 'service_orders, service_order_items, service_order_labor, customers, equipment, technicians', 'service_order_view.html', '/ordens-servico/visualizar/<id>', 'Leitura'),
('SCR024', 'Lista de Técnicos', 'Gerenciamento de técnicos', 'technicians', 'technician_list.html', '/tecnicos', 'Leitura, Exclusão'),
('SCR025', 'Formulário de Técnico', 'Cadastro/edição de técnicos', 'technicians', 'technician_form.html', '/tecnicos/novo, /tecnicos/editar/<id>', 'Criação, Atualização'),
('SCR026', 'Visualização de Técnico', 'Detalhes de um técnico específico', 'technicians, service_orders, service_order_labor', 'technician_view.html', '/tecnicos/visualizar/<id>', 'Leitura'),
('SCR027', 'Lista de Leituras de Horímetro', 'Gerenciamento de leituras de horímetro', 'hour_meter_readings', 'hour_meter_reading_list.html', '/horimetro', 'Leitura, Exclusão'),
('SCR028', 'Formulário de Leitura de Horímetro', 'Cadastro/edição de leituras de horímetro', 'hour_meter_readings, equipment', 'hour_meter_reading_form.html', '/horimetro/novo, /horimetro/editar/<id>', 'Criação, Atualização'),
('SCR029', 'Visualização de Leitura de Horímetro', 'Detalhes de uma leitura de horímetro específica', 'hour_meter_readings, equipment', 'hour_meter_reading_view.html', '/horimetro/visualizar/<id>', 'Leitura'),
('SCR030', 'Lista de Alertas', 'Gerenciamento de alertas', 'alerts', 'alert_list.html', '/alertas', 'Leitura, Exclusão'),
('SCR031', 'Formulário de Alerta', 'Cadastro/edição de alertas', 'alerts, equipment, supplies', 'alert_form.html', '/alertas/novo, /alertas/editar/<id>', 'Criação, Atualização'),
('SCR032', 'Visualização de Alerta', 'Detalhes de um alerta específico', 'alerts, equipment, supplies', 'alert_view.html', '/alertas/visualizar/<id>', 'Leitura'),
('SCR033', 'Lista de Contas Bancárias', 'Gerenciamento de contas bancárias', 'bank_accounts', 'bank_account_list.html', '/contas-bancarias', 'Leitura, Exclusão'),
('SCR034', 'Formulário de Conta Bancária', 'Cadastro/edição de contas bancárias', 'bank_accounts', 'bank_account_form.html', '/contas-bancarias/novo, /contas-bancarias/editar/<id>', 'Criação, Atualização'),
('SCR035', 'Visualização de Conta Bancária', 'Detalhes de uma conta bancária específica', 'bank_accounts, accounts_payable, accounts_receivable', 'bank_account_view.html', '/contas-bancarias/visualizar/<id>', 'Leitura'),
('SCR036', 'Lista de Contas a Pagar', 'Gerenciamento de contas a pagar', 'accounts_payable', 'accounts_payable_list.html', '/contas-pagar', 'Leitura, Exclusão'),
('SCR037', 'Formulário de Conta a Pagar', 'Cadastro/edição de contas a pagar', 'accounts_payable, suppliers, bank_accounts', 'accounts_payable_form.html', '/contas-pagar/novo, /contas-pagar/editar/<id>', 'Criação, Atualização'),
('SCR038', 'Visualização de Conta a Pagar', 'Detalhes de uma conta a pagar específica', 'accounts_payable, suppliers, bank_accounts', 'accounts_payable_view.html', '/contas-pagar/visualizar/<id>', 'Leitura'),
('SCR039', 'Lista de Contas a Receber', 'Gerenciamento de contas a receber', 'accounts_receivable', 'accounts_receivable_list.html', '/contas-receber', 'Leitura, Exclusão'),
('SCR040', 'Formulário de Conta a Receber', 'Cadastro/edição de contas a receber', 'accounts_receivable, customers, bank_accounts', 'accounts_receivable_form.html', '/contas-receber/novo, /contas-receber/editar/<id>', 'Criação, Atualização'),
('SCR041', 'Visualização de Conta a Receber', 'Detalhes de uma conta a receber específica', 'accounts_receivable, customers, bank_accounts', 'accounts_receivable_view.html', '/contas-receber/visualizar/<id>', 'Leitura'),
('SCR042', 'Relatório de Manutenção', 'Relatório de manutenções realizadas', 'service_orders, equipment, customers, technicians', 'maintenance_report.html', '/relatorios/manutencao', 'Leitura'),
('SCR043', 'Relatório de Custos', 'Relatório de custos de manutenção', 'service_orders, service_order_items, service_order_labor', 'cost_report.html', '/relatorios/custos', 'Leitura'),
('SCR044', 'Relatório de Desempenho', 'Relatório de desempenho de equipamentos', 'equipment, service_orders, hour_meter_readings', 'performance_report.html', '/relatorios/desempenho', 'Leitura'),
('SCR045', 'Configurações do Sistema', 'Configurações gerais do sistema', 'users', 'settings.html', '/configuracoes', 'Leitura, Atualização'),
('SCR046', 'Perfil de Usuário', 'Visualização/edição do perfil do usuário', 'users', 'user_profile.html', '/perfil', 'Leitura, Atualização'),
('SCR047', 'Lista de Usuários', 'Gerenciamento de usuários', 'users', 'user_list.html', '/usuarios', 'Leitura, Exclusão'),
('SCR048', 'Formulário de Usuário', 'Cadastro/edição de usuários', 'users', 'user_form.html', '/usuarios/novo, /usuarios/editar/<id>', 'Criação, Atualização'),
('SCR049', 'Visualização de Usuário', 'Detalhes de um usuário específico', 'users', 'user_view.html', '/usuarios/visualizar/<id>', 'Leitura'),
('SCR050', 'Dashboard de Integrações', 'Visão geral das integrações do sistema', '-', 'integrations_dashboard.html', '/integracoes', 'Leitura');

-- Criar índice para melhorar a performance de consultas
CREATE INDEX idx_screen_name ON screen_documentation(screen_name);
