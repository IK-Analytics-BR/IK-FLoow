-- Script SQL para criar as tabelas do módulo Simulador de Cenários

-- Tabela de cenários de simulação
CREATE TABLE IF NOT EXISTS scenarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    equipment_id INT NOT NULL,
    simulation_period INT NOT NULL,
    usage_pattern VARCHAR(20) NOT NULL,
    maintenance_strategy VARCHAR(20) NOT NULL,
    user_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Tabela de resultados de simulação
CREATE TABLE IF NOT EXISTS simulation_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    scenario_id INT NOT NULL,
    result_data JSON NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

-- Índices para melhorar a performance
CREATE INDEX idx_scenarios_equipment ON scenarios(equipment_id);
CREATE INDEX idx_scenarios_user ON scenarios(user_id);
CREATE INDEX idx_simulation_results_scenario ON simulation_results(scenario_id);
