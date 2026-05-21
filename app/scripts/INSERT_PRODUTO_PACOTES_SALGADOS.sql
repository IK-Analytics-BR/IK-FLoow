-- Script de inserção de pacotes comerciais (produto_pacotes) para SALGADOS
-- Gerado a partir da tabela de FRITURAS, MINI FRITURAS, CHIPA, PÃO DE QUEIJO, SALGADOS PRÉ-ASSADOS e LINHA DE ASSADOS.
-- Pode ser executado múltiplas vezes: cada INSERT tem proteção para não duplicar (NOT EXISTS).

USE `supply_chain_system`;

TRUNCATE TABLE produto_pacotes;

-- =====================================================================
-- 1) FRITURAS (P/ FRITAR) - pct c/ 10 un (R$ 43,87 / 4,39)
-- =====================================================================

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'FRITURAS (P/ FRITAR) - pct c/ 10 un',
       'PCT',
       10,
       NULL,
       43.87,
       4.39,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%COXINHA FRANGO 140 GRS%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'FRITURAS (P/ FRITAR) - pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'FRITURAS (P/ FRITAR) - pct c/ 10 un',
       'PCT',
       10,
       NULL,
       43.87,
       4.39,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%COXINHA CARNE 140 GRS%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'FRITURAS (P/ FRITAR) - pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'FRITURAS (P/ FRITAR) - pct c/ 10 un',
       'PCT',
       10,
       NULL,
       43.87,
       4.39,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%COXINHOCA CARNE SECA 130 GRS%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'FRITURAS (P/ FRITAR) - pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'FRITURAS (P/ FRITAR) - pct c/ 10 un',
       'PCT',
       10,
       NULL,
       43.87,
       4.39,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%RISOLES FRANGO%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'FRITURAS (P/ FRITAR) - pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'FRITURAS (P/ FRITAR) - pct c/ 10 un',
       'PCT',
       10,
       NULL,
       43.87,
       4.39,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%RISOLES CARNE%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'FRITURAS (P/ FRITAR) - pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'FRITURAS (P/ FRITAR) - pct c/ 10 un',
       'PCT',
       10,
       NULL,
       43.87,
       4.39,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%RISOLES PIZZA%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'FRITURAS (P/ FRITAR) - pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'FRITURAS (P/ FRITAR) - pct c/ 10 un',
       'PCT',
       10,
       NULL,
       43.87,
       4.39,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%ENROLADINHO SALSICHA 140%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'FRITURAS (P/ FRITAR) - pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'FRITURAS (P/ FRITAR) - pct c/ 10 un',
       'PCT',
       10,
       NULL,
       43.87,
       4.39,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%ENROLADINHO PRES/QUEIJO 140%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'FRITURAS (P/ FRITAR) - pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'FRITURAS (P/ FRITAR) - pct c/ 10 un',
       'PCT',
       10,
       NULL,
       43.87,
       4.39,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%QUIBE CARNE 130%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'FRITURAS (P/ FRITAR) - pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'FRITURAS (P/ FRITAR) - ESPETO FRANGO pct c/ 10 un',
       'PCT',
       10,
       NULL,
       60.45,
       6.05,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%ESPETO%FRANGO%120%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'FRITURAS (P/ FRITAR) - ESPETO FRANGO pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'FRITURAS (P/ FRITAR) - BOLINHO CARNE pct c/ 10 un',
       'PCT',
       10,
       NULL,
       55.65,
       5.57,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%BOLINHO CARNE%140%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'FRITURAS (P/ FRITAR) - BOLINHO CARNE pct c/ 10 un'
    );

