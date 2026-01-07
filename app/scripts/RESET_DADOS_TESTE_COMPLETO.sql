-- =============================================================
-- RESET_DADOS_TESTE_COMPLETO.sql
-- Limpa dados transacionais para testes fim-a-fim
-- Preserva: usuário admin, formas de pagamento, parâmetros fixos
-- =============================================================

USE supply_chain_system;

-- IMPORTANTE: execute apenas em AMBIENTE DE TESTE
-- Revise a lista de tabelas antes de rodar em produção.

SET FOREIGN_KEY_CHECKS = 0;

-- =============================================================
-- =============================================================

-- Logs de sessão/atividade
DELETE FROM sessions;
DELETE FROM activity_logs;

-- Relação de permissões (mantém apenas vínculos do admin)
DELETE FROM user_permissions;

-- Usuários (mantém apenas admin)
DELETE FROM users
WHERE username <> 'admin';

-- Se existir módulo legado de usuários (ajuste o nome da tabela se diferente)
-- DELETE FROM usuarios WHERE id <> 1;

-- =============================================================
-- 2) CADASTROS OPERACIONAIS (CLIENTES, FORNECEDORES, EQUIPAMENTOS)
-- =============================================================

-- Clientes e fornecedores de testes
DELETE FROM service_order_labor;
DELETE FROM service_order_items;
DELETE FROM service_orders;
DELETE FROM maintenance_plans;
DELETE FROM equipment;
DELETE FROM supplies;
DELETE FROM customers;
DELETE FROM suppliers;

DELETE FROM hour_meter_readings;
DELETE FROM technicians;

DELETE FROM alerts;

-- =============================================================
-- =============================================================

-- Novo sistema de estoque por empresa
-- (ajuste nomes se sua instalação usar variações)

-- Reservas / movimentos
DELETE FROM estoque_reservas;
DELETE FROM estoque_movimentacoes;

-- Tabela consolidada por empresa
DELETE FROM estoque_empresa;

-- Kardex / views materializadas (se existirem como tabelas físicas)
-- DELETE FROM vw_kardex_empresa;   -- normalmente é VIEW, não limpar aqui

-- Estoque antigo baseado em stock_*
DELETE FROM inventory_count_items;
DELETE FROM inventory_counts;
DELETE FROM stock_movements;
DELETE FROM current_stock;

DELETE FROM products;

-- Hierarquia de produtos / modelos / vínculos com cliente
DELETE FROM customer_product_children_status;
DELETE FROM customer_products;
DELETE FROM product_children;
DELETE FROM product_models;

-- Categorias, NCM, CFOP etc. são parâmetros: NÃO limpar
-- Ex.: product_categories, ncm, cfop, etc.

-- =============================================================
-- =============================================================

-- Pagamentos por venda
DELETE FROM sale_payments;

-- Itens de venda e vendas
DELETE FROM sale_items;
DELETE FROM sales;

-- Romaneios (sistema de rotas, romaneios e pedidos externos)
DELETE FROM order_items;
DELETE FROM manifest_orders;
DELETE FROM manifest_visits;
DELETE FROM sales_manifests;
DELETE FROM route_customer;
DELETE FROM sales_routes;
DELETE FROM seller_customer;
DELETE FROM sellers;

-- Caixa
DELETE FROM cash_register_movements;
DELETE FROM cash_register;

-- =============================================================
-- =============================================================

-- Parcelas
DELETE FROM receivable_installments;
DELETE FROM payable_installments;

-- Títulos
DELETE FROM accounts_receivable;
DELETE FROM accounts_payable;

-- Fluxo de caixa e alertas
DELETE FROM cash_flow;
DELETE FROM financial_alerts;

-- Contas bancárias fazem parte da empresa: ZERAR
DELETE FROM bank_accounts;

-- Formas de pagamento SÃO PARÂMETROS: NÃO limpar (payment_methods_config)

-- =============================================================
-- =============================================================

DELETE FROM orcamento_historico;
DELETE FROM orcamento_duplicatas;
DELETE FROM orcamento_itens;
DELETE FROM orcamentos;

-- Tabelas auxiliares de integração com OP (se existirem)
-- Ajuste se houver outras tabelas relacionadas
DELETE FROM orcamento_op_itens;
DELETE FROM orcamento_op_grupos;

-- =============================================================
-- =============================================================

-- Templates de produção, etapas, OPs, lotes, pausas, operadores, previsões
DELETE FROM ordem_producao_itens;
DELETE FROM ordens_producao;
DELETE FROM produto_template_itens;
DELETE FROM produto_templates_producao;
DELETE FROM producao_pausas;
DELETE FROM op_lotes;
DELETE FROM producao_etapas;
DELETE FROM produtos_tempo_etapa;
DELETE FROM config_capacidade_etapa;
DELETE FROM log_calculo_previsao;

-- Estrutura de líderes / equipe / operadores por etapa
DELETE FROM etapa_operadores;
DELETE FROM lider_etapas;
DELETE FROM lider_operadores;

-- Jornadas de trabalho e horários
DELETE FROM jornada_horarios;
DELETE FROM jornadas_trabalho;

-- Feriados / folgas
DELETE FROM config_feriados;

-- =============================================================
-- =============================================================

-- Logs de importação
DELETE FROM nfe_entrada_import_log;

-- Staging
DELETE FROM nfe_entrada_staging_itens;
DELETE FROM nfe_entrada_staging_notas;

-- Pedidos de compra, notas e itens gerados a partir das NF-e de entrada
-- (ajuste o critério conforme seus campos de vínculo)
-- Exemplo usando nfe_entrada_staging_id:
DELETE FROM purchase_invoice_items;
DELETE FROM purchase_invoices;
DELETE FROM purchase_order_items;
DELETE FROM purchase_orders;

-- Histórico de importação XML e relações de compras
DELETE FROM xml_imports;
DELETE FROM price_history;
DELETE FROM supplier_products;
DELETE FROM purchase_suggestions;

-- Módulo genérico de Notas Fiscais (se usado)
DELETE FROM invoice_items;
DELETE FROM invoices;

-- =============================================================
-- =============================================================

-- Staging genérico de NF-e saída
DELETE FROM nfe_staging_itens;
DELETE FROM nfe_staging_notas;

-- Numeração e configuração de NF-e / email / logs
DELETE FROM nfe_numeracao;
DELETE FROM email_log_nfe;
DELETE FROM email_config_nfe;

-- =============================================================
-- =============================================================

-- Tabelas temporárias/derivadas da Receita Federal
DELETE FROM empresas_filtradas;
DELETE FROM empresas_receita;

-- Tabela de empresas cadastradas no sistema (zerar tudo)
DELETE FROM empresas;

-- Se houver geocodificações específicas de empresas/leads, limpe aqui
-- Ex.: campos latitude/longitude já são limpos com empresas_filtradas

-- =============================================================
-- =============================================================

-- Logs de alertas, notificações, rotas de venda, etc.
-- alerts já foi limpo; inclua aqui outras tabelas de log se existirem.

SET FOREIGN_KEY_CHECKS = 1;

-- FIM DO SCRIPT
