-- Script para criar as tabelas do sistema de Romaneio de Vendas

-- Tabela de Vendedores
CREATE TABLE IF NOT EXISTS sellers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    cpf VARCHAR(14) NOT NULL UNIQUE,
    region VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    status ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Tabela de associação entre Vendedores e Clientes
CREATE TABLE IF NOT EXISTS seller_customer (
    id INT AUTO_INCREMENT PRIMARY KEY,
    seller_id INT NOT NULL,
    customer_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES sellers(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    UNIQUE KEY (seller_id, customer_id)
);

-- Tabela de Rotas de Vendas
CREATE TABLE IF NOT EXISTS sales_routes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    seller_id INT NOT NULL,
    frequency ENUM('daily', 'weekly', 'monthly') NOT NULL DEFAULT 'weekly',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (seller_id) REFERENCES sellers(id)
);

-- Tabela de associação entre Rotas e Clientes
CREATE TABLE IF NOT EXISTS route_customer (
    id INT AUTO_INCREMENT PRIMARY KEY,
    route_id INT NOT NULL,
    customer_id INT NOT NULL,
    visit_order INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (route_id) REFERENCES sales_routes(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    UNIQUE KEY (route_id, customer_id)
);

-- Tabela de Romaneio de Vendas
CREATE TABLE IF NOT EXISTS sales_manifests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    manifest_number VARCHAR(20) NOT NULL UNIQUE,
    date DATE NOT NULL,
    seller_id INT NOT NULL,
    route_id INT NOT NULL,
    status ENUM('draft', 'in_progress', 'completed', 'canceled') NOT NULL DEFAULT 'draft',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (seller_id) REFERENCES sellers(id),
    FOREIGN KEY (route_id) REFERENCES sales_routes(id)
);

-- Tabela de Visitas do Romaneio
CREATE TABLE IF NOT EXISTS manifest_visits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    manifest_id INT NOT NULL,
    customer_id INT NOT NULL,
    visit_order INT NOT NULL,
    visit_status ENUM('pending', 'visited', 'skipped') NOT NULL DEFAULT 'pending',
    visit_time DATETIME,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (manifest_id) REFERENCES sales_manifests(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Tabela de Pedidos do Romaneio
CREATE TABLE IF NOT EXISTS manifest_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    visit_id INT NOT NULL,
    order_number VARCHAR(20) NOT NULL UNIQUE,
    total_amount DECIMAL(10, 2) NOT NULL DEFAULT 0,
    payment_method VARCHAR(50),
    payment_terms VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (visit_id) REFERENCES manifest_visits(id)
);

-- Tabela de Itens do Pedido
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    discount DECIMAL(10, 2) NOT NULL DEFAULT 0,
    total_price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES manifest_orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Índices para melhorar o desempenho
CREATE INDEX idx_sellers_name ON sellers(name);
CREATE INDEX idx_sellers_region ON sellers(region);
CREATE INDEX idx_sales_routes_seller ON sales_routes(seller_id);
CREATE INDEX idx_sales_manifests_date ON sales_manifests(date);
CREATE INDEX idx_sales_manifests_seller ON sales_manifests(seller_id);
CREATE INDEX idx_sales_manifests_route ON sales_manifests(route_id);
CREATE INDEX idx_manifest_visits_manifest ON manifest_visits(manifest_id);
CREATE INDEX idx_manifest_visits_customer ON manifest_visits(customer_id);
CREATE INDEX idx_manifest_orders_visit ON manifest_orders(visit_id);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