-- =====================================================================
-- 2) FRITURAS (FRITOS) - pct c/ 10 un (R$ 47,10 / 4,71)
-- =====================================================================

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'FRITURAS (FRITOS) - pct c/ 10 un',
       'PCT',
       10,
       NULL,
       47.10,
       4.71,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%COXINHOCA FRANGO%130%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'FRITURAS (FRITOS) - pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'FRITURAS (FRITOS) - pct c/ 10 un',
       'PCT',
       10,
       NULL,
       47.10,
       4.71,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%COXINHOCA CARNE%130%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'FRITURAS (FRITOS) - pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'FRITURAS (FRITOS) - pct c/ 10 un',
       'PCT',
       10,
       NULL,
       47.10,
       4.71,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%COXINHOCA CARNE SECA%110%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'FRITURAS (FRITOS) - pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'FRITURAS (FRITOS) - pct c/ 10 un',
       'PCT',
       10,
       NULL,
       47.10,
       4.71,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%RISOLES FRANGO%140%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'FRITURAS (FRITOS) - pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'FRITURAS (FRITOS) - pct c/ 10 un',
       'PCT',
       10,
       NULL,
       47.10,
       4.71,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%RISOLES CARNE%140%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'FRITURAS (FRITOS) - pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'FRITURAS (FRITOS) - pct c/ 10 un',
       'PCT',
       10,
       NULL,
       47.10,
       4.71,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%RISOLES PIZZA%140%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'FRITURAS (FRITOS) - pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'FRITURAS (FRITOS) - pct c/ 10 un',
       'PCT',
       10,
       NULL,
       47.10,
       4.71,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%ENROLADINHO SALSICHA%120%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'FRITURAS (FRITOS) - pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'FRITURAS (FRITOS) - pct c/ 10 un',
       'PCT',
       10,
       NULL,
       47.10,
       4.71,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%ENROLADINHO PRES/QUEIJO%130%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'FRITURAS (FRITOS) - pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'FRITURAS (FRITOS) - pct c/ 10 un',
       'PCT',
       10,
       NULL,
       47.10,
       4.71,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%QUIBE CARNE%120%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'FRITURAS (FRITOS) - pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'FRITURAS (FRITOS) - ESPETO FRANGO pct c/ 10 un',
       'PCT',
       10,
       NULL,
       63.65,
       6.37,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%ESPETO%FRANGO%110%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'FRITURAS (FRITOS) - ESPETO FRANGO pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'FRITURAS (FRITOS) - BOLINHO CARNE pct c/ 10 un',
       'PCT',
       10,
       NULL,
       58.85,
       5.89,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%BOLINHO CARNE%130%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'FRITURAS (FRITOS) - BOLINHO CARNE pct c/ 10 un'
    );

-- =====================================================================
-- 3) MINI FRITURAS (P/ FRITAR) - 1kg (aprox 50 un) (R$ 30,28 / 0,61)
-- =====================================================================

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'MINI FRITURAS (P/ FRITAR) - 1kg (aprox 50 un)',
       'PCT',
       50,
       1.0,
       30.28,
       0.61,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%COXINHA FRANGO MAND 20 GRS%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'MINI FRITURAS (P/ FRITAR) - 1kg (aprox 50 un)'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'MINI FRITURAS (P/ FRITAR) - 1kg (aprox 50 un)',
       'PCT',
       50,
       1.0,
       30.28,
       0.61,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%COXINHA CARNE MAND 20 GRS%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'MINI FRITURAS (P/ FRITAR) - 1kg (aprox 50 un)'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'MINI FRITURAS (P/ FRITAR) - 1kg (aprox 50 un)',
       'PCT',
       50,
       1.0,
       30.28,
       0.61,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%CROQUETE CARNE SECA 20 GRS%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'MINI FRITURAS (P/ FRITAR) - 1kg (aprox 50 un)'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'MINI FRITURAS (P/ FRITAR) - 1kg (aprox 50 un)',
       'PCT',
       50,
       1.0,
       30.28,
       0.61,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%BOLINHA DE QUEIJO 20 GRS%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'MINI FRITURAS (P/ FRITAR) - 1kg (aprox 50 un)'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'MINI FRITURAS (P/ FRITAR) - 1kg (aprox 50 un)',
       'PCT',
       50,
       1.0,
       30.28,
       0.61,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%ENROLADINHO PRES/QUEIJO 20GRS%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'MINI FRITURAS (P/ FRITAR) - 1kg (aprox 50 un)'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'MINI FRITURAS (P/ FRITAR) - 1kg (aprox 50 un)',
       'PCT',
       50,
       1.0,
       30.28,
       0.61,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%QUIBE CARNE 20 GR%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'MINI FRITURAS (P/ FRITAR) - 1kg (aprox 50 un)'
    );

