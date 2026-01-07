"""
Script para executar a migration de permissões de usuário.
Cria as tabelas sistema_telas e usuario_permissoes.
"""
import pymysql
import sys

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'aritana',
    'database': 'supply_chain_system',
    'charset': 'utf8mb4'
}

def executar_migration():
    print("=" * 60)
    print("MIGRATION: Sistema de Permissoes de Usuario")
    print("=" * 60)
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 1. Criar tabela sistema_telas
        print("\n[1] Criando tabela sistema_telas...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sistema_telas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                codigo VARCHAR(100) NOT NULL UNIQUE,
                nome VARCHAR(150) NOT NULL,
                descricao VARCHAR(255) NULL,
                modulo VARCHAR(50) NOT NULL,
                rota_flask VARCHAR(200) NULL,
                url_padrao VARCHAR(200) NULL,
                icone VARCHAR(50) DEFAULT 'fas fa-file',
                ordem INT DEFAULT 0,
                ativo TINYINT(1) DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_modulo (modulo),
                INDEX idx_ativo (ativo)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("   [OK] Tabela sistema_telas criada/verificada")
        
        # 2. Criar tabela usuario_permissoes
        print("\n[2] Criando tabela usuario_permissoes...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuario_permissoes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                usuario_id INT NOT NULL,
                tela_id INT NOT NULL,
                pode_visualizar TINYINT(1) DEFAULT 0,
                pode_criar TINYINT(1) DEFAULT 0,
                pode_editar TINYINT(1) DEFAULT 0,
                pode_excluir TINYINT(1) DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                created_by INT NULL,
                UNIQUE KEY uk_usuario_tela (usuario_id, tela_id),
                INDEX idx_usuario (usuario_id),
                INDEX idx_tela (tela_id),
                FOREIGN KEY (usuario_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (tela_id) REFERENCES sistema_telas(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("   [OK] Tabela usuario_permissoes criada/verificada")
        
        # 3. Inserir telas do sistema
        print("\n[3] Inserindo telas do sistema...")
        telas = [
            # Dashboard
            ('dashboard', 'Dashboard', 'Painel principal do sistema', 'Dashboard', 'dashboard', '/', 'fas fa-home', 1),
            
            # Vendas
            ('vendas.orcamentos', 'Orcamentos', 'Gerenciar orcamentos', 'Vendas', 'orcamentos.lista', '/orcamentos/', 'fas fa-file-invoice-dollar', 10),
            ('vendas.lista_preco', 'Listas de Preco', 'Gerenciar listas de preco', 'Vendas', 'lista_preco.lista', '/lista-preco/', 'fas fa-tags', 11),
            ('vendas.pdv', 'PDV / Venda', 'Ponto de venda', 'Vendas', 'venda.venda_pdv_moderna', '/pdv/', 'fas fa-cash-register', 12),
            ('vendas.caixa', 'Caixa', 'Controle de caixa', 'Vendas', None, '/caixa/atual', 'fas fa-dollar-sign', 13),
            ('vendas.rotas', 'Rotas de Vendas', 'Gerenciar rotas de vendas', 'Vendas', 'rota_vendas.rotas_vendas_list', '/rotas-vendas/', 'fas fa-route', 14),
            ('vendas.vendedores', 'Vendedores', 'Cadastro de vendedores', 'Vendas', 'vendedor.vendedores', '/vendedores/', 'fas fa-user-tie', 15),
            ('vendas.romaneio', 'Romaneio', 'Gerenciar romaneios', 'Vendas', 'romaneio.romaneio_list', '/romaneio/', 'fas fa-clipboard-list', 16),
            ('vendas.nfe_pendentes', 'NF-e Pendentes', 'Vendas pendentes de NF-e', 'Vendas', 'nfe_emissao.vendas_pendentes', '/nfe/vendas-pendentes', 'fas fa-clock', 17),
            ('vendas.nfe_emitir', 'Emitir NF-e', 'Emitir NF-e manual', 'Vendas', 'nfe_emissao.emitir_manual', '/nfe/emitir', 'fas fa-file-invoice', 18),
            ('vendas.nfe_historico', 'Historico NF-e', 'Historico de NF-e emitidas', 'Vendas', 'nfe_emissao.historico', '/nfe/historico', 'fas fa-history', 19),
            ('vendas.relacao', 'Relacao de Vendas', 'Relatorio de vendas', 'Vendas', 'venda.vendas_relacao', '/vendas/relacao', 'fas fa-list', 20),
            
            # Clientes
            ('clientes.lista', 'Clientes', 'Cadastro de clientes', 'Clientes', 'cliente.clientes', '/clientes/', 'fas fa-user-check', 30),
            ('clientes.potenciais', 'Clientes em Potencial', 'Leads e prospects', 'Clientes', 'clientes_potenciais.lista', '/clientes-potenciais/', 'fas fa-user-plus', 31),
            ('clientes.segmentos', 'Segmentos', 'Segmentos de clientes', 'Clientes', 'segment.segmentos', '/segmentos/', 'fas fa-layer-group', 32),
            
            # Produtos e Estoque
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
            ('estoque.kardex', 'Kardex', 'Historico de movimentacoes', 'Produtos', 'kardex.kardex_index', '/kardex/', 'fas fa-history', 51),
            ('produtos.fichas_tecnicas', 'Fichas Tecnicas', 'Fichas tecnicas de produtos', 'Produtos', 'ficha_tecnica.listar', '/fichas-tecnicas/', 'fas fa-clipboard-list', 52),
            
            # Industria
            ('industria.ops', 'Ordens de Producao', 'Gerenciar OPs', 'Industria', 'ordem_producao.listar_ops', '/industria/ordem-producao/', 'fas fa-tasks', 60),
            ('industria.gantt', 'Producao (Gantt)', 'Visualizacao Gantt', 'Industria', 'ordem_producao.producao_gantt', '/industria/ordem-producao/producao/gantt', 'fas fa-project-diagram', 61),
            ('industria.minha_producao', 'Minha Producao', 'Producao do operador', 'Industria', 'ordem_producao.meu_gantt', '/industria/ordem-producao/meu-gantt', 'fas fa-hard-hat', 62),
            ('industria.etapas', 'Etapas de Producao', 'Cadastro de etapas', 'Industria', 'ordem_producao.etapas_lista', '/industria/ordem-producao/etapas', 'fas fa-stream', 63),
            ('industria.grupos_etapas', 'Grupos de Etapas', 'Grupos de etapas', 'Industria', 'ordem_producao.etapas_grupos_lista', '/industria/ordem-producao/etapas/grupos', 'fas fa-layer-group', 64),
            ('industria.jornada', 'Jornada de Trabalho', 'Configurar jornadas', 'Industria', 'jornada_trabalho.listar_jornadas', '/jornadas/', 'fas fa-clock', 65),
            ('industria.dashboard_gargalos', 'Dashboard Gargalos', 'Analise de gargalos', 'Industria', 'config_producao.dashboard_producao', '/industria/config/dashboard', 'fas fa-chart-line', 66),
            ('industria.tempos', 'Tempos de Producao', 'Configurar tempos', 'Industria', 'config_producao.tempos_producao', '/industria/config/tempos-producao', 'fas fa-stopwatch', 67),
            ('industria.feriados', 'Feriados', 'Cadastro de feriados', 'Industria', 'config_producao.feriados', '/industria/config/feriados', 'fas fa-calendar-times', 68),
            ('industria.capacidade', 'Capacidade Etapas', 'Capacidade por etapa', 'Industria', 'config_producao.capacidade_etapas', '/industria/config/capacidade-etapas', 'fas fa-tachometer-alt', 69),
            ('industria.painel_lider', 'Painel do Lider', 'Painel do lider de equipe', 'Industria', 'ordem_producao.lider_painel', '/industria/ordem-producao/lider/painel', 'fas fa-user-tie', 70),
            ('industria.gerenciar_equipe', 'Gerenciar Equipe', 'Gerenciar equipe de producao', 'Industria', 'ordem_producao.lider_gerenciar_equipe', '/industria/ordem-producao/lider/gerenciar-equipe', 'fas fa-users-cog', 71),
            
            # Compras
            ('compras.fornecedores', 'Fornecedores', 'Cadastro de fornecedores', 'Compras', 'fornecedor.fornecedores', '/fornecedores/', 'fas fa-truck', 80),
            ('compras.entrada', 'Entrada de Produtos', 'Entrada de notas fiscais', 'Compras', 'invoice.invoice_create', '/entrada/', 'fas fa-inbox', 81),
            ('compras.pedidos', 'Pedidos de Compra', 'Gerenciar pedidos', 'Compras', 'purchase_order.purchase_orders_list', '/pedidos-compra/', 'fas fa-file-invoice', 82),
            ('compras.transportadoras', 'Transportadoras', 'Cadastro de transportadoras', 'Compras', 'transportadoras.lista', '/transportadoras/', 'fas fa-truck-moving', 83),
            
            # Financeiro
            ('financeiro.contas_bancarias', 'Contas Bancarias', 'Gerenciar contas', 'Financeiro', 'bank_account.bank_accounts_list', '/contas-bancarias/', 'fas fa-university', 90),
            ('financeiro.contas_pagar', 'Contas a Pagar', 'Gerenciar pagamentos', 'Financeiro', 'accounts_payable.accounts_payable_list', '/contas-pagar/', 'fas fa-file-invoice-dollar', 91),
            ('financeiro.contas_receber', 'Contas a Receber', 'Gerenciar recebimentos', 'Financeiro', 'accounts_receivable.accounts_receivable_list', '/contas-receber/', 'fas fa-hand-holding-usd', 92),
            ('financeiro.fluxo_caixa', 'Fluxo de Caixa', 'Dashboard financeiro', 'Financeiro', 'cash_flow.cash_flow_dashboard', '/fluxo-caixa/', 'fas fa-chart-line', 93),
            ('financeiro.plano_contas', 'Plano de Contas', 'Estrutura contabil', 'Financeiro', 'chart_of_accounts.chart_of_accounts_list', '/plano-contas/', 'fas fa-book', 94),
            ('financeiro.historico_caixas', 'Historico de Caixas', 'Historico de caixas', 'Financeiro', None, '/caixa', 'fas fa-cash-register', 95),
            ('financeiro.formas_pagamento', 'Formas de Pagamento', 'Configurar formas', 'Financeiro', 'payment_config.payment_config_list', '/formas-pagamento/', 'fas fa-credit-card', 96),
            ('financeiro.condicoes_pagamento', 'Condicoes de Pagamento', 'Configurar condicoes', 'Financeiro', 'condicoes_pagamento.lista', '/condicoes-pagamento/', 'fas fa-calendar-alt', 97),
            
            # Manutencao
            ('manutencao.equipamentos', 'Equipamentos', 'Cadastro de equipamentos', 'Manutencao', 'equipamento.equipamentos', '/equipamentos/', 'fas fa-tools', 100),
            ('manutencao.horimetro', 'Horimetro', 'Controle de horimetro', 'Manutencao', 'hour_meter.hour_meter_list', '/horimetro/', 'fas fa-clock', 101),
            ('manutencao.planos', 'Planos de Manutencao', 'Planos preventivos', 'Manutencao', 'maintenance_plan.maintenance_plan_list', '/planos-manutencao/', 'fas fa-clipboard-list', 102),
            ('manutencao.calendario', 'Calendario Manutencao', 'Calendario de manutencoes', 'Manutencao', 'maintenance_plan.maintenance_plan_calendar', '/planos-manutencao/calendario', 'fas fa-calendar-alt', 103),
            ('manutencao.ordens', 'Ordens de Servico', 'Gerenciar OS', 'Manutencao', 'service_order.service_order_list', '/ordens-servico/', 'fas fa-tools', 104),
            ('manutencao.tecnicos', 'Tecnicos', 'Cadastro de tecnicos', 'Manutencao', 'technician.technicians_list', '/tecnicos/', 'fas fa-users-cog', 105),
            
            # Administracao
            ('admin.empresas', 'Empresas', 'Gerenciar empresas', 'Administracao', 'empresa.empresas', '/empresas/', 'fas fa-building', 110),
            ('admin.usuarios', 'Usuarios', 'Gerenciar usuarios', 'Administracao', 'usuario.usuarios', '/usuarios/', 'fas fa-user-cog', 111),
            ('admin.permissoes', 'Permissoes de Usuario', 'Configurar permissoes', 'Administracao', 'permissoes.lista', '/admin/permissoes/', 'fas fa-shield-alt', 112),
            ('admin.config_pdv', 'Configuracoes PDV', 'Configurar PDV', 'Administracao', 'pdv_config.configuracoes', '/pdv/config/', 'fas fa-cash-register', 113),
            ('admin.importar_clientes', 'Importar Clientes', 'Importar clientes via arquivo', 'Administracao', 'importar_clientes.importar_clientes_form', '/importar-clientes/', 'fas fa-file-import', 114),
            ('admin.importar_nfe', 'Importar XML (NFe)', 'Importar XMLs de NF-e', 'Administracao', 'nfe_upload.importar_nfe_upload_page', '/importar-nfe/', 'fas fa-file-invoice', 115),
            ('admin.config_email_nfe', 'Config. Email NF-e', 'Configurar envio de email', 'Administracao', 'nfe_emissao.config_email_nfe', '/nfe/config-email', 'fas fa-envelope-open-text', 116),
            ('admin.numeracao_nfe', 'Numeracao NF-e', 'Configurar numeracao', 'Administracao', 'nfe_emissao.numeracao_config', '/nfe/numeracao', 'fas fa-hashtag', 117),
            ('admin.teste_nfce', 'Teste NFC-e', 'Testar NFC-e homologacao', 'Administracao', 'nfce.pagina_teste_homologacao', '/nfce/teste', 'fas fa-flask', 118),
        ]
        
        for tela in telas:
            cursor.execute("""
                INSERT INTO sistema_telas (codigo, nome, descricao, modulo, rota_flask, url_padrao, icone, ordem)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    nome = VALUES(nome),
                    descricao = VALUES(descricao),
                    modulo = VALUES(modulo),
                    rota_flask = VALUES(rota_flask),
                    url_padrao = VALUES(url_padrao),
                    icone = VALUES(icone),
                    ordem = VALUES(ordem)
            """, tela)
        
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM sistema_telas")
        total_telas = cursor.fetchone()[0]
        print(f"   [OK] {total_telas} telas inseridas/atualizadas")
        
        # 4. Dar acesso total ao admin (user_id = 1)
        print("\n[4] Concedendo acesso total ao admin (user_id = 1)...")
        cursor.execute("DELETE FROM usuario_permissoes WHERE usuario_id = 1")
        cursor.execute("""
            INSERT INTO usuario_permissoes (usuario_id, tela_id, pode_visualizar, pode_criar, pode_editar, pode_excluir, created_by)
            SELECT 1, id, 1, 1, 1, 1, 1
            FROM sistema_telas
            WHERE ativo = 1
        """)
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM usuario_permissoes WHERE usuario_id = 1")
        total_perm = cursor.fetchone()[0]
        print(f"   [OK] {total_perm} permissoes concedidas ao admin")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Migration executada com sucesso!")
        print("=" * 60)
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Erro ao executar migration: {e}")
        return False

if __name__ == '__main__':
    success = executar_migration()
    sys.exit(0 if success else 1)
