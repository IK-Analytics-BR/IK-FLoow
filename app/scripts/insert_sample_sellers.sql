-- Script para inserir dados de exemplo para vendedores
-- Inserir 10 vendedores com dados fictícios

-- Verificar se já existem vendedores cadastrados
SELECT COUNT(*) AS count FROM sellers;

-- Inserir vendedores
INSERT INTO sellers (name, cpf, region, phone, email, status, active)
VALUES 
('João Silva', '123.456.789-01', 'Norte', '(11) 98765-4321', 'joao.silva@exemplo.com', 'active', TRUE),
('Maria Oliveira', '234.567.890-12', 'Sul', '(21) 98765-4322', 'maria.oliveira@exemplo.com', 'active', TRUE),
('Pedro Santos', '345.678.901-23', 'Leste', '(31) 98765-4323', 'pedro.santos@exemplo.com', 'active', TRUE),
('Ana Costa', '456.789.012-34', 'Oeste', '(41) 98765-4324', 'ana.costa@exemplo.com', 'active', TRUE),
('Carlos Pereira', '567.890.123-45', 'Centro', '(51) 98765-4325', 'carlos.pereira@exemplo.com', 'active', TRUE),
('Fernanda Lima', '678.901.234-56', 'Nordeste', '(61) 98765-4326', 'fernanda.lima@exemplo.com', 'active', TRUE),
('Ricardo Souza', '789.012.345-67', 'Sudeste', '(71) 98765-4327', 'ricardo.souza@exemplo.com', 'active', TRUE),
('Juliana Martins', '890.123.456-78', 'Noroeste', '(81) 98765-4328', 'juliana.martins@exemplo.com', 'active', TRUE),
('Roberto Almeida', '901.234.567-89', 'Sudoeste', '(91) 98765-4329', 'roberto.almeida@exemplo.com', 'active', TRUE),
('Patrícia Ferreira', '012.345.678-90', 'Centro-Oeste', '(12) 98765-4330', 'patricia.ferreira@exemplo.com', 'active', TRUE);

-- Verificar se os vendedores foram inseridos
SELECT id, name, region FROM sellers;

-- Buscar clientes existentes para vincular aos vendedores
SELECT id, name FROM customers LIMIT 30;

-- Vincular clientes aos vendedores (assumindo que existem pelo menos 30 clientes)
-- Para cada vendedor, vincular 3 clientes diferentes
-- Vendedor 1 (João Silva) - Clientes 1, 2, 3
INSERT INTO seller_customer (seller_id, customer_id)
SELECT 
    (SELECT id FROM sellers WHERE name = 'João Silva' LIMIT 1) as seller_id,
    id as customer_id
FROM customers
WHERE active = TRUE
ORDER BY id
LIMIT 3;

-- Vendedor 2 (Maria Oliveira) - Clientes 4, 5, 6
INSERT INTO seller_customer (seller_id, customer_id)
SELECT 
    (SELECT id FROM sellers WHERE name = 'Maria Oliveira' LIMIT 1) as seller_id,
    id as customer_id
FROM customers
WHERE active = TRUE
ORDER BY id
LIMIT 3 OFFSET 3;

-- Vendedor 3 (Pedro Santos) - Clientes 7, 8, 9
INSERT INTO seller_customer (seller_id, customer_id)
SELECT 
    (SELECT id FROM sellers WHERE name = 'Pedro Santos' LIMIT 1) as seller_id,
    id as customer_id
FROM customers
WHERE active = TRUE
ORDER BY id
LIMIT 3 OFFSET 6;

-- Vendedor 4 (Ana Costa) - Clientes 10, 11, 12
INSERT INTO seller_customer (seller_id, customer_id)
SELECT 
    (SELECT id FROM sellers WHERE name = 'Ana Costa' LIMIT 1) as seller_id,
    id as customer_id
FROM customers
WHERE active = TRUE
ORDER BY id
LIMIT 3 OFFSET 9;

-- Vendedor 5 (Carlos Pereira) - Clientes 13, 14, 15
INSERT INTO seller_customer (seller_id, customer_id)
SELECT 
    (SELECT id FROM sellers WHERE name = 'Carlos Pereira' LIMIT 1) as seller_id,
    id as customer_id
FROM customers
WHERE active = TRUE
ORDER BY id
LIMIT 3 OFFSET 12;

-- Vendedor 6 (Fernanda Lima) - Clientes 16, 17, 18
INSERT INTO seller_customer (seller_id, customer_id)
SELECT 
    (SELECT id FROM sellers WHERE name = 'Fernanda Lima' LIMIT 1) as seller_id,
    id as customer_id
FROM customers
WHERE active = TRUE
ORDER BY id
LIMIT 3 OFFSET 15;

-- Vendedor 7 (Ricardo Souza) - Clientes 19, 20, 21
INSERT INTO seller_customer (seller_id, customer_id)
SELECT 
    (SELECT id FROM sellers WHERE name = 'Ricardo Souza' LIMIT 1) as seller_id,
    id as customer_id
FROM customers
WHERE active = TRUE
ORDER BY id
LIMIT 3 OFFSET 18;

-- Vendedor 8 (Juliana Martins) - Clientes 22, 23, 24
INSERT INTO seller_customer (seller_id, customer_id)
SELECT 
    (SELECT id FROM sellers WHERE name = 'Juliana Martins' LIMIT 1) as seller_id,
    id as customer_id
FROM customers
WHERE active = TRUE
ORDER BY id
LIMIT 3 OFFSET 21;

-- Vendedor 9 (Roberto Almeida) - Clientes 25, 26, 27
INSERT INTO seller_customer (seller_id, customer_id)
SELECT 
    (SELECT id FROM sellers WHERE name = 'Roberto Almeida' LIMIT 1) as seller_id,
    id as customer_id
FROM customers
WHERE active = TRUE
ORDER BY id
LIMIT 3 OFFSET 24;

-- Vendedor 10 (Patrícia Ferreira) - Clientes 28, 29, 30
INSERT INTO seller_customer (seller_id, customer_id)
SELECT 
    (SELECT id FROM sellers WHERE name = 'Patrícia Ferreira' LIMIT 1) as seller_id,
    id as customer_id
FROM customers
WHERE active = TRUE
ORDER BY id
LIMIT 3 OFFSET 27;

-- Verificar as associações entre vendedores e clientes
SELECT s.name as seller_name, c.name as customer_name
FROM seller_customer sc
JOIN sellers s ON sc.seller_id = s.id
JOIN customers c ON sc.customer_id = c.id
ORDER BY s.name, c.name;
