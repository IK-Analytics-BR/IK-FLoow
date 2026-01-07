-- =====================================================
-- ADICIONAR CAMPOS PARA CONTROLE DE OPERADORES EM OP_LOTES
-- Script: 027_add_campos_operador_op_lotes.sql
-- Data: 24/12/2024
-- Descrição: Adiciona campos para controlar operadores de chão de fábrica
--            no fluxo de produção (Gantt)
-- =====================================================

USE supply_chain_system;

-- =====================================================
-- 1. ADICIONAR CAMPOS NA TABELA op_lotes
-- =====================================================

-- Campo: operador_id - Operador responsável pelo lote na etapa atual
ALTER TABLE op_lotes 
ADD COLUMN operador_id INT NULL 
COMMENT 'ID do operador responsável pelo lote na etapa atual'
AFTER etapa_atual_id;

-- Campo: status_operador - Status do lote para o operador
ALTER TABLE op_lotes 
ADD COLUMN status_operador ENUM('em_espera', 'em_producao', 'despachado') DEFAULT 'em_espera'
COMMENT 'Status do lote para o operador: em_espera, em_producao, despachado'
AFTER operador_id;

-- Campo: arara - Local onde o lote foi deixado após despacho
ALTER TABLE op_lotes 
ADD COLUMN arara VARCHAR(50) NULL
COMMENT 'Local/arara onde o lote foi deixado após despacho'
AFTER status_operador;

-- Campo: data_inicio_operador - Data/hora que operador iniciou produção
ALTER TABLE op_lotes 
ADD COLUMN data_inicio_operador DATETIME NULL
COMMENT 'Data/hora que o operador iniciou a produção do lote'
AFTER arara;

-- Campo: data_fim_operador - Data/hora que operador finalizou/despachou
ALTER TABLE op_lotes 
ADD COLUMN data_fim_operador DATETIME NULL
COMMENT 'Data/hora que o operador finalizou/despachou o lote'
AFTER data_inicio_operador;

-- Índices para performance
CREATE INDEX idx_op_lotes_operador ON op_lotes(operador_id);
CREATE INDEX idx_op_lotes_status_operador ON op_lotes(status_operador);

-- Foreign Key para operador (usuário)
ALTER TABLE op_lotes 
ADD CONSTRAINT fk_op_lotes_operador 
FOREIGN KEY (operador_id) REFERENCES users(id) ON DELETE SET NULL;

-- =====================================================
-- 2. ADICIONAR CAMPOS NA TABELA op_lotes_etapas_log
-- =====================================================

-- Campo: operador_origem_id - Operador que despachou
ALTER TABLE op_lotes_etapas_log 
ADD COLUMN operador_origem_id INT NULL
COMMENT 'ID do operador que despachou o lote'
AFTER usuario_id;

-- Campo: operador_destino_id - Operador que recebeu
ALTER TABLE op_lotes_etapas_log 
ADD COLUMN operador_destino_id INT NULL
COMMENT 'ID do operador que recebeu o lote'
AFTER operador_origem_id;

-- Campo: arara - Local onde foi deixado
ALTER TABLE op_lotes_etapas_log 
ADD COLUMN arara VARCHAR(50) NULL
COMMENT 'Local/arara onde o lote foi deixado'
AFTER operador_destino_id;

-- Campo: status_anterior - Status antes da movimentação
ALTER TABLE op_lotes_etapas_log 
ADD COLUMN status_anterior VARCHAR(20) NULL
COMMENT 'Status do lote antes da movimentação'
AFTER arara;

-- Campo: status_novo - Status após a movimentação
ALTER TABLE op_lotes_etapas_log 
ADD COLUMN status_novo VARCHAR(20) NULL
COMMENT 'Status do lote após a movimentação'
AFTER status_anterior;

-- =====================================================
-- 3. VINCULAR ETAPAS A OPERADORES (producao_etapas)
-- =====================================================

-- Campo: operador_padrao_id - Operador padrão da etapa (opcional)
ALTER TABLE producao_etapas 
ADD COLUMN operador_padrao_id INT NULL
COMMENT 'ID do operador padrão responsável por esta etapa'
AFTER grupo_etapas_id;

-- Índice
CREATE INDEX idx_producao_etapas_operador ON producao_etapas(operador_padrao_id);

-- =====================================================
-- 4. VERIFICAÇÃO
-- =====================================================

SELECT 'Campos adicionados com sucesso!' AS status;

-- Verificar estrutura de op_lotes
SHOW COLUMNS FROM op_lotes WHERE Field IN ('operador_id', 'status_operador', 'arara', 'data_inicio_operador', 'data_fim_operador');

-- Verificar estrutura de op_lotes_etapas_log
SHOW COLUMNS FROM op_lotes_etapas_log WHERE Field IN ('operador_origem_id', 'operador_destino_id', 'arara', 'status_anterior', 'status_novo');

-- Verificar estrutura de producao_etapas
SHOW COLUMNS FROM producao_etapas WHERE Field = 'operador_padrao_id';
