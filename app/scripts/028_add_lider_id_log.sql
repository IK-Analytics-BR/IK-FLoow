-- =====================================================
-- ADICIONAR CAMPO LIDER_ID NO LOG DE ETAPAS
-- Script: 028_add_lider_id_log.sql
-- Data: 24/12/2024
-- Descrição: Adiciona campo lider_id para rastrear qual líder
--            era responsável no momento da movimentação
-- =====================================================

USE supply_chain_system;

-- Campo: lider_id - Líder responsável no momento da movimentação
ALTER TABLE op_lotes_etapas_log 
ADD COLUMN lider_id INT NULL
COMMENT 'ID do líder responsável no momento da movimentação'
AFTER ordem_producao_id;

-- Índice
CREATE INDEX idx_op_lotes_log_lider ON op_lotes_etapas_log(lider_id);

-- Verificação
SELECT 'Campo lider_id adicionado com sucesso!' AS status;
SHOW COLUMNS FROM op_lotes_etapas_log WHERE Field = 'lider_id';