-- =====================================================================
-- 4) MINI FRITURAS (FRITOS) - 1kg (aprox 50 un) (R$ 33,70 / 0,67)
-- =====================================================================

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'MINI FRITURAS (FRITOS) - 1kg (aprox 50 un)',
       'PCT',
       50,
       1.0,
       33.70,
       0.67,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%COXINHA FRANGO MAND 20 GRS%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'MINI FRITURAS (FRITOS) - 1kg (aprox 50 un)'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'MINI FRITURAS (FRITOS) - 1kg (aprox 50 un)',
       'PCT',
       50,
       1.0,
       33.70,
       0.67,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%COXINHA CARNE MAND 20 GRS%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'MINI FRITURAS (FRITOS) - 1kg (aprox 50 un)'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'MINI FRITURAS (FRITOS) - 1kg (aprox 50 un)',
       'PCT',
       50,
       1.0,
       33.70,
       0.67,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%CROQUETE CARNE SECA 20 GRS%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'MINI FRITURAS (FRITOS) - 1kg (aprox 50 un)'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'MINI FRITURAS (FRITOS) - 1kg (aprox 50 un)',
       'PCT',
       50,
       1.0,
       33.70,
       0.67,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%BOLINHA DE QUEIJO 20 GRS%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'MINI FRITURAS (FRITOS) - 1kg (aprox 50 un)'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'MINI FRITURAS (FRITOS) - 1kg (aprox 50 un)',
       'PCT',
       50,
       1.0,
       33.70,
       0.67,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%ENROLADINHO PRES/QUEIJO 20GRS%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'MINI FRITURAS (FRITOS) - 1kg (aprox 50 un)'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'MINI FRITURAS (FRITOS) - 1kg (aprox 50 un)',
       'PCT',
       50,
       1.0,
       33.70,
       0.67,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%QUIBE CARNE 20 GR%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'MINI FRITURAS (FRITOS) - 1kg (aprox 50 un)'
    );

-- =====================================================================
-- 5) MINI FRITURAS (FRITOS) - 400g (aprox 20 un) (R$ 13,80 / 0,69)
-- =====================================================================

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'MINI FRITURAS (FRITOS) - 400g (aprox 20 un)',
       'PCT',
       20,
       0.4,
       13.80,
       0.69,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%COXINHA FRANGO MAND 20 GRS%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'MINI FRITURAS (FRITOS) - 400g (aprox 20 un)'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'MINI FRITURAS (FRITOS) - 400g (aprox 20 un)',
       'PCT',
       20,
       0.4,
       13.80,
       0.69,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%COXINHA CARNE MAND 20 GRS%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'MINI FRITURAS (FRITOS) - 400g (aprox 20 un)'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'MINI FRITURAS (FRITOS) - 400g (aprox 20 un)',
       'PCT',
       20,
       0.4,
       13.80,
       0.69,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%CROQUETE CARNE SECA 20 GRS%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'MINI FRITURAS (FRITOS) - 400g (aprox 20 un)'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'MINI FRITURAS (FRITOS) - 400g (aprox 20 un)',
       'PCT',
       20,
       0.4,
       13.80,
       0.69,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%MINI CHURROS%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'MINI FRITURAS (FRITOS) - 400g (aprox 20 un)'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'MINI FRITURAS (FRITOS) - 400g (aprox 20 un)',
       'PCT',
       20,
       0.4,
       13.80,
       0.69,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%BOLINHA DE QUEIJO 20 GRS%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'MINI FRITURAS (FRITOS) - 400g (aprox 20 un)'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'MINI FRITURAS (FRITOS) - 400g (aprox 20 un)',
       'PCT',
       20,
       0.4,
       13.80,
       0.69,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%ENROLADINHO PRES/QUEIJO 20GRS%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'MINI FRITURAS (FRITOS) - 400g (aprox 20 un)'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'MINI FRITURAS (FRITOS) - 400g (aprox 20 un)',
       'PCT',
       20,
       0.4,
       13.80,
       0.69,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%QUIBE CARNE 20 GR%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'MINI FRITURAS (FRITOS) - 400g (aprox 20 un)'
    );

-- =====================================================================
-- 6) CHIPA
-- =====================================================================

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'CHIPA PIETRO ARTESANAL - pct c/ 10 un',
       'PCT',
       10,
       NULL,
       37.80,
       3.78,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%CHIPA PIETRO ARTESANAL 120 GRS%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'CHIPA PIETRO ARTESANAL - pct c/ 10 un'
    );

-- =====================================================================
-- 7) PÃO DE QUEIJO TRADICIONAL 90g - pct 2kg c/ 22 un
-- =====================================================================

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'PÃO DE QUEIJO TRADICIONAL 90g - pct 2kg c/ 22 un',
       'PCT',
       22,
       2.0,
       55.65,
       2.53,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%PÃO DE QUEIJO TRADICIONAL 90 GRS 2KG%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'PÃO DE QUEIJO TRADICIONAL 90g - pct 2kg c/ 22 un'
    );

