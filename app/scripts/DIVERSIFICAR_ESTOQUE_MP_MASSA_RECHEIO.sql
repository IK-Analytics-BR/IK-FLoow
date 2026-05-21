-- =============================================================================
-- DIVERSIFICAR ESTOQUE DE MP PARA MASSAS E RECHEIOS
-- Objetivo: deixar ~1/3 dos itens próximo ao mínimo (vermelho/amarelo),
--           ~1/3 no intermediário, ~1/3 próximo ao máximo (verde).
-- Isso garante que a tela de planejamento mostre cores variadas e
-- identifique itens que precisam de compra.
-- =============================================================================

-- Primeiro, garantir que todos os produtos de MP usados em MASSA e RECHEIO
-- tenham registro em current_stock com min_stock e max_stock configurados.

-- 1) Inserir current_stock para MPs que ainda não têm registro
INSERT IGNORE INTO current_stock (product_id, location_id, quantity, min_stock, max_stock)
SELECT DISTINCT
    ti.produto_id,
    1,
    0,
    ROUND(5 + RAND() * 15, 2),    -- min_stock entre 5 e 20
    ROUND(80 + RAND() * 120, 2)   -- max_stock entre 80 e 200
FROM produto_template_itens ti
INNER JOIN produto_templates_producao t ON t.id = ti.template_id AND t.ativo = 1
INNER JOIN products p_final ON p_final.id = t.produto_id
INNER JOIN products p_item ON p_item.id = ti.produto_id
WHERE (p_final.name LIKE 'MASSA - %' OR p_final.name LIKE 'RECHEIO - %'
       OR p_final.category = 'Semiacabado (Massa/Recheio/Caldo)')
  AND p_item.active = 1
  AND ti.produto_id NOT IN (SELECT product_id FROM current_stock WHERE location_id = 1);

-- 2) Garantir min_stock e max_stock para os que já existem mas estão zerados
UPDATE current_stock cs
INNER JOIN produto_template_itens ti ON ti.produto_id = cs.product_id
INNER JOIN produto_templates_producao t ON t.id = ti.template_id AND t.ativo = 1
INNER JOIN products p_final ON p_final.id = t.produto_id
SET
    cs.min_stock = CASE WHEN cs.min_stock <= 0 THEN ROUND(5 + RAND() * 15, 2) ELSE cs.min_stock END,
    cs.max_stock = CASE WHEN cs.max_stock <= 0 THEN ROUND(80 + RAND() * 120, 2) ELSE cs.max_stock END
WHERE cs.location_id = 1
  AND (p_final.name LIKE 'MASSA - %' OR p_final.name LIKE 'RECHEIO - %'
       OR p_final.category = 'Semiacabado (Massa/Recheio/Caldo)')
  AND (cs.min_stock <= 0 OR cs.max_stock <= 0);

-- 3) Agora diversificar os estoques usando MOD do ID para distribuir em 3 faixas:
--    - MOD 3 = 0 -> BAIXO (entre 0 e min_stock * 1.2) => vermelho/amarelo
--    - MOD 3 = 1 -> MÉDIO (entre min_stock e ponto médio)  => amarelo
--    - MOD 3 = 2 -> ALTO  (entre 60% e 95% do max_stock)   => verde

UPDATE current_stock cs
INNER JOIN (
    SELECT DISTINCT ti.produto_id
    FROM produto_template_itens ti
    INNER JOIN produto_templates_producao t ON t.id = ti.template_id AND t.ativo = 1
    INNER JOIN products p_final ON p_final.id = t.produto_id
    WHERE p_final.name LIKE 'MASSA - %'
       OR p_final.name LIKE 'RECHEIO - %'
       OR p_final.category = 'Semiacabado (Massa/Recheio/Caldo)'
) mp ON mp.produto_id = cs.product_id
SET cs.quantity = CASE
    -- FAIXA BAIXA (vermelho): estoque entre 0 e min_stock (ou pouco acima)
    WHEN MOD(cs.product_id, 3) = 0 THEN ROUND(cs.min_stock * RAND() * 0.8, 2)
    -- FAIXA MÉDIA (amarelo): estoque entre min_stock e ponto médio
    WHEN MOD(cs.product_id, 3) = 1 THEN ROUND(cs.min_stock + (cs.max_stock - cs.min_stock) * (0.2 + RAND() * 0.3), 2)
    -- FAIXA ALTA (verde): estoque entre 65% e 95% do max
    ELSE ROUND(cs.max_stock * (0.65 + RAND() * 0.30), 2)
END
WHERE cs.location_id = 1;

-- 4) Sincronizar products.stock_quantity com current_stock.quantity
UPDATE products p
INNER JOIN current_stock cs ON cs.product_id = p.id AND cs.location_id = 1
INNER JOIN (
    SELECT DISTINCT ti.produto_id
    FROM produto_template_itens ti
    INNER JOIN produto_templates_producao t ON t.id = ti.template_id AND t.ativo = 1
    INNER JOIN products p_final ON p_final.id = t.produto_id
    WHERE p_final.name LIKE 'MASSA - %'
       OR p_final.name LIKE 'RECHEIO - %'
       OR p_final.category = 'Semiacabado (Massa/Recheio/Caldo)'
) mp ON mp.produto_id = p.id
SET p.stock_quantity = cs.quantity;

-- 5) Verificação: listar os MPs atualizados com suas faixas
SELECT
    p.id,
    p.name,
    cs.quantity AS estoque_atual,
    cs.min_stock,
    cs.max_stock,
    CASE
        WHEN cs.quantity <= cs.min_stock THEN 'VERMELHO (baixo)'
        WHEN cs.quantity <= cs.min_stock + (cs.max_stock - cs.min_stock) * 0.33 THEN 'AMARELO (médio-baixo)'
        WHEN cs.quantity <= cs.min_stock + (cs.max_stock - cs.min_stock) * 0.66 THEN 'AMARELO (médio)'
        ELSE 'VERDE (ok)'
    END AS faixa
FROM current_stock cs
INNER JOIN products p ON p.id = cs.product_id
INNER JOIN (
    SELECT DISTINCT ti.produto_id
    FROM produto_template_itens ti
    INNER JOIN produto_templates_producao t ON t.id = ti.template_id AND t.ativo = 1
    INNER JOIN products p_final ON p_final.id = t.produto_id
    WHERE p_final.name LIKE 'MASSA - %'
       OR p_final.name LIKE 'RECHEIO - %'
       OR p_final.category = 'Semiacabado (Massa/Recheio/Caldo)'
) mp ON mp.produto_id = p.id
WHERE cs.location_id = 1
ORDER BY cs.quantity / NULLIF(cs.max_stock, 0) ASC;
