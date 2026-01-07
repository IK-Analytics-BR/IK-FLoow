-- Script para inserir dados de exemplo para romaneios de vendas
-- Inserir 10 romaneios com dados fictícios

-- Verificar se já existem romaneios cadastrados
SELECT COUNT(*) AS count FROM sales_manifests;

-- Inserir romaneios de vendas (um para cada vendedor/rota)
-- Usamos a data atual para gerar códigos únicos
SET @current_date = CURDATE();
SET @date_code = DATE_FORMAT(@current_date, '%Y%m%d');
SET @yesterday = DATE_SUB(@current_date, INTERVAL 1 DAY);
SET @tomorrow = DATE_ADD(@current_date, INTERVAL 1 DAY);
SET @next_week = DATE_ADD(@current_date, INTERVAL 7 DAY);

-- Romaneio 1 - João Silva (Norte) - Concluído
INSERT INTO sales_manifests (manifest_number, date, seller_id, route_id, status, notes, active)
SELECT 
    CONCAT('RM-', @date_code, '-001'), 
    @yesterday, 
    s.id, 
    r.id, 
    'completed', 
    'Romaneio concluído com sucesso. Todos os clientes visitados.',
    TRUE
FROM sellers s
JOIN sales_routes r ON r.seller_id = s.id
WHERE s.name = 'João Silva'
LIMIT 1;

-- Romaneio 2 - Maria Oliveira (Sul) - Em andamento
INSERT INTO sales_manifests (manifest_number, date, seller_id, route_id, status, notes, active)
SELECT 
    CONCAT('RM-', @date_code, '-002'), 
    @current_date, 
    s.id, 
    r.id, 
    'in_progress', 
    'Romaneio em andamento. Alguns clientes já visitados.',
    TRUE
FROM sellers s
JOIN sales_routes r ON r.seller_id = s.id
WHERE s.name = 'Maria Oliveira'
LIMIT 1;

-- Romaneio 3 - Pedro Santos (Leste) - Rascunho
INSERT INTO sales_manifests (manifest_number, date, seller_id, route_id, status, notes, active)
SELECT 
    CONCAT('RM-', @date_code, '-003'), 
    @tomorrow, 
    s.id, 
    r.id, 
    'draft', 
    'Romaneio planejado para amanhã.',
    TRUE
FROM sellers s
JOIN sales_routes r ON r.seller_id = s.id
WHERE s.name = 'Pedro Santos'
LIMIT 1;

-- Romaneio 4 - Ana Costa (Oeste) - Cancelado
INSERT INTO sales_manifests (manifest_number, date, seller_id, route_id, status, notes, active)
SELECT 
    CONCAT('RM-', @date_code, '-004'), 
    @yesterday, 
    s.id, 
    r.id, 
    'canceled', 
    'Romaneio cancelado devido a problemas climáticos.',
    TRUE
FROM sellers s
JOIN sales_routes r ON r.seller_id = s.id
WHERE s.name = 'Ana Costa'
LIMIT 1;

-- Romaneio 5 - Carlos Pereira (Centro) - Concluído
INSERT INTO sales_manifests (manifest_number, date, seller_id, route_id, status, notes, active)
SELECT 
    CONCAT('RM-', @date_code, '-005'), 
    @yesterday, 
    s.id, 
    r.id, 
    'completed', 
    'Romaneio concluído. Boas vendas realizadas.',
    TRUE
FROM sellers s
JOIN sales_routes r ON r.seller_id = s.id
WHERE s.name = 'Carlos Pereira'
LIMIT 1;

-- Romaneio 6 - Fernanda Lima (Nordeste) - Rascunho
INSERT INTO sales_manifests (manifest_number, date, seller_id, route_id, status, notes, active)
SELECT 
    CONCAT('RM-', @date_code, '-006'), 
    @next_week, 
    s.id, 
    r.id, 
    'draft', 
    'Romaneio planejado para a próxima semana.',
    TRUE
FROM sellers s
JOIN sales_routes r ON r.seller_id = s.id
WHERE s.name = 'Fernanda Lima'
LIMIT 1;

-- Romaneio 7 - Ricardo Souza (Sudeste) - Em andamento
INSERT INTO sales_manifests (manifest_number, date, seller_id, route_id, status, notes, active)
SELECT 
    CONCAT('RM-', @date_code, '-007'), 
    @current_date, 
    s.id, 
    r.id, 
    'in_progress', 
    'Romaneio em andamento. Visitas sendo realizadas conforme planejado.',
    TRUE
FROM sellers s
JOIN sales_routes r ON r.seller_id = s.id
WHERE s.name = 'Ricardo Souza'
LIMIT 1;

