-- Script para adicionar funcionalidades CMMS ao SupplyChainSystem
-- Antes da solicitação: caso já tenha na versão atual, avance para a próxima.

-- 1. Adicionar campos de parâmetros de uso na tabela equipment
ALTER TABLE equipment
ADD COLUMN base_life_hours INT DEFAULT NULL COMMENT 'Vida útil base em horas',
ADD COLUMN standard_hours_day DECIMAL(5,2) DEFAULT 8.00 COMMENT 'Horas padrão por dia',
ADD COLUMN real_hours_day DECIMAL(5,2) DEFAULT NULL COMMENT 'Horas reais por dia',
ADD COLUMN k_intensity DECIMAL(3,2) DEFAULT 1.00 COMMENT 'Fator de intensidade (1.0=leve, 1.1-1.2=médio, 1.3-1.5=pesado)',
ADD COLUMN k_environment DECIMAL(3,2) DEFAULT 1.00 COMMENT 'Fator de ambiente (1.0=limpo, 1.1=poeira, 1.2=químicos, 1.3=alta temp.)',
ADD COLUMN accumulated_hours INT DEFAULT 0 COMMENT 'Horas acumuladas de operação',
ADD COLUMN adjusted_life_hours INT DEFAULT NULL COMMENT 'Vida útil ajustada em horas',
ADD COLUMN wear_percentage DECIMAL(5,2) DEFAULT 0.00 COMMENT 'Percentual de desgaste',
ADD COLUMN last_hour_update DATE DEFAULT NULL COMMENT 'Data da última atualização do horímetro',
ADD COLUMN manufacturer VARCHAR(100) DEFAULT NULL COMMENT 'Fabricante do equipamento',
ADD COLUMN model VARCHAR(100) DEFAULT NULL COMMENT 'Modelo do equipamento',
ADD COLUMN serial_number VARCHAR(100) DEFAULT NULL COMMENT 'Número de série',
ADD COLUMN acquisition_date DATE DEFAULT NULL COMMENT 'Data de aquisição',
ADD COLUMN environment_type ENUM('clean', 'dust', 'chemical', 'high_temp') DEFAULT 'clean' COMMENT 'Tipo de ambiente';

-- 2. Adicionar campos de parâmetros de uso na tabela supplies
ALTER TABLE supplies
ADD COLUMN base_life_hours INT DEFAULT NULL COMMENT 'Vida útil base em horas',
ADD COLUMN preventive_percentage INT DEFAULT 90 COMMENT 'Percentual para manutenção preventiva',
ADD COLUMN location VARCHAR(100) DEFAULT NULL COMMENT 'Localização no estoque',
ADD COLUMN last_price DECIMAL(10,2) DEFAULT NULL COMMENT 'Último preço de compra';

-- 3. Criar tabela para planos de manutenção
CREATE TABLE IF NOT EXISTS maintenance_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    equipment_id INT NOT NULL,
    supply_id INT DEFAULT NULL,
    type ENUM('preventive', 'corrective', 'predictive') NOT NULL DEFAULT 'preventive',
    trigger_type ENUM('hours', 'cycles', 'time') NOT NULL DEFAULT 'hours',
    trigger_value INT NOT NULL COMMENT 'Valor do gatilho (horas, ciclos ou dias)',
    task VARCHAR(100) NOT NULL COMMENT 'Tarefa (troca, inspeção, limpeza, etc)',
    instructions TEXT DEFAULT NULL COMMENT 'Instruções detalhadas',
    standard_execution_time INT DEFAULT 60 COMMENT 'Tempo padrão de execução em minutos',
    active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (equipment_id) REFERENCES equipment(id),
    FOREIGN KEY (supply_id) REFERENCES supplies(id)
);

-- 4. Criar tabela para ordens de serviço
CREATE TABLE IF NOT EXISTS service_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_number VARCHAR(20) NOT NULL COMMENT 'Número da OS (auto)',
    customer_id INT NOT NULL,
    equipment_id INT NOT NULL,
    supply_id INT DEFAULT NULL,
    maintenance_plan_id INT DEFAULT NULL COMMENT 'Plano de manutenção que gerou a OS (se aplicável)',
    type ENUM('preventive', 'corrective', 'predictive') NOT NULL DEFAULT 'preventive',
    status ENUM('open', 'in_progress', 'completed', 'canceled') NOT NULL DEFAULT 'open',
    technician_id INT DEFAULT NULL COMMENT 'Técnico responsável',
    open_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Data de abertura',
    completion_date TIMESTAMP DEFAULT NULL COMMENT 'Data de conclusão',
    downtime_minutes INT DEFAULT 0 COMMENT 'Tempo de parada em minutos',
    observations TEXT DEFAULT NULL,
    active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (equipment_id) REFERENCES equipment(id),
    FOREIGN KEY (supply_id) REFERENCES supplies(id),
    FOREIGN KEY (maintenance_plan_id) REFERENCES maintenance_plans(id),
    FOREIGN KEY (technician_id) REFERENCES users(id)
);

-- 5. Criar tabela para itens usados nas ordens de serviço
CREATE TABLE IF NOT EXISTS service_order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service_order_id INT NOT NULL,
    supply_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    unit_cost DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (service_order_id) REFERENCES service_orders(id),
    FOREIGN KEY (supply_id) REFERENCES supplies(id)
);

-- 6. Criar tabela para horas trabalhadas nas ordens de serviço
CREATE TABLE IF NOT EXISTS service_order_labor (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service_order_id INT NOT NULL,
    technician_id INT NOT NULL,
    hours_worked DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    hourly_rate DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (service_order_id) REFERENCES service_orders(id),
    FOREIGN KEY (technician_id) REFERENCES users(id)
);

-- 7. Criar tabela para horímetro (registros de horas de operação)
CREATE TABLE IF NOT EXISTS hour_meter_readings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    equipment_id INT NOT NULL,
    reading_date DATE NOT NULL,
    hours INT NOT NULL COMMENT 'Leitura do horímetro em horas',
    reading_type ENUM('manual', 'iot') NOT NULL DEFAULT 'manual',
    user_id INT DEFAULT NULL COMMENT 'Usuário que registrou a leitura',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 8. Criar tabela para alertas
CREATE TABLE IF NOT EXISTS alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    equipment_id INT NOT NULL,
    supply_id INT DEFAULT NULL,
    alert_type ENUM('wear_80', 'wear_100', 'stock_low', 'maintenance_due') NOT NULL,
    status ENUM('active', 'acknowledged', 'resolved') NOT NULL DEFAULT 'active',
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id),
    FOREIGN KEY (supply_id) REFERENCES supplies(id)
);

-- 9. Adicionar campo de especialidade na tabela users para técnicos
ALTER TABLE users
ADD COLUMN specialty ENUM('mechanical', 'electrical', 'automation', 'general') DEFAULT NULL COMMENT 'Especialidade do técnico';

-- 10. Criar índices para melhorar performance
CREATE INDEX idx_equipment_wear ON equipment(wear_percentage);
CREATE INDEX idx_maintenance_plans_trigger ON maintenance_plans(trigger_type, trigger_value);
CREATE INDEX idx_service_orders_status ON service_orders(status);
CREATE INDEX idx_alerts_status ON alerts(status);
