-- =====================================================
-- TABELA DE MOVIMENTAÇÕES DE ESTOQUE
-- Registra todas as entradas e saídas de estoque
-- =====================================================

CREATE TABLE IF NOT EXISTS estoque_movimentacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    produto_id INT NOT NULL,
    
    -- Tipo: entrada, saida, ajuste, reserva, baixa_producao
    tipo ENUM('entrada', 'saida', 'ajuste', 'reserva', 'baixa_producao', 'devolucao') NOT NULL,
    
    -- Quantidade (positiva para entrada, negativa para saída)
    quantidade DECIMAL(15,4) NOT NULL,
    
    -- Estoque anterior e posterior
    estoque_anterior DECIMAL(15,4),
    estoque_posterior DECIMAL(15,4),
    
    -- Referência (qual documento originou a movimentação)
    referencia_tipo VARCHAR(50) COMMENT 'orcamento, op, compra, venda, ajuste_manual',
    referencia_id INT COMMENT 'ID do documento de origem',
    
    -- Custo unitário no momento da movimentação
    custo_unitario DECIMAL(15,4),
    
    -- Localização
    local_origem VARCHAR(100),
    local_destino VARCHAR(100),
    
    -- Observações
    observacao TEXT,
    
    -- Metadados
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INT,
    
    INDEX idx_produto (produto_id),
    INDEX idx_tipo (tipo),
    INDEX idx_referencia (referencia_tipo, referencia_id),
    INDEX idx_data (created_at),
    
    FOREIGN KEY (produto_id) REFERENCES products(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- View para saldo de estoque com movimentações
CREATE OR REPLACE VIEW vw_estoque_saldo AS
SELECT 
    p.id AS produto_id,
    p.name AS produto_nome,
    p.internal_code,
    COALESCE(p.stock_quantity, 0) AS estoque_sistema,
    COALESCE(
        (SELECT SUM(CASE WHEN em.tipo IN ('entrada', 'devolucao') THEN em.quantidade ELSE -em.quantidade END)
         FROM estoque_movimentacoes em WHERE em.produto_id = p.id), 0
    ) AS saldo_movimentacoes,
    COALESCE(
        (SELECT SUM(er.quantidade) FROM estoque_reservas er 
         WHERE er.produto_id = p.id AND er.status IN ('ativo', 'confirmado')), 0
    ) AS reservado,
    COALESCE(p.stock_quantity, 0) - COALESCE(
        (SELECT SUM(er.quantidade) FROM estoque_reservas er 
         WHERE er.produto_id = p.id AND er.status IN ('ativo', 'confirmado')), 0
    ) AS disponivel
FROM products p
WHERE p.active = 1;

SELECT 'Tabela estoque_movimentacoes criada!' AS resultado;
