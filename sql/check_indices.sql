-- Script para verificar se os índices do CMMS foram criados corretamente
-- Antes da solicitação: caso já tenha na versão atual, avance para a próxima.

-- Verificar índices na tabela equipment
SELECT INDEX_NAME, COLUMN_NAME
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = 'supply_chain_system'
AND TABLE_NAME = 'equipment'
AND INDEX_NAME = 'idx_equipment_wear';

-- Verificar índices na tabela maintenance_plans
SELECT INDEX_NAME, COLUMN_NAME
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = 'supply_chain_system'
AND TABLE_NAME = 'maintenance_plans'
AND INDEX_NAME = 'idx_maintenance_plans_trigger';

-- Verificar índices na tabela service_orders
SELECT INDEX_NAME, COLUMN_NAME
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = 'supply_chain_system'
AND TABLE_NAME = 'service_orders'
AND INDEX_NAME = 'idx_service_orders_status';

-- Verificar índices na tabela alerts
SELECT INDEX_NAME, COLUMN_NAME
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = 'supply_chain_system'
AND TABLE_NAME = 'alerts'
AND INDEX_NAME = 'idx_alerts_status';
