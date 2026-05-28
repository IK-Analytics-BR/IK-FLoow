-- =====================================================
-- Script de Inicialização do Banco de Dados IK Flow
-- Cria todas as tabelas necessárias e dados mínimos
-- =====================================================

-- Tabela de Empresas
CREATE TABLE IF NOT EXISTS empresas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    razao_social VARCHAR(200) NOT NULL,
    nome_fantasia VARCHAR(200),
    cnpj VARCHAR(20),
    ie VARCHAR(20),
    im VARCHAR(20),
    endereco VARCHAR(200),
    numero VARCHAR(20),
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    estado VARCHAR(2),
    cep VARCHAR(10),
    telefone VARCHAR(20),
    email VARCHAR(100),
    logo VARCHAR(255),
    app_mode VARCHAR(20) DEFAULT 'global',
    active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Usuários
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
    status VARCHAR(20) DEFAULT 'active',
    active TINYINT(1) DEFAULT 1,
    last_login TIMESTAMP NULL,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabela de Vínculo Usuário-Empresa
CREATE TABLE IF NOT EXISTS usuario_empresas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    empresa_id INT NOT NULL,
    is_default TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES users(id),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    UNIQUE KEY uk_usuario_empresa (usuario_id, empresa_id)
);

-- Tabela de Permissões
CREATE TABLE IF NOT EXISTS permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Permissões de Usuário
CREATE TABLE IF NOT EXISTS user_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    permission_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (permission_id) REFERENCES permissions(id),
    UNIQUE KEY uk_user_permission (user_id, permission_id)
);

-- Tabela de Clientes
CREATE TABLE IF NOT EXISTS clients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(2),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Produtos
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50),
    description TEXT,
    price DECIMAL(15,2) DEFAULT 0,
    cost DECIMAL(15,2) DEFAULT 0,
    stock_quantity DECIMAL(15,3) DEFAULT 0,
    unit VARCHAR(20) DEFAULT 'UN',
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Categorias de Produto
CREATE TABLE IF NOT EXISTS product_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Fornecedores
CREATE TABLE IF NOT EXISTS suppliers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    legal_name VARCHAR(200),
    tax_id VARCHAR(20),
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(2),
    active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Pedidos de Compra
CREATE TABLE IF NOT EXISTS purchase_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT,
    order_date DATE,
    total_amount DECIMAL(15,2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'draft',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

-- Tabela de Itens de Pedido de Compra
CREATE TABLE IF NOT EXISTS purchase_order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    purchase_order_id INT NOT NULL,
    product_id INT,
    quantity DECIMAL(15,3) DEFAULT 0,
    unit_price DECIMAL(15,2) DEFAULT 0,
    total_price DECIMAL(15,2) DEFAULT 0,
    FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Tabela de Locais de Estoque
CREATE TABLE IF NOT EXISTS stock_locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Estoque
CREATE TABLE IF NOT EXISTS inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    location_id INT,
    quantity DECIMAL(15,3) DEFAULT 0,
    min_stock DECIMAL(15,3) DEFAULT 0,
    max_stock DECIMAL(15,3) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (location_id) REFERENCES stock_locations(id)
);

-- =====================================================
-- DADOS INICIAIS
-- =====================================================

-- Inserir empresa padrão
INSERT INTO empresas (razao_social, nome_fantasia, cnpj, active) 
VALUES ('Empresa Padrão', 'IK Flow', '00.000.000/0000-00', 1)
ON DUPLICATE KEY UPDATE active = 1;

-- Inserir usuário admin (senha: admin123)
-- Hash PBKDF2-SHA512 gerado via password_utils
INSERT INTO users (name, username, email, password_hash, salt, role, status, active) 
VALUES (
    'Administrador', 
    'admin', 
    'admin@ikflow.com',
    '9f4a5c7c2c9a5c50c57328015144e842af9cbe8a54a33cd678d14fa8e04a612833ee5431eadba4ad1d178855ab5c7a2473604471322c74c57e80bfa8579eb20dd7a77409cf093ba941491bbde08972db21d9810fc22a2ea19b35c5308c132006',
    '123456789abcdef',
    'admin',
    'active',
    1
)
ON DUPLICATE KEY UPDATE 
    password_hash = VALUES(password_hash),
    salt = VALUES(salt),
    status = 'active',
    active = 1;

-- Vincular admin à empresa padrão
INSERT INTO usuario_empresas (usuario_id, empresa_id, is_default)
SELECT u.id, e.id, 1 
FROM users u, empresas e 
WHERE u.username = 'admin' AND e.razao_social = 'Empresa Padrão'
ON DUPLICATE KEY UPDATE is_default = 1;

-- Inserir local de estoque padrão
INSERT INTO stock_locations (name, description, active)
VALUES ('Estoque Principal', 'Local principal de armazenamento', 1)
ON DUPLICATE KEY UPDATE active = 1;

-- Inserir permissões padrão
INSERT INTO permissions (name, description) VALUES
    ('dashboard.visualizar', 'Visualizar dashboard'),
    ('clientes.visualizar', 'Visualizar clientes'),
    ('clientes.editar', 'Editar clientes'),
    ('produtos.visualizar', 'Visualizar produtos'),
    ('produtos.editar', 'Editar produtos'),
    ('compras.visualizar', 'Visualizar compras'),
    ('compras.editar', 'Editar compras'),
    ('estoque.visualizar', 'Visualizar estoque'),
    ('estoque.editar', 'Editar estoque'),
    ('vendas.visualizar', 'Visualizar vendas'),
    ('vendas.editar', 'Editar vendas'),
    ('financeiro.visualizar', 'Visualizar financeiro'),
    ('financeiro.editar', 'Editar financeiro'),
    ('relatorios.visualizar', 'Visualizar relatórios'),
    ('admin.usuarios', 'Gerenciar usuários'),
    ('admin.configuracoes', 'Configurações do sistema')
ON DUPLICATE KEY UPDATE description = VALUES(description);

-- Dar todas as permissões ao admin
INSERT INTO user_permissions (user_id, permission_id)
SELECT u.id, p.id 
FROM users u, permissions p 
WHERE u.username = 'admin'
ON DUPLICATE KEY UPDATE user_id = user_id;

SELECT 'Banco de dados inicializado com sucesso!' as resultado;
