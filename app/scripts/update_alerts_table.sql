-- Script para atualizar a tabela de alertas
-- Adiciona coluna de prioridade e expande os tipos de alerta

-- Modificar a tabela para adicionar a coluna de prioridade
ALTER TABLE alerts ADD COLUMN priority ENUM('low', 'medium', 'high', 'critical') NOT NULL DEFAULT 'medium' AFTER message;

-- Modificar o tipo de alerta para incluir os novos tipos
ALTER TABLE alerts MODIFY COLUMN alert_type ENUM(
    'wear_80',
    'wear_100',
    'stock_low',
    'maintenance_due',
    'os_created',
    'os_assigned',
    'os_completed'
) NOT NULL;

-- Adicionar colunas para reconhecimento e resolução de alertas
ALTER TABLE alerts ADD COLUMN acknowledged_by INT NULL AFTER updated_at;
ALTER TABLE alerts ADD COLUMN acknowledged_at TIMESTAMP NULL AFTER acknowledged_by;
ALTER TABLE alerts ADD COLUMN resolved_by INT NULL AFTER acknowledged_at;
ALTER TABLE alerts ADD COLUMN resolved_at TIMESTAMP NULL AFTER resolved_by;

-- Adicionar chaves estrangeiras
ALTER TABLE alerts ADD CONSTRAINT fk_alerts_acknowledged_by FOREIGN KEY (acknowledged_by) REFERENCES users(id);
ALTER TABLE alerts ADD CONSTRAINT fk_alerts_resolved_by FOREIGN KEY (resolved_by) REFERENCES users(id);

-- Adicionar índices para melhorar o desempenho
CREATE INDEX idx_alerts_priority ON alerts(priority);
CREATE INDEX idx_alerts_created_at ON alerts(created_at);
