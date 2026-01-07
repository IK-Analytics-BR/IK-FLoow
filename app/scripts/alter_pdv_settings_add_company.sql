-- ============================================
-- ALTERAÇÃO: VINCULAR PDV A EMPRESA
-- Data: 2025-10-24
-- Objetivo: Permitir múltiplos PDVs, cada um vinculado a uma empresa
-- ============================================

-- Adicionar campo company_id à tabela pdv_settings
ALTER TABLE pdv_settings
ADD COLUMN company_id INT NULL COMMENT 'Empresa vinculada ao PDV' AFTER pdv_number,
ADD CONSTRAINT fk_pdv_company FOREIGN KEY (company_id) REFERENCES empresas(id) ON DELETE SET NULL;

-- Criar índice para melhor performance
CREATE INDEX idx_pdv_settings_company ON pdv_settings(company_id);

-- Atualizar registro existente com primeira empresa
UPDATE pdv_settings 
SET company_id = (SELECT id FROM empresas WHERE ativo = 1 LIMIT 1)
WHERE company_id IS NULL;

-- Adicionar campo description
ALTER TABLE pdv_settings
ADD COLUMN description TEXT NULL COMMENT 'Descrição do PDV' AFTER pdv_name;

-- Remover constraint UNIQUE de active (permitir múltiplos ativos)
-- Modificar a lógica para ter um PDV ativo por empresa

-- Criar visualização para facilitar consultas
CREATE OR REPLACE VIEW vw_pdv_list AS
SELECT 
    ps.id,
    ps.pdv_name,
    ps.pdv_number,
    ps.description,
    ps.company_id,
    COALESCE(e.nome_fantasia, e.razao_social) AS empresa_nome,
    e.cnpj AS empresa_cnpj,
    e.usar_no_pdv AS empresa_usar_no_pdv,
    ps.active,
    ps.allow_negative_stock,
    ps.ask_quantity,
    ps.show_discount_button,
    ps.created_at,
    ps.updated_at,
    COALESCE(u.name, u.username) AS updated_by_name
FROM pdv_settings ps
LEFT JOIN empresas e ON e.id = ps.company_id
LEFT JOIN users u ON u.id = ps.updated_by
ORDER BY ps.company_id, ps.pdv_number;
