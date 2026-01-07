-- =====================================================
-- Script: 069_PERMISSOES_USUARIO.sql
-- Descrição: Sistema de controle de acesso por usuário
-- Data: 2024-12-28
-- =====================================================

USE supply_chain_system;

-- 1. Tabela de módulos/telas do sistema
CREATE TABLE IF NOT EXISTS sistema_telas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(100) NOT NULL UNIQUE COMMENT 'Código único da tela (ex: vendas.pdv)',
    nome VARCHAR(150) NOT NULL COMMENT 'Nome amigável da tela',
    descricao VARCHAR(255) NULL COMMENT 'Descrição da funcionalidade',
    modulo VARCHAR(50) NOT NULL COMMENT 'Módulo pai (Vendas, Compras, etc.)',
    rota_flask VARCHAR(200) NULL COMMENT 'Endpoint Flask (ex: venda.venda_pdv_moderna)',
    url_padrao VARCHAR(200) NULL COMMENT 'URL padrão da tela',
    icone VARCHAR(50) DEFAULT 'fas fa-file' COMMENT 'Ícone FontAwesome',
    ordem INT DEFAULT 0 COMMENT 'Ordem de exibição no menu',
    ativo TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_modulo (modulo),
    INDEX idx_ativo (ativo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Tabela de permissões do usuário por tela
CREATE TABLE IF NOT EXISTS usuario_permissoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    tela_id INT NOT NULL,
    pode_visualizar TINYINT(1) DEFAULT 0 COMMENT 'Pode ver a tela',
    pode_criar TINYINT(1) DEFAULT 0 COMMENT 'Pode criar novos registros',
    pode_editar TINYINT(1) DEFAULT 0 COMMENT 'Pode editar registros',
    pode_excluir TINYINT(1) DEFAULT 0 COMMENT 'Pode excluir registros',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT NULL,
    
    UNIQUE KEY uk_usuario_tela (usuario_id, tela_id),
    INDEX idx_usuario (usuario_id),
    INDEX idx_tela (tela_id),
    
    FOREIGN KEY (usuario_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (tela_id) REFERENCES sistema_telas(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Inserir todas as telas do sistema
INSERT INTO sistema_telas (codigo, nome, descricao, modulo, rota_flask, url_padrao, icone, ordem) VALUES
-- Dashboard
('dashboard', 'Dashboard', 'Painel principal do sistema', 'Dashboard', 'dashboard', '/', 'fas fa-home', 1),

-- Vendas
('vendas.orcamentos', 'Orçamentos', 'Gerenciar orçamentos', 'Vendas', 'orcamentos.lista', '/orcamentos/', 'fas fa-file-invoice-dollar', 10),
('vendas.lista_preco', 'Listas de Preço', 'Gerenciar listas de preço', 'Vendas', 'lista_preco.lista', '/lista-preco/', 'fas fa-tags', 11),
('vendas.pdv', 'PDV / Venda', 'Ponto de venda', 'Vendas', 'venda.venda_pdv_moderna', '/pdv/', 'fas fa-cash-register', 12),
('vendas.caixa', 'Caixa', 'Controle de caixa', 'Vendas', NULL, '/caixa/atual', 'fas fa-dollar-sign', 13),
('vendas.rotas', 'Rotas de Vendas', 'Gerenciar rotas de vendas', 'Vendas', 'rota_vendas.rotas_vendas_list', '/rotas-vendas/', 'fas fa-route', 14),
('vendas.vendedores', 'Vendedores', 'Cadastro de vendedores', 'Vendas', 'vendedor.vendedores', '/vendedores/', 'fas fa-user-tie', 15),
('vendas.romaneio', 'Romaneio', 'Gerenciar romaneios', 'Vendas', 'romaneio.romaneio_list', '/romaneio/', 'fas fa-clipboard-list', 16),
('vendas.nfe_pendentes', 'NF-e Pendentes', 'Vendas pendentes de NF-e', 'Vendas', 'nfe_emissao.vendas_pendentes', '/nfe/vendas-pendentes', 'fas fa-clock', 17),
('vendas.nfe_emitir', 'Emitir NF-e', 'Emitir NF-e manual', 'Vendas', 'nfe_emissao.emitir_manual', '/nfe/emitir', 'fas fa-file-invoice', 18),
('vendas.nfe_historico', 'Histórico NF-e', 'Histórico de NF-e emitidas', 'Vendas', 'nfe_emissao.historico', '/nfe/historico', 'fas fa-history', 19),
('vendas.relacao', 'Relação de Vendas', 'Relatório de vendas', 'Vendas', 'venda.vendas_relacao', '/vendas/relacao', 'fas fa-list', 20),

-- Clientes
('clientes.lista', 'Clientes', 'Cadastro de clientes', 'Clientes', 'cliente.clientes', '/clientes/', 'fas fa-user-check', 30),
('clientes.potenciais', 'Clientes em Potencial', 'Leads e prospects', 'Clientes', 'clientes_potenciais.lista', '/clientes-potenciais/', 'fas fa-user-plus', 31),
('clientes.segmentos', 'Segmentos', 'Segmentos de clientes', 'Clientes', 'segment.segmentos', '/segmentos/', 'fas fa-layer-group', 32),

-- Produtos e Estoque
('produtos.lista', 'Produtos', 'Cadastro de produtos', 'Produtos', 'produto.produtos', '/produtos/', 'fas fa-box', 40),
('produtos.ncm', 'NCM', 'Tabela NCM', 'Produtos', 'ncm.ncms', '/ncm/', 'fas fa-barcode', 41),
('produtos.cfop', 'CFOP', 'Tabela CFOP', 'Produtos', 'cfop.cfops', '/cfop/', 'fas fa-receipt', 42),
('produtos.categorias', 'Categorias', 'Categorias de produtos', 'Produtos', 'product_category.categorias', '/categorias/', 'fas fa-sitemap', 43),
('produtos.marcas', 'Marcas', 'Marcas de produtos', 'Produtos', 'product_brand.marcas', '/marcas/', 'fas fa-copyright', 44),
('produtos.modelos', 'Modelos', 'Modelos de produtos', 'Produtos', 'product_model.modelos', '/modelos/', 'fas fa-cube', 45),
('produtos.grupos', 'Grupos', 'Grupos de produtos', 'Produtos', 'product_group.grupos', '/grupos/', 'fas fa-object-group', 46),
('produtos.subgrupos', 'Subgrupos', 'Subgrupos de produtos', 'Produtos', 'product_subgroup.subgrupos', '/subgrupos/', 'fas fa-layer-group', 47),
('produtos.unidades', 'Unidades de Medida', 'Unidades de medida', 'Produtos', 'unit_measure.unidades', '/unidades/', 'fas fa-balance-scale', 48),
('produtos.insumos', 'Insumos', 'Cadastro de insumos', 'Produtos', 'insumo.insumos', '/insumos/', 'fas fa-cogs', 49),
('estoque.lista', 'Estoque', 'Controle de estoque', 'Produtos', 'inventory.inventory_list', '/estoque/', 'fas fa-warehouse', 50),
('estoque.kardex', 'Kardex', 'Histórico de movimentações', 'Produtos', 'kardex.kardex_index', '/kardex/', 'fas fa-history', 51),
('produtos.fichas_tecnicas', 'Fichas Técnicas', 'Fichas técnicas de produtos', 'Produtos', 'ficha_tecnica.listar', '/fichas-tecnicas/', 'fas fa-clipboard-list', 52),

-- Indústria
('industria.ops', 'Ordens de Produção', 'Gerenciar OPs', 'Indústria', 'ordem_producao.listar_ops', '/industria/ordem-producao/', 'fas fa-tasks', 60),
('industria.gantt', 'Produção (Gantt)', 'Visualização Gantt', 'Indústria', 'ordem_producao.producao_gantt', '/industria/ordem-producao/producao/gantt', 'fas fa-project-diagram', 61),
('industria.minha_producao', 'Minha Produção', 'Produção do operador', 'Indústria', 'ordem_producao.meu_gantt', '/industria/ordem-producao/meu-gantt', 'fas fa-hard-hat', 62),
('industria.etapas', 'Etapas de Produção', 'Cadastro de etapas', 'Indústria', 'ordem_producao.etapas_lista', '/industria/ordem-producao/etapas', 'fas fa-stream', 63),
('industria.grupos_etapas', 'Grupos de Etapas', 'Grupos de etapas', 'Indústria', 'ordem_producao.etapas_grupos_lista', '/industria/ordem-producao/etapas/grupos', 'fas fa-layer-group', 64),
('industria.jornada', 'Jornada de Trabalho', 'Configurar jornadas', 'Indústria', 'jornada_trabalho.listar_jornadas', '/jornadas/', 'fas fa-clock', 65),
('industria.dashboard_gargalos', 'Dashboard Gargalos', 'Análise de gargalos', 'Indústria', 'config_producao.dashboard_producao', '/industria/config/dashboard', 'fas fa-chart-line', 66),
('industria.tempos', 'Tempos de Produção', 'Configurar tempos', 'Indústria', 'config_producao.tempos_producao', '/industria/config/tempos-producao', 'fas fa-stopwatch', 67),
('industria.feriados', 'Feriados', 'Cadastro de feriados', 'Indústria', 'config_producao.feriados', '/industria/config/feriados', 'fas fa-calendar-times', 68),
('industria.capacidade', 'Capacidade Etapas', 'Capacidade por etapa', 'Indústria', 'config_producao.capacidade_etapas', '/industria/config/capacidade-etapas', 'fas fa-tachometer-alt', 69),
('industria.painel_lider', 'Painel do Líder', 'Painel do líder de equipe', 'Indústria', 'ordem_producao.lider_painel', '/industria/ordem-producao/lider/painel', 'fas fa-user-tie', 70),
('industria.gerenciar_equipe', 'Gerenciar Equipe', 'Gerenciar equipe de produção', 'Indústria', 'ordem_producao.lider_gerenciar_equipe', '/industria/ordem-producao/lider/gerenciar-equipe', 'fas fa-users-cog', 71),

-- Compras
('compras.fornecedores', 'Fornecedores', 'Cadastro de fornecedores', 'Compras', 'fornecedor.fornecedores', '/fornecedores/', 'fas fa-truck', 80),
('compras.entrada', 'Entrada de Produtos', 'Entrada de notas fiscais', 'Compras', 'invoice.invoice_create', '/entrada/', 'fas fa-inbox', 81),
('compras.pedidos', 'Pedidos de Compra', 'Gerenciar pedidos', 'Compras', 'purchase_order.purchase_orders_list', '/pedidos-compra/', 'fas fa-file-invoice', 82),
('compras.transportadoras', 'Transportadoras', 'Cadastro de transportadoras', 'Compras', 'transportadoras.lista', '/transportadoras/', 'fas fa-truck-moving', 83),

-- Financeiro
('financeiro.contas_bancarias', 'Contas Bancárias', 'Gerenciar contas', 'Financeiro', 'bank_account.bank_accounts_list', '/contas-bancarias/', 'fas fa-university', 90),
('financeiro.contas_pagar', 'Contas a Pagar', 'Gerenciar pagamentos', 'Financeiro', 'accounts_payable.accounts_payable_list', '/contas-pagar/', 'fas fa-file-invoice-dollar', 91),
('financeiro.contas_receber', 'Contas a Receber', 'Gerenciar recebimentos', 'Financeiro', 'accounts_receivable.accounts_receivable_list', '/contas-receber/', 'fas fa-hand-holding-usd', 92),
('financeiro.fluxo_caixa', 'Fluxo de Caixa', 'Dashboard financeiro', 'Financeiro', 'cash_flow.cash_flow_dashboard', '/fluxo-caixa/', 'fas fa-chart-line', 93),
('financeiro.plano_contas', 'Plano de Contas', 'Estrutura contábil', 'Financeiro', 'chart_of_accounts.chart_of_accounts_list', '/plano-contas/', 'fas fa-book', 94),
('financeiro.historico_caixas', 'Histórico de Caixas', 'Histórico de caixas', 'Financeiro', NULL, '/caixa', 'fas fa-cash-register', 95),
('financeiro.formas_pagamento', 'Formas de Pagamento', 'Configurar formas', 'Financeiro', 'payment_config.payment_config_list', '/formas-pagamento/', 'fas fa-credit-card', 96),
('financeiro.condicoes_pagamento', 'Condições de Pagamento', 'Configurar condições', 'Financeiro', 'condicoes_pagamento.lista', '/condicoes-pagamento/', 'fas fa-calendar-alt', 97),

-- Manutenção
('manutencao.equipamentos', 'Equipamentos', 'Cadastro de equipamentos', 'Manutenção', 'equipamento.equipamentos', '/equipamentos/', 'fas fa-tools', 100),
('manutencao.horimetro', 'Horímetro', 'Controle de horímetro', 'Manutenção', 'hour_meter.hour_meter_list', '/horimetro/', 'fas fa-clock', 101),
('manutencao.planos', 'Planos de Manutenção', 'Planos preventivos', 'Manutenção', 'maintenance_plan.maintenance_plan_list', '/planos-manutencao/', 'fas fa-clipboard-list', 102),
('manutencao.calendario', 'Calendário Manutenção', 'Calendário de manutenções', 'Manutenção', 'maintenance_plan.maintenance_plan_calendar', '/planos-manutencao/calendario', 'fas fa-calendar-alt', 103),
('manutencao.ordens', 'Ordens de Serviço', 'Gerenciar OS', 'Manutenção', 'service_order.service_order_list', '/ordens-servico/', 'fas fa-tools', 104),
('manutencao.tecnicos', 'Técnicos', 'Cadastro de técnicos', 'Manutenção', 'technician.technicians_list', '/tecnicos/', 'fas fa-users-cog', 105),

-- Administração
('admin.empresas', 'Empresas', 'Gerenciar empresas', 'Administração', 'empresa.empresas', '/empresas/', 'fas fa-building', 110),
('admin.usuarios', 'Usuários', 'Gerenciar usuários', 'Administração', 'usuario.usuarios', '/usuarios/', 'fas fa-user-cog', 111),
('admin.permissoes', 'Permissões de Usuário', 'Configurar permissões', 'Administração', 'permissoes.lista', '/admin/permissoes/', 'fas fa-shield-alt', 112),
('admin.config_pdv', 'Configurações PDV', 'Configurar PDV', 'Administração', 'pdv_config.configuracoes', '/pdv/config/', 'fas fa-cash-register', 113),
('admin.importar_clientes', 'Importar Clientes', 'Importar clientes via arquivo', 'Administração', 'importar_clientes.importar_clientes_form', '/importar-clientes/', 'fas fa-file-import', 114),
('admin.importar_nfe', 'Importar XML (NFe)', 'Importar XMLs de NF-e', 'Administração', 'nfe_upload.importar_nfe_upload_page', '/importar-nfe/', 'fas fa-file-invoice', 115),
('admin.config_email_nfe', 'Config. Email NF-e', 'Configurar envio de email', 'Administração', 'nfe_emissao.config_email_nfe', '/nfe/config-email', 'fas fa-envelope-open-text', 116),
('admin.numeracao_nfe', 'Numeração NF-e', 'Configurar numeração', 'Administração', 'nfe_emissao.numeracao_config', '/nfe/numeracao', 'fas fa-hashtag', 117),
('admin.teste_nfce', 'Teste NFC-e', 'Testar NFC-e homologação', 'Administração', 'nfce.pagina_teste_homologacao', '/nfce/teste', 'fas fa-flask', 118)

ON DUPLICATE KEY UPDATE 
    nome = VALUES(nome),
    descricao = VALUES(descricao),
    modulo = VALUES(modulo),
    rota_flask = VALUES(rota_flask),
    url_padrao = VALUES(url_padrao),
    icone = VALUES(icone),
    ordem = VALUES(ordem);

-- 4. Criar view para consulta de permissões
CREATE OR REPLACE VIEW vw_usuario_permissoes AS
SELECT 
    up.id,
    up.usuario_id,
    u.name as usuario_nome,
    u.username,
    up.tela_id,
    st.codigo as tela_codigo,
    st.nome as tela_nome,
    st.modulo,
    st.rota_flask,
    st.url_padrao,
    st.icone,
    up.pode_visualizar,
    up.pode_criar,
    up.pode_editar,
    up.pode_excluir,
    CASE 
        WHEN up.pode_visualizar = 1 AND up.pode_criar = 1 AND up.pode_editar = 1 AND up.pode_excluir = 1 THEN 'Acesso Total'
        WHEN up.pode_visualizar = 1 AND up.pode_criar = 0 AND up.pode_editar = 0 AND up.pode_excluir = 0 THEN 'Somente Visualizar'
        WHEN up.pode_visualizar = 1 AND up.pode_criar = 1 AND up.pode_editar = 0 AND up.pode_excluir = 0 THEN 'Visualizar e Criar'
        WHEN up.pode_visualizar = 1 AND up.pode_criar = 1 AND up.pode_editar = 1 AND up.pode_excluir = 0 THEN 'Sem Exclusão'
        ELSE 'Personalizado'
    END as tipo_acesso
FROM usuario_permissoes up
JOIN users u ON u.id = up.usuario_id
JOIN sistema_telas st ON st.id = up.tela_id
WHERE st.ativo = 1;

-- 5. Procedure para copiar permissões de um usuário para outro
DELIMITER //
DROP PROCEDURE IF EXISTS sp_copiar_permissoes//
CREATE PROCEDURE sp_copiar_permissoes(
    IN p_usuario_origem_id INT,
    IN p_usuario_destino_id INT,
    IN p_created_by INT
)
BEGIN
    -- Remove permissões existentes do destino
    DELETE FROM usuario_permissoes WHERE usuario_id = p_usuario_destino_id;
    
    -- Copia permissões da origem para o destino
    INSERT INTO usuario_permissoes (usuario_id, tela_id, pode_visualizar, pode_criar, pode_editar, pode_excluir, created_by)
    SELECT 
        p_usuario_destino_id,
        tela_id,
        pode_visualizar,
        pode_criar,
        pode_editar,
        pode_excluir,
        p_created_by
    FROM usuario_permissoes
    WHERE usuario_id = p_usuario_origem_id;
    
    SELECT ROW_COUNT() as permissoes_copiadas;
END//

-- 6. Procedure para dar acesso total a um usuário
DROP PROCEDURE IF EXISTS sp_acesso_total_usuario//
CREATE PROCEDURE sp_acesso_total_usuario(
    IN p_usuario_id INT,
    IN p_created_by INT
)
BEGIN
    -- Remove permissões existentes
    DELETE FROM usuario_permissoes WHERE usuario_id = p_usuario_id;
    
    -- Insere acesso total para todas as telas ativas
    INSERT INTO usuario_permissoes (usuario_id, tela_id, pode_visualizar, pode_criar, pode_editar, pode_excluir, created_by)
    SELECT 
        p_usuario_id,
        id,
        1, 1, 1, 1,
        p_created_by
    FROM sistema_telas
    WHERE ativo = 1;
    
    SELECT ROW_COUNT() as telas_liberadas;
END//

DELIMITER ;

-- 7. Dar acesso total ao admin (user_id = 1)
CALL sp_acesso_total_usuario(1, 1);

-- 8. Mensagem de conclusão
SELECT 'Script 069_PERMISSOES_USUARIO.sql executado com sucesso!' as resultado;
SELECT COUNT(*) as total_telas FROM sistema_telas WHERE ativo = 1;
SELECT COUNT(*) as total_permissoes FROM usuario_permissoes;
