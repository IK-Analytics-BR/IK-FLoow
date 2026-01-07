-- Script para criar as tabelas de referência necessárias para a integração de técnicos com ordens de serviço
-- Autor: Sistema de Gestão de Suprimentos
-- Data: 2025-09-08

-- Tabela de Clientes (se ainda não existir)
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

-- Inserir um cliente de exemplo
INSERT INTO customers (name, cnpj, contact_name, phone, email, address, city, state, zip_code, notes, active)
VALUES ('Cliente Exemplo', '12.345.678/0001-90', 'João Silva', '(11) 98765-4321', 'joao@cliente.com', 'Rua dos Clientes, 123', 'São Paulo', 'SP', '01234-567', 'Cliente corporativo', TRUE);

-- Tabela de Equipamentos (se ainda não existir)
CREATE TABLE IF NOT EXISTS equipment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    model VARCHAR(50),
    serial_number VARCHAR(50),
    customer_id INT NOT NULL,
    location VARCHAR(100),
    status ENUM('active', 'inactive', 'maintenance') NOT NULL DEFAULT 'active',
    purchase_date DATE,
    warranty_end_date DATE,
    last_maintenance_date DATE,
    next_maintenance_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Inserir um equipamento de exemplo
INSERT INTO equipment (name, model, serial_number, customer_id, location, status, purchase_date, warranty_end_date, active)
VALUES ('Equipamento Teste', 'Modelo X', 'SN12345', 1, 'Setor de Produção', 'active', '2025-01-01', '2026-01-01', TRUE);

-- Tabela de Insumos (se ainda não existir)
CREATE TABLE IF NOT EXISTS supplies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    supplier_id INT,
    part_number VARCHAR(50),
    stock INT DEFAULT 0,
    min_stock INT DEFAULT 5,
    unit_cost DECIMAL(10, 2),
    location VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

-- Inserir um insumo de exemplo
INSERT INTO supplies (name, description, supplier_id, part_number, stock, min_stock, unit_cost, location, active)
VALUES ('Peça de Reposição', 'Peça para manutenção preventiva', 1, 'PN-001', 10, 5, 150.00, 'Almoxarifado A', TRUE);

-- Tabela de Planos de Manutenção (se ainda não existir)
CREATE TABLE IF NOT EXISTS maintenance_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task VARCHAR(100) NOT NULL,
    description TEXT,
    customer_id INT NOT NULL,
    equipment_id INT NOT NULL,
    frequency_days INT NOT NULL,
    estimated_hours DECIMAL(5, 2),
    last_execution_date DATE,
    next_execution_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
);

-- Inserir um plano de manutenção de exemplo
INSERT INTO maintenance_plans (task, description, customer_id, equipment_id, frequency_days, estimated_hours, next_execution_date, active)
VALUES ('Manutenção Preventiva', 'Verificação periódica do equipamento', 1, 1, 90, 2.5, DATE_ADD(CURRENT_DATE, INTERVAL 30 DAY), TRUE);
