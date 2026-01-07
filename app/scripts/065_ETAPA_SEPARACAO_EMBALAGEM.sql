-- =====================================================
-- SCRIPT: Adicionar etapa de Separação/Embalagem
-- Para produtos que já estão em estoque e não precisam produção
-- =====================================================

-- 1. Verificar se etapa já existe, senão criar
INSERT INTO producao_etapas (nome, descricao, ordem, ativo, tipo_etapa)
SELECT 'Separacao e Embalagem', 'Separar produto do estoque e embalar para envio', 999, 1, 'separacao'
FROM DUAL
WHERE NOT EXISTS (
    SELECT 1 FROM producao_etapas WHERE nome LIKE '%Separa%Embalag%'
);

-- 2. Adicionar coluna tipo_etapa se não existir
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'producao_etapas' AND COLUMN_NAME = 'tipo_etapa');
SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE producao_etapas ADD COLUMN tipo_etapa ENUM(''producao'', ''separacao'', ''embalagem'', ''expedicao'') DEFAULT ''producao'' COMMENT ''Tipo da etapa''',
    'SELECT ''Coluna tipo_etapa já existe''');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3. Adicionar coluna tipo_op na tabela ordens_producao se não existir
SET @col_exists2 = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ordens_producao' AND COLUMN_NAME = 'tipo_op');
SET @sql2 = IF(@col_exists2 = 0, 
    'ALTER TABLE ordens_producao ADD COLUMN tipo_op ENUM(''producao'', ''separacao'', ''mista'') DEFAULT ''producao'' COMMENT ''Tipo da OP: producao=fabricar, separacao=apenas separar do estoque''',
    'SELECT ''Coluna tipo_op já existe''');
PREPARE stmt2 FROM @sql2;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;

-- 4. Adicionar coluna origem_estoque para indicar de qual produto veio
SET @col_exists3 = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ordens_producao' AND COLUMN_NAME = 'produto_estoque_origem_id');
SET @sql3 = IF(@col_exists3 = 0, 
    'ALTER TABLE ordens_producao ADD COLUMN produto_estoque_origem_id INT NULL COMMENT ''ID do produto do estoque (quando tipo=separacao)''',
    'SELECT ''Coluna produto_estoque_origem_id já existe''');
PREPARE stmt3 FROM @sql3;
EXECUTE stmt3;
DEALLOCATE PREPARE stmt3;

-- 5. Adicionar campo para observação de estoque na OP
SET @col_exists4 = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ordens_producao' AND COLUMN_NAME = 'obs_estoque');
SET @sql4 = IF(@col_exists4 = 0, 
    'ALTER TABLE ordens_producao ADD COLUMN obs_estoque TEXT NULL COMMENT ''Informações sobre alocação de estoque''',
    'SELECT ''Coluna obs_estoque já existe''');
PREPARE stmt4 FROM @sql4;
EXECUTE stmt4;
DEALLOCATE PREPARE stmt4;

-- 6. View para resumo de OPs por tipo
CREATE OR REPLACE VIEW vw_ops_por_tipo AS
SELECT 
    op.id,
    op.numero_op,
    op.tipo_op,
    op.status,
    p.name AS produto_nome,
    op.quantidade,
    pe.name AS produto_estoque_nome,
    CASE op.tipo_op
        WHEN 'producao' THEN 'Produzir'
        WHEN 'separacao' THEN 'Separar do Estoque'
        WHEN 'mista' THEN 'Parcial Estoque + Produção'
    END AS tipo_descricao,
    op.created_at
FROM ordens_producao op
LEFT JOIN products p ON p.id = op.produto_id
LEFT JOIN products pe ON pe.id = op.produto_estoque_origem_id;

SELECT 'Script 065_ETAPA_SEPARACAO_EMBALAGEM.sql executado com sucesso!' AS resultado;