-- Romaneio 8 - Juliana Martins (Noroeste) - Rascunho
INSERT INTO sales_manifests (manifest_number, date, seller_id, route_id, status, notes, active)
SELECT 
    CONCAT('RM-', @date_code, '-008'), 
    @tomorrow, 
    s.id, 
    r.id, 
    'draft', 
    'Romaneio planejado para amanhã.',
    TRUE
FROM sellers s
JOIN sales_routes r ON r.seller_id = s.id
WHERE s.name = 'Juliana Martins'
LIMIT 1;

-- Romaneio 9 - Roberto Almeida (Sudoeste) - Concluído
INSERT INTO sales_manifests (manifest_number, date, seller_id, route_id, status, notes, active)
SELECT 
    CONCAT('RM-', @date_code, '-009'), 
    @yesterday, 
    s.id, 
    r.id, 
    'completed', 
    'Romaneio concluído com sucesso. Todos os pedidos registrados.',
    TRUE
FROM sellers s
JOIN sales_routes r ON r.seller_id = s.id
WHERE s.name = 'Roberto Almeida'
LIMIT 1;

-- Romaneio 10 - Patrícia Ferreira (Centro-Oeste) - Em andamento
INSERT INTO sales_manifests (manifest_number, date, seller_id, route_id, status, notes, active)
SELECT 
    CONCAT('RM-', @date_code, '-010'), 
    @current_date, 
    s.id, 
    r.id, 
    'in_progress', 
    'Romaneio em andamento. Metade dos clientes já visitados.',
    TRUE
FROM sellers s
JOIN sales_routes r ON r.seller_id = s.id
WHERE s.name = 'Patrícia Ferreira'
LIMIT 1;

-- Verificar se os romaneios foram inseridos
SELECT m.id, m.manifest_number, m.date, s.name as seller_name, r.name as route_name, m.status
FROM sales_manifests m
JOIN sellers s ON m.seller_id = s.id
JOIN sales_routes r ON m.route_id = r.id
ORDER BY m.id;

-- Agora vamos criar as visitas para cada romaneio
-- Para cada romaneio, criar visitas para os clientes da rota

-- Função para criar visitas para um romaneio
DELIMITER //
CREATE PROCEDURE create_visits_for_manifest(IN manifest_id INT, IN manifest_status VARCHAR(20))
BEGIN
    -- Inserir visitas para os clientes da rota
    INSERT INTO manifest_visits (manifest_id, customer_id, visit_order, visit_status, visit_time, notes)
    SELECT 
        manifest_id,
        rc.customer_id,
        rc.visit_order,
        CASE 
            WHEN manifest_status = 'completed' THEN 'visited'
            WHEN manifest_status = 'in_progress' AND rc.visit_order <= 2 THEN 'visited'
            WHEN manifest_status = 'in_progress' AND rc.visit_order > 2 THEN 'pending'
            WHEN manifest_status = 'canceled' THEN 'skipped'
            ELSE 'pending'
        END as visit_status,
        CASE 
            WHEN manifest_status = 'completed' OR (manifest_status = 'in_progress' AND rc.visit_order <= 2) 
            THEN NOW() - INTERVAL (rc.visit_order * 30) MINUTE
            ELSE NULL
        END as visit_time,
        CASE 
            WHEN manifest_status = 'completed' OR (manifest_status = 'in_progress' AND rc.visit_order <= 2) 
            THEN 'Cliente visitado conforme planejado.'
            WHEN manifest_status = 'canceled' THEN 'Visita cancelada.'
            ELSE NULL
        END as notes
    FROM route_customer rc
    JOIN sales_routes r ON rc.route_id = r.id
    JOIN sales_manifests m ON m.route_id = r.id
    WHERE m.id = manifest_id;
    
    -- Para romaneios concluídos e em andamento, criar pedidos para as visitas realizadas
    IF manifest_status IN ('completed', 'in_progress') THEN
        -- Criar pedidos para as visitas realizadas
        INSERT INTO manifest_orders (visit_id, order_number, total_amount, payment_method, payment_terms, notes)
        SELECT 
            mv.id,
            CONCAT('PD-', DATE_FORMAT(NOW(), '%Y%m%d'), '-', LPAD(mv.id, 3, '0')),
            ROUND(RAND() * 1000 + 100, 2), -- Valor aleatório entre 100 e 1100
            CASE FLOOR(RAND() * 3)
                WHEN 0 THEN 'Dinheiro'
                WHEN 1 THEN 'Cartão de Crédito'
                ELSE 'Boleto'
            END,
            CASE FLOOR(RAND() * 3)
                WHEN 0 THEN 'À vista'
                WHEN 1 THEN '30 dias'
                ELSE '30/60 dias'
            END,
            'Pedido registrado durante a visita.'
        FROM manifest_visits mv
        WHERE mv.manifest_id = manifest_id AND mv.visit_status = 'visited';
        
        -- Criar itens para os pedidos
        INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount, total_price)
        SELECT 
            mo.id,
            FLOOR(RAND() * 10) + 1, -- Produto ID aleatório entre 1 e 10
            FLOOR(RAND() * 5) + 1, -- Quantidade aleatória entre 1 e 5
            ROUND(RAND() * 100 + 10, 2), -- Preço unitário aleatório entre 10 e 110
            0, -- Sem desconto
            ROUND((FLOOR(RAND() * 5) + 1) * (RAND() * 100 + 10), 2) -- Total = quantidade * preço unitário
        FROM manifest_orders mo
        JOIN manifest_visits mv ON mo.visit_id = mv.id
        WHERE mv.manifest_id = manifest_id;
        
        -- Atualizar o valor total dos pedidos com base nos itens
        UPDATE manifest_orders mo
        JOIN (
            SELECT order_id, SUM(total_price) as total
            FROM order_items
            GROUP BY order_id
        ) oi ON mo.id = oi.order_id
        SET mo.total_amount = oi.total
        WHERE mo.id IN (
            SELECT mo2.id
            FROM manifest_orders mo2
            JOIN manifest_visits mv ON mo2.visit_id = mv.id
            WHERE mv.manifest_id = manifest_id
        );
    END IF;
