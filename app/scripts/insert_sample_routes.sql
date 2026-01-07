-- Script para inserir dados de exemplo para rotas de vendas
-- Inserir 10 rotas de vendas com dados fictícios

-- Verificar se já existem rotas cadastradas
SELECT COUNT(*) AS count FROM sales_routes;

-- Inserir rotas de vendas (uma para cada vendedor)
-- Usamos a data atual para gerar códigos únicos
SET @current_date = CURDATE();
SET @date_code = DATE_FORMAT(@current_date, '%Y%m%d');

-- Rota 1 - João Silva (Norte)
INSERT INTO sales_routes (code, name, seller_id, frequency, active)
SELECT CONCAT('R-', @date_code, '-001'), 'Rota Norte Capital', id, 'weekly', TRUE
FROM sellers WHERE name = 'João Silva' LIMIT 1;

-- Rota 2 - Maria Oliveira (Sul)
INSERT INTO sales_routes (code, name, seller_id, frequency, active)
SELECT CONCAT('R-', @date_code, '-002'), 'Rota Sul Metropolitana', id, 'weekly', TRUE
FROM sellers WHERE name = 'Maria Oliveira' LIMIT 1;

-- Rota 3 - Pedro Santos (Leste)
INSERT INTO sales_routes (code, name, seller_id, frequency, active)
SELECT CONCAT('R-', @date_code, '-003'), 'Rota Leste Comercial', id, 'daily', TRUE
FROM sellers WHERE name = 'Pedro Santos' LIMIT 1;

-- Rota 4 - Ana Costa (Oeste)
INSERT INTO sales_routes (code, name, seller_id, frequency, active)
SELECT CONCAT('R-', @date_code, '-004'), 'Rota Oeste Industrial', id, 'weekly', TRUE
FROM sellers WHERE name = 'Ana Costa' LIMIT 1;

-- Rota 5 - Carlos Pereira (Centro)
INSERT INTO sales_routes (code, name, seller_id, frequency, active)
SELECT CONCAT('R-', @date_code, '-005'), 'Rota Centro Histórico', id, 'daily', TRUE
FROM sellers WHERE name = 'Carlos Pereira' LIMIT 1;

-- Rota 6 - Fernanda Lima (Nordeste)
INSERT INTO sales_routes (code, name, seller_id, frequency, active)
SELECT CONCAT('R-', @date_code, '-006'), 'Rota Nordeste Praias', id, 'weekly', TRUE
FROM sellers WHERE name = 'Fernanda Lima' LIMIT 1;

-- Rota 7 - Ricardo Souza (Sudeste)
INSERT INTO sales_routes (code, name, seller_id, frequency, active)
SELECT CONCAT('R-', @date_code, '-007'), 'Rota Sudeste Montanhas', id, 'monthly', TRUE
FROM sellers WHERE name = 'Ricardo Souza' LIMIT 1;

-- Rota 8 - Juliana Martins (Noroeste)
INSERT INTO sales_routes (code, name, seller_id, frequency, active)
SELECT CONCAT('R-', @date_code, '-008'), 'Rota Noroeste Rural', id, 'weekly', TRUE
FROM sellers WHERE name = 'Juliana Martins' LIMIT 1;

-- Rota 9 - Roberto Almeida (Sudoeste)
INSERT INTO sales_routes (code, name, seller_id, frequency, active)
SELECT CONCAT('R-', @date_code, '-009'), 'Rota Sudoeste Fazendas', id, 'monthly', TRUE
FROM sellers WHERE name = 'Roberto Almeida' LIMIT 1;

-- Rota 10 - Patrícia Ferreira (Centro-Oeste)
INSERT INTO sales_routes (code, name, seller_id, frequency, active)
SELECT CONCAT('R-', @date_code, '-010'), 'Rota Centro-Oeste Agronegócio', id, 'weekly', TRUE
FROM sellers WHERE name = 'Patrícia Ferreira' LIMIT 1;

-- Verificar se as rotas foram inseridas
SELECT r.id, r.code, r.name, s.name as seller_name, r.frequency
FROM sales_routes r
JOIN sellers s ON r.seller_id = s.id
ORDER BY r.id;

-- Agora vamos vincular os clientes às rotas
-- Para cada rota, vincular os mesmos clientes que estão vinculados ao vendedor

-- Rota 1 - João Silva (Norte)
INSERT INTO route_customer (route_id, customer_id, visit_order)
SELECT 
    (SELECT r.id FROM sales_routes r JOIN sellers s ON r.seller_id = s.id WHERE s.name = 'João Silva' LIMIT 1) as route_id,
    sc.customer_id,
    ROW_NUMBER() OVER (ORDER BY sc.customer_id) as visit_order
FROM seller_customer sc
JOIN sellers s ON sc.seller_id = s.id
WHERE s.name = 'João Silva';

-- Rota 2 - Maria Oliveira (Sul)
INSERT INTO route_customer (route_id, customer_id, visit_order)
SELECT 
    (SELECT r.id FROM sales_routes r JOIN sellers s ON r.seller_id = s.id WHERE s.name = 'Maria Oliveira' LIMIT 1) as route_id,
    sc.customer_id,
    ROW_NUMBER() OVER (ORDER BY sc.customer_id) as visit_order
