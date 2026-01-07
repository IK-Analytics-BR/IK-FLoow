-- Script para adicionar campos NFC-e na tabela empresas
-- Execute este script no MySQL

-- Adicionar campos para NFC-e
ALTER TABLE empresas 
ADD COLUMN IF NOT EXISTS csc_nfce VARCHAR(50) NULL COMMENT 'CSC para NFC-e',
ADD COLUMN IF NOT EXISTS id_csc_nfce VARCHAR(10) NULL COMMENT 'ID do CSC',
ADD COLUMN IF NOT EXISTS ambiente_nfce INT DEFAULT 2 COMMENT '1=Producao, 2=Homologacao';

-- Atualizar CSC da IK Analytics (empresa_id = 9)
UPDATE empresas 
SET csc_nfce = '8b6c3d1d3b00be82fad2e68a03a5817688c2',
    id_csc_nfce = '000001',
    ambiente_nfce = 2  -- Homologação
WHERE id = 9;

-- Verificar
SELECT id, nome_fantasia, csc_nfce, id_csc_nfce, ambiente_nfce 
FROM empresas WHERE id = 9;
