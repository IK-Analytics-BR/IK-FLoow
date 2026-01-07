-- Script para criar as tabelas de fornecedores e clientes
-- Autor: Sistema de Gestão de Suprimentos
-- Data: 2025-09-08

-- Tabela de Fornecedores
CREATE TABLE IF NOT EXISTS suppliers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    cnpj VARCHAR(18),
    contact_name VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(10),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Tabela de Clientes
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    cnpj VARCHAR(18),
    contact_name VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(10),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Inserir um fornecedor e um cliente de exemplo
INSERT INTO suppliers (name, cnpj, contact_name, phone, email, address, city, state, zip_code, notes, active)
VALUES ('Fornecedor Exemplo', '12.345.678/0001-90', 'João Silva', '(11) 98765-4321', 'joao@fornecedor.com', 'Rua dos Fornecedores, 123', 'São Paulo', 'SP', '01234-567', 'Fornecedor de materiais de escritório', TRUE);

INSERT INTO customers (name, cnpj, contact_name, phone, email, address, city, state, zip_code, notes, active)
VALUES ('Cliente Exemplo', '98.765.432/0001-10', 'Maria Souza', '(11) 91234-5678', 'maria@cliente.com', 'Avenida dos Clientes, 456', 'São Paulo', 'SP', '04321-765', 'Cliente corporativo', TRUE);