END //
DELIMITER ;

-- Criar visitas para cada romaneio
CALL create_visits_for_manifest(
    (SELECT id FROM sales_manifests WHERE manifest_number = CONCAT('RM-', @date_code, '-001')),
    'completed'
);

CALL create_visits_for_manifest(
    (SELECT id FROM sales_manifests WHERE manifest_number = CONCAT('RM-', @date_code, '-002')),
    'in_progress'
);

CALL create_visits_for_manifest(
    (SELECT id FROM sales_manifests WHERE manifest_number = CONCAT('RM-', @date_code, '-003')),
    'draft'
);

CALL create_visits_for_manifest(
    (SELECT id FROM sales_manifests WHERE manifest_number = CONCAT('RM-', @date_code, '-004')),
    'canceled'
);

CALL create_visits_for_manifest(
    (SELECT id FROM sales_manifests WHERE manifest_number = CONCAT('RM-', @date_code, '-005')),
    'completed'
);

CALL create_visits_for_manifest(
    (SELECT id FROM sales_manifests WHERE manifest_number = CONCAT('RM-', @date_code, '-006')),
    'draft'
);

CALL create_visits_for_manifest(
    (SELECT id FROM sales_manifests WHERE manifest_number = CONCAT('RM-', @date_code, '-007')),
    'in_progress'
);

CALL create_visits_for_manifest(
    (SELECT id FROM sales_manifests WHERE manifest_number = CONCAT('RM-', @date_code, '-008')),
    'draft'
);

CALL create_visits_for_manifest(
    (SELECT id FROM sales_manifests WHERE manifest_number = CONCAT('RM-', @date_code, '-009')),
    'completed'
);

CALL create_visits_for_manifest(
    (SELECT id FROM sales_manifests WHERE manifest_number = CONCAT('RM-', @date_code, '-010')),
    'in_progress'
);

-- Remover a procedure temporária
DROP PROCEDURE IF EXISTS create_visits_for_manifest;

-- Verificar as visitas criadas
SELECT 
    m.manifest_number, 
    s.name as seller_name, 
    c.name as customer_name, 
    mv.visit_order, 
    mv.visit_status,
    mv.visit_time
FROM manifest_visits mv
JOIN sales_manifests m ON mv.manifest_id = m.id
JOIN sellers s ON m.seller_id = s.id
JOIN customers c ON mv.customer_id = c.id
ORDER BY m.manifest_number, mv.visit_order;

-- Verificar os pedidos criados
SELECT 
    m.manifest_number, 
    mo.order_number, 
    c.name as customer_name, 
    mo.payment_method, 
    mo.payment_terms, 
    mo.total_amount
FROM manifest_orders mo
JOIN manifest_visits mv ON mo.visit_id = mv.id
JOIN sales_manifests m ON mv.manifest_id = m.id
JOIN customers c ON mv.customer_id = c.id
ORDER BY m.manifest_number, mv.visit_order;

-- Verificar os itens dos pedidos
SELECT 
    mo.order_number, 
    p.name as product_name, 
    oi.quantity, 
    oi.unit_price, 
    oi.total_price
FROM order_items oi
JOIN manifest_orders mo ON oi.order_id = mo.id
JOIN products p ON oi.product_id = p.id
ORDER BY mo.order_number;
