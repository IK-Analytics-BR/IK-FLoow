-- Script para atualizar a tabela service_orders para integração com a tabela de técnicos
-- Autor: Sistema de Gestão de Suprimentos
-- Data: 2025-09-08

-- Verificar se já existe a tabela service_orders
CREATE TABLE IF NOT EXISTS service_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_number VARCHAR(20) NOT NULL,
    customer_id INT NOT NULL,
    equipment_id INT NOT NULL,
    supply_id INT,
    maintenance_plan_id INT,
    type ENUM('preventive', 'corrective', 'predictive') NOT NULL,
    technician_id INT,
    status ENUM('open', 'in_progress', 'completed', 'canceled') NOT NULL DEFAULT 'open',
    observations TEXT,
    downtime_minutes INT DEFAULT 0,
    open_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completion_date TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (equipment_id) REFERENCES equipment(id),
    FOREIGN KEY (supply_id) REFERENCES supplies(id),
    FOREIGN KEY (maintenance_plan_id) REFERENCES maintenance_plans(id),
    UNIQUE KEY (order_number)
);

-- Verificar se já existe a tabela service_order_labor
CREATE TABLE IF NOT EXISTS service_order_labor (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service_order_id INT NOT NULL,
    technician_id INT NOT NULL,
    hours_worked DECIMAL(10, 2) NOT NULL,
    hourly_rate DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (service_order_id) REFERENCES service_orders(id),
    FOREIGN KEY (technician_id) REFERENCES technicians(id)
);

-- Verificar se já existe a tabela service_order_items
CREATE TABLE IF NOT EXISTS service_order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service_order_id INT NOT NULL,
    supply_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_cost DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (service_order_id) REFERENCES service_orders(id),
    FOREIGN KEY (supply_id) REFERENCES supplies(id)
);

-- Atualizar a chave estrangeira da coluna technician_id na tabela service_orders
-- Verificar se existe a chave estrangeira e removê-la
SET @constraint_name = (
    SELECT CONSTRAINT_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'supply_chain_system'
    AND TABLE_NAME = 'service_orders'
    AND COLUMN_NAME = 'technician_id'
    AND REFERENCED_TABLE_NAME IS NOT NULL
    LIMIT 1
);

SET @sql = IF(@constraint_name IS NOT NULL, 
    CONCAT('ALTER TABLE service_orders DROP FOREIGN KEY ', @constraint_name), 
    'SELECT "No foreign key constraint found for technician_id"');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Adicionar a nova chave estrangeira para a tabela technicians
ALTER TABLE service_orders
ADD CONSTRAINT fk_service_orders_technician
FOREIGN KEY (technician_id) REFERENCES technicians(id);

-- Atualizar a chave estrangeira da coluna technician_id na tabela service_order_labor
-- Verificar se existe a chave estrangeira e removê-la
SET @constraint_name = (
    SELECT CONSTRAINT_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'supply_chain_system'
    AND TABLE_NAME = 'service_order_labor'
    AND COLUMN_NAME = 'technician_id'
    AND REFERENCED_TABLE_NAME IS NOT NULL
    LIMIT 1
);

SET @sql = IF(@constraint_name IS NOT NULL, 
    CONCAT('ALTER TABLE service_order_labor DROP FOREIGN KEY ', @constraint_name), 
    'SELECT "No foreign key constraint found for technician_id"');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Adicionar a nova chave estrangeira para a tabela technicians
ALTER TABLE service_order_labor
ADD CONSTRAINT fk_service_order_labor_technician
FOREIGN KEY (technician_id) REFERENCES technicians(id);
