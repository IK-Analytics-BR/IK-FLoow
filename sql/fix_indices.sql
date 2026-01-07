-- Script para corrigir os índices faltantes do CMMS
-- Antes da solicitação: caso já tenha na versão atual, avance para a próxima.

-- Criar índice para wear_percentage na tabela equipment
CREATE INDEX idx_equipment_wear ON equipment(wear_percentage);

-- Criar índice para trigger_type e trigger_value na tabela maintenance_plans
CREATE INDEX idx_maintenance_plans_trigger ON maintenance_plans(trigger_type, trigger_value);

-- Criar índice para status na tabela service_orders
CREATE INDEX idx_service_orders_status ON service_orders(status);

-- Criar índice para status na tabela alerts
CREATE INDEX idx_alerts_status ON alerts(status);
