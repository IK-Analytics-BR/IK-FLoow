-- Script para excluir tabelas redundantes e padronizar o uso das tabelas de pedidos de compra
-- IMPORTANTE: Faça um backup do banco de dados antes de executar este script

-- Verificar se a tabela order_items não está sendo usada
SELECT COUNT(*) FROM order_items;

-- Se o resultado for 0, você pode excluir a tabela
DROP TABLE IF EXISTS order_items;

-- Verificar se há alguma coluna total_amount na tabela purchase_orders
DESCRIBE purchase_orders;

-- Verificar se há alguma referência a total_amount em outras consultas
-- Se necessário, você pode criar uma view para compatibilidade
CREATE OR REPLACE VIEW purchase_orders_view AS
SELECT 
    po.*,
    po.total_value as total_amount
FROM 
    purchase_orders po;

-- Verificar se a view foi criada corretamente
SELECT * FROM purchase_orders_view LIMIT 1;
