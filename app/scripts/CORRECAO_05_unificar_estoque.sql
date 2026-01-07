-- =====================================================
-- CORREÇÃO #5: Unificar Fontes de Estoque
-- =====================================================
-- OBJETIVO: Usar APENAS current_stock como fonte única
-- PROBLEMA: Sistema tem 3 fontes: products.stock, current_stock, SUM(stock_movements)
-- DATA: 22/10/2025
-- =====================================================

-- =====================================================
-- FASE 1: SINCRONIZAR DADOS
-- =====================================================

-- PASSO 1: Garantir que current_stock existe para todos os produtos
-- Cria registros faltantes com quantity=0
INSERT IGNORE INTO current_stock (product_id, location_id, quantity, min_stock, max_stock)
SELECT 
    p.id AS product_id,
    1 AS location_id,  -- Local padrão
    0 AS quantity,
    COALESCE(p.min_stock, 0) AS min_stock,
    0 AS max_stock
FROM products p
WHERE p.active = TRUE
  AND NOT EXISTS (
      SELECT 1 FROM current_stock cs 
      WHERE cs.product_id = p.id AND cs.location_id = 1
  );

-- PASSO 2: Sincronizar current_stock com products + stock_movements
-- Calcula: current_stock = products.stock + SUM(stock_movements)
UPDATE current_stock cs
INNER JOIN products p ON cs.product_id = p.id
LEFT JOIN (
    SELECT 
        product_id, 
        location_id,
        SUM(quantity) AS total_movements
    FROM stock_movements
    GROUP BY product_id, location_id
) sm ON cs.product_id = sm.product_id AND cs.location_id = sm.location_id
SET cs.quantity = COALESCE(
    -- Tentar todas as variações de nome de coluna
    p.stock, 
    p.start_stock, 
    p.opening_stock, 
    p.initial_stock,
    p.estoque_inicial,
    p.quantity,
    0
) + COALESCE(sm.total_movements, 0);

-- PASSO 3: Verificar sincronização
SELECT 
    p.id,
    p.name AS produto,
    COALESCE(p.stock, p.start_stock, p.opening_stock, 0) AS estoque_products,
    COALESCE(sm.total, 0) AS movimentos,
    cs.quantity AS estoque_current_stock,
    (COALESCE(p.stock, p.start_stock, p.opening_stock, 0) + COALESCE(sm.total, 0)) AS calculado,
    CASE 
        WHEN cs.quantity = (COALESCE(p.stock, p.start_stock, p.opening_stock, 0) + COALESCE(sm.total, 0)) 
        THEN '✓ OK'
        ELSE '✗ DIVERGENTE'
    END AS status
FROM products p
LEFT JOIN current_stock cs ON p.id = cs.product_id AND cs.location_id = 1
LEFT JOIN (
    SELECT product_id, SUM(quantity) AS total 
    FROM stock_movements 
    GROUP BY product_id
) sm ON p.id = sm.product_id
WHERE p.active = TRUE
ORDER BY p.name
LIMIT 100;

-- =====================================================
-- FASE 2: CRIAR TRIGGER PARA MANTER SINCRONIA
-- =====================================================

-- Trigger para atualizar current_stock quando houver movimento
DELIMITER $$

DROP TRIGGER IF EXISTS trg_stock_movements_after_insert$$
CREATE TRIGGER trg_stock_movements_after_insert
AFTER INSERT ON stock_movements
FOR EACH ROW
BEGIN
    -- Atualizar current_stock
    INSERT INTO current_stock (product_id, location_id, quantity)
    VALUES (NEW.product_id, COALESCE(NEW.location_id, 1), NEW.quantity)
    ON DUPLICATE KEY UPDATE 
        quantity = quantity + NEW.quantity;
END$$

DELIMITER ;

-- =====================================================
-- FASE 3: REMOVER COLUNAS OBSOLETAS (APÓS VALIDAR!)
-- =====================================================

-- ATENÇÃO: Execute apenas após confirmar que tudo funciona!
-- 
-- ALTER TABLE products 
-- DROP COLUMN IF EXISTS stock,
-- DROP COLUMN IF EXISTS start_stock,
-- DROP COLUMN IF EXISTS opening_stock,
-- DROP COLUMN IF EXISTS initial_stock,
-- DROP COLUMN IF EXISTS estoque_inicial,
-- DROP COLUMN IF EXISTS qty,
-- DROP COLUMN IF EXISTS on_hand,
-- DROP COLUMN IF EXISTS saldo;

-- =====================================================
-- QUERIES DE VERIFICAÇÃO
-- =====================================================

-- Query 1: Produtos com divergência
SELECT 
    p.id,
    p.name,
    cs.quantity AS estoque_atual,
    (SELECT SUM(quantity) FROM stock_movements WHERE product_id = p.id) AS soma_movimentos,
    COALESCE(p.stock, 0) AS products_stock
FROM products p
LEFT JOIN current_stock cs ON p.id = cs.product_id
WHERE p.active = TRUE
  AND cs.quantity != COALESCE(p.stock, 0) + (SELECT COALESCE(SUM(quantity), 0) FROM stock_movements WHERE product_id = p.id)
LIMIT 50;

-- Query 2: Verificar integridade
SELECT 
    'Total Produtos' AS metrica,
    COUNT(*) AS valor
FROM products
WHERE active = TRUE
UNION ALL
SELECT 
    'Com registro em current_stock',
    COUNT(DISTINCT cs.product_id)
FROM current_stock cs
INNER JOIN products p ON cs.product_id = p.id
WHERE p.active = TRUE
UNION ALL
SELECT 
    'Com movimentos',
    COUNT(DISTINCT sm.product_id)
FROM stock_movements sm
INNER JOIN products p ON sm.product_id = p.id
WHERE p.active = TRUE;

-- =====================================================
-- ROLLBACK (se necessário)
-- =====================================================
-- Para reverter:
-- 
-- DROP TRIGGER IF EXISTS trg_stock_movements_after_insert;
-- 
-- -- Restaurar products.stock do backup
-- UPDATE products p
-- LEFT JOIN products_backup pb ON p.id = pb.id
-- SET p.stock = pb.stock;
-- =====================================================

-- =====================================================
-- INSTRUÇÕES DE USO
-- =====================================================
-- 
-- 1. BACKUP PRIMEIRO!
--    mysqldump -u root -p supply_chain_system > backup_antes_correcao_05.sql
--
-- 2. Executar FASE 1 (sincronizar)
--
-- 3. Executar queries de verificação
--
-- 4. Executar FASE 2 (criar trigger)
--
-- 5. Testar criando venda e pedido
--
-- 6. Após 1 semana de testes, executar FASE 3 (remover colunas)
--
-- =====================================================
