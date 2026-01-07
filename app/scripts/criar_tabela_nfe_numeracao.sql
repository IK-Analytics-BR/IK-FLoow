-- =====================================================
-- TABELA DE CONTROLE DE NUMERAÇÃO DE NF-e
-- Permite configurar último número por empresa/série/ambiente
-- =====================================================

CREATE TABLE IF NOT EXISTS nfe_numeracao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    serie INT NOT NULL DEFAULT 1,
    ambiente ENUM('homologacao', 'producao') NOT NULL DEFAULT 'homologacao',
    ultimo_numero INT NOT NULL DEFAULT 0,
    observacao VARCHAR(255) NULL COMMENT 'Ex: Migração do sistema X',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Chave única: empresa + série + ambiente
    UNIQUE KEY uk_empresa_serie_ambiente (empresa_id, serie, ambiente),
    
    -- Índices
    INDEX idx_empresa (empresa_id),
    INDEX idx_ambiente (ambiente),
    
    -- FK para empresas
    CONSTRAINT fk_numeracao_empresa FOREIGN KEY (empresa_id) 
        REFERENCES empresas(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Inserir configuração inicial para empresa 9 (exemplo)
-- INSERT INTO nfe_numeracao (empresa_id, serie, ambiente, ultimo_numero, observacao) 
-- VALUES (9, 1, 'producao', 123456, 'Migração do sistema anterior');