-- =====================================================================
-- 8) SALGADOS PRÉ-ASSADOS - EMPADAS (se existirem no cadastro)
-- =====================================================================

-- ATENÇÃO: confirme antes se os produtos de EMPADA existem no cadastro
-- Exemplo de conferência:
-- SELECT id, name FROM products WHERE name LIKE '%EMPADA%';

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'SALGADOS PRÉ-ASSADOS - EMPADA FRANGO pct c/ 6 un',
       'PCT',
       6,
       NULL,
       25.70,
       4.28,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%EMPADA%' AND p.name LIKE '%FRANGO%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'SALGADOS PRÉ-ASSADOS - EMPADA FRANGO pct c/ 6 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'SALGADOS PRÉ-ASSADOS - EMPADA PALMITO pct c/ 6 un',
       'PCT',
       6,
       NULL,
       25.70,
       4.28,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%EMPADA%' AND p.name LIKE '%PALMITO%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'SALGADOS PRÉ-ASSADOS - EMPADA PALMITO pct c/ 6 un'
    );

-- =====================================================================
-- 9) LINHA DE ASSADOS
-- =====================================================================

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'LINHA DE ASSADOS - BAURU HOT DOG pct c/ 10 un',
       'PCT',
       10,
       NULL,
       47.83,
       4.78,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%BAURU HOT DOG%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'LINHA DE ASSADOS - BAURU HOT DOG pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'LINHA DE ASSADOS - BAURU PRESUNTO E QUEIJO (COM TOMATE) pct c/ 10 un',
       'PCT',
       10,
       NULL,
       47.83,
       4.78,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%BAURU PRESUNTO E QUEIJO%TOMATE%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'LINHA DE ASSADOS - BAURU PRESUNTO E QUEIJO (COM TOMATE) pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'LINHA DE ASSADOS - MISTINHO PRES/QUEIJO (SEM TOMATE) pct c/ 10 un',
       'PCT',
       10,
       NULL,
       47.83,
       4.78,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%MISTINHO PRESUNTO E QUEIJO%SEM TOMATE%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'LINHA DE ASSADOS - MISTINHO PRES/QUEIJO (SEM TOMATE) pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'LINHA DE ASSADOS - ITALIANINHO CALABRESA pct c/ 10 un',
       'PCT',
       10,
       NULL,
       47.83,
       4.78,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%ITALIANINHO%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'LINHA DE ASSADOS - ITALIANINHO CALABRESA pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'LINHA DE ASSADOS - ESFIHA CARNE pct c/ 10 un',
       'PCT',
       10,
       NULL,
       47.83,
       4.78,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%ESFIHA CARNE%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'LINHA DE ASSADOS - ESFIHA CARNE pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'LINHA DE ASSADOS - ESFIHA FRANGO pct c/ 10 un',
       'PCT',
       10,
       NULL,
       47.83,
       4.78,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%ESFIHA FRANGO%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'LINHA DE ASSADOS - ESFIHA FRANGO pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'LINHA DE ASSADOS - X-BURGUER CARNE pct c/ 10 un',
       'PCT',
       10,
       NULL,
       51.25,
       5.13,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%X-BURGUER CARNE%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'LINHA DE ASSADOS - X-BURGUER CARNE pct c/ 10 un'
    );

INSERT INTO produto_pacotes (
    produto_id,
    descricao,
    unidade_comercial,
    unidades_por_pacote,
    peso_pacote_kg,
    preco_pacote,
    preco_unidade,
    ativo,
    padrao_planejamento
)
SELECT p.id,
       'LINHA DE ASSADOS - X-BURGUER CHEDDAR pct c/ 10 un',
       'PCT',
       10,
       NULL,
       51.25,
       5.13,
       1,
       1
FROM products p
LEFT JOIN product_categories pc0
       ON pc0.id = p.category_id
      AND pc0.categoria_fiscal IN ('Produto', 'produto', 'produto_producao')
WHERE p.active = 1 AND p.name LIKE '%X-BURGUER CHEDDAR%'
  AND NOT EXISTS (
        SELECT 1 FROM produto_pacotes pp
        WHERE pp.produto_id = p.id
          AND pp.descricao = 'LINHA DE ASSADOS - X-BURGUER CHEDDAR pct c/ 10 un'
    );

-- =====================================================================
-- Fim do script de pacotes de SALGADOS
-- =====================================================================