FROM seller_customer sc
JOIN sellers s ON sc.seller_id = s.id
WHERE s.name = 'Maria Oliveira';

-- Rota 3 - Pedro Santos (Leste)
INSERT INTO route_customer (route_id, customer_id, visit_order)
SELECT 
    (SELECT r.id FROM sales_routes r JOIN sellers s ON r.seller_id = s.id WHERE s.name = 'Pedro Santos' LIMIT 1) as route_id,
    sc.customer_id,
    ROW_NUMBER() OVER (ORDER BY sc.customer_id) as visit_order
FROM seller_customer sc
JOIN sellers s ON sc.seller_id = s.id
WHERE s.name = 'Pedro Santos';

-- Rota 4 - Ana Costa (Oeste)
INSERT INTO route_customer (route_id, customer_id, visit_order)
SELECT 
    (SELECT r.id FROM sales_routes r JOIN sellers s ON r.seller_id = s.id WHERE s.name = 'Ana Costa' LIMIT 1) as route_id,
    sc.customer_id,
    ROW_NUMBER() OVER (ORDER BY sc.customer_id) as visit_order
FROM seller_customer sc
JOIN sellers s ON sc.seller_id = s.id
WHERE s.name = 'Ana Costa';

-- Rota 5 - Carlos Pereira (Centro)
INSERT INTO route_customer (route_id, customer_id, visit_order)
SELECT 
    (SELECT r.id FROM sales_routes r JOIN sellers s ON r.seller_id = s.id WHERE s.name = 'Carlos Pereira' LIMIT 1) as route_id,
    sc.customer_id,
    ROW_NUMBER() OVER (ORDER BY sc.customer_id) as visit_order
FROM seller_customer sc
JOIN sellers s ON sc.seller_id = s.id
WHERE s.name = 'Carlos Pereira';

-- Rota 6 - Fernanda Lima (Nordeste)
INSERT INTO route_customer (route_id, customer_id, visit_order)
SELECT 
    (SELECT r.id FROM sales_routes r JOIN sellers s ON r.seller_id = s.id WHERE s.name = 'Fernanda Lima' LIMIT 1) as route_id,
    sc.customer_id,
    ROW_NUMBER() OVER (ORDER BY sc.customer_id) as visit_order
FROM seller_customer sc
JOIN sellers s ON sc.seller_id = s.id
WHERE s.name = 'Fernanda Lima';

-- Rota 7 - Ricardo Souza (Sudeste)
INSERT INTO route_customer (route_id, customer_id, visit_order)
SELECT 
    (SELECT r.id FROM sales_routes r JOIN sellers s ON r.seller_id = s.id WHERE s.name = 'Ricardo Souza' LIMIT 1) as route_id,
    sc.customer_id,
    ROW_NUMBER() OVER (ORDER BY sc.customer_id) as visit_order
FROM seller_customer sc
JOIN sellers s ON sc.seller_id = s.id
WHERE s.name = 'Ricardo Souza';

-- Rota 8 - Juliana Martins (Noroeste)
INSERT INTO route_customer (route_id, customer_id, visit_order)
SELECT 
    (SELECT r.id FROM sales_routes r JOIN sellers s ON r.seller_id = s.id WHERE s.name = 'Juliana Martins' LIMIT 1) as route_id,
    sc.customer_id,
    ROW_NUMBER() OVER (ORDER BY sc.customer_id) as visit_order
FROM seller_customer sc
JOIN sellers s ON sc.seller_id = s.id
WHERE s.name = 'Juliana Martins';

-- Rota 9 - Roberto Almeida (Sudoeste)
INSERT INTO route_customer (route_id, customer_id, visit_order)
SELECT 
    (SELECT r.id FROM sales_routes r JOIN sellers s ON r.seller_id = s.id WHERE s.name = 'Roberto Almeida' LIMIT 1) as route_id,
    sc.customer_id,
    ROW_NUMBER() OVER (ORDER BY sc.customer_id) as visit_order
FROM seller_customer sc
JOIN sellers s ON sc.seller_id = s.id
WHERE s.name = 'Roberto Almeida';

-- Rota 10 - Patrícia Ferreira (Centro-Oeste)
INSERT INTO route_customer (route_id, customer_id, visit_order)
SELECT 
    (SELECT r.id FROM sales_routes r JOIN sellers s ON r.seller_id = s.id WHERE s.name = 'Patrícia Ferreira' LIMIT 1) as route_id,
    sc.customer_id,
    ROW_NUMBER() OVER (ORDER BY sc.customer_id) as visit_order
FROM seller_customer sc
JOIN sellers s ON sc.seller_id = s.id
WHERE s.name = 'Patrícia Ferreira';

-- Verificar as associações entre rotas e clientes
SELECT r.code, r.name as route_name, s.name as seller_name, c.name as customer_name, rc.visit_order
FROM route_customer rc
JOIN sales_routes r ON rc.route_id = r.id
JOIN sellers s ON r.seller_id = s.id
JOIN customers c ON rc.customer_id = c.id
ORDER BY r.name, rc.visit_order;
