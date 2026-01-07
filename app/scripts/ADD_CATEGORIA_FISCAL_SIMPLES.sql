-- ========================================
-- ADICIONAR COLUNA CATEGORIA_FISCAL - VERSÃO SIMPLES
-- Execute linha por linha se necessário
-- ========================================

USE supply_chain_system;

-- ========================================
-- ADICIONAR COLUNA
-- ========================================

-- Se a coluna NÃO existir, execute este comando:
ALTER TABLE products 
ADD COLUMN categoria_fiscal ENUM('servico', 'materia_prima', 'consumo_interno', 'produto_final') DEFAULT NULL 
AFTER category_id;

-- Se der erro "Duplicate column name", ignore - a coluna já existe!

-- ========================================
-- ADICIONAR ÍNDICE
-- ========================================

-- Se o índice NÃO existir, execute este comando:
CREATE INDEX idx_categoria_fiscal ON products(categoria_fiscal);

-- Se der erro "Duplicate key name", ignore - o índice já existe!

-- ========================================
-- VERIFICAÇÃO
-- ========================================

-- Ver estrutura da tabela
DESCRIBE products;

-- Ver se a coluna foi criada
SELECT column_name, column_type, is_nullable, column_default
FROM information_schema.COLUMNS
WHERE table_schema = 'supply_chain_system'
AND table_name = 'products'
AND column_name = 'categoria_fiscal';

-- Ver se o índice foi criado
SELECT index_name, column_name
FROM information_schema.STATISTICS
WHERE table_schema = 'supply_chain_system'
AND table_name = 'products'
AND index_name = 'idx_categoria_fiscal';
