-- =====================================================
-- ADICIONAR CAMPO DE LOGO NA TABELA EMPRESA
-- =====================================================

USE supply_chain_system;

-- Verificar se a coluna já existe antes de adicionar
SET @dbname = DATABASE();
SET @tablename = 'empresa';
SET @columnname = 'logo_path';

SET @preparedStatement = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = @dbname
     AND TABLE_NAME = @tablename
     AND COLUMN_NAME = @columnname) > 0,
    'SELECT ''Coluna logo_path já existe.'' AS resultado;',
    'ALTER TABLE empresa ADD COLUMN logo_path VARCHAR(255) NULL AFTER website;'
));

PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

SELECT '✅ Campo logo_path adicionado (ou já existia) na tabela empresa!' AS resultado;

-- Verificar estrutura
DESCRIBE empresa;
