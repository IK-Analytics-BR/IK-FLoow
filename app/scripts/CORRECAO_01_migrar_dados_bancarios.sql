-- =====================================================
-- CORREÇÃO #1: Migrar Dados Bancários para bank_accounts
-- =====================================================
-- OBJETIVO: Eliminar duplicação de dados bancários
-- TABELAS: empresas, bank_accounts
-- DATA: 22/10/2025
-- =====================================================

-- PASSO 1: Adicionar coluna bank_account_id na tabela empresas
ALTER TABLE empresas 
ADD COLUMN bank_account_id INT NULL,
ADD CONSTRAINT fk_empresas_bank_account 
    FOREIGN KEY (bank_account_id) REFERENCES bank_accounts(id)
    ON DELETE SET NULL;

-- PASSO 2: Migrar dados bancários existentes para bank_accounts
-- (Cria conta bancária para cada empresa que tem dados bancários)
INSERT INTO bank_accounts (name, agency, account_number, cost_center, status, created_at)
SELECT 
    CONCAT('Conta - ', nome_fantasia) AS name,
    agencia AS agency,
    conta AS account_number,
    'Empresas' AS cost_center,
    'active' AS status,
    NOW() AS created_at
FROM empresas
WHERE banco IS NOT NULL 
  AND banco != ''
  AND ativo = TRUE;

-- PASSO 3: Atualizar bank_account_id nas empresas
UPDATE empresas e
INNER JOIN bank_accounts ba ON ba.account_number = e.conta AND ba.agency = e.agencia
SET e.bank_account_id = ba.id
WHERE e.banco IS NOT NULL AND e.banco != '';

-- PASSO 4: Verificar migração
SELECT 
    e.id,
    e.nome_fantasia,
    e.banco AS banco_antigo,
    e.bank_account_id,
    ba.name AS conta_bancaria_nova
FROM empresas e
LEFT JOIN bank_accounts ba ON e.bank_account_id = ba.id
WHERE e.ativo = TRUE;

-- PASSO 5: APÓS VERIFICAR QUE TUDO ESTÁ OK, remover colunas antigas
-- ATENÇÃO: Execute apenas após confirmar que dados migraram corretamente!
-- ALTER TABLE empresas 
-- DROP COLUMN banco,
-- DROP COLUMN agencia,
-- DROP COLUMN conta,
-- DROP COLUMN tipo_conta;

-- =====================================================
-- ROLLBACK (se necessário)
-- =====================================================
-- Para reverter as mudanças:
-- 
-- ALTER TABLE empresas DROP FOREIGN KEY fk_empresas_bank_account;
-- ALTER TABLE empresas DROP COLUMN bank_account_id;
-- DELETE FROM bank_accounts WHERE cost_center = 'Empresas';
-- =====================================================
