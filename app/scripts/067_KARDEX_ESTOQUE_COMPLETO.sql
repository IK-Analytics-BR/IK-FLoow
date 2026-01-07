-- =====================================================
-- SISTEMA KARDEX DE ESTOQUE COMPLETO
-- Histórico detalhado de todas as movimentações
-- =====================================================

-- Garantir que a tabela estoque_movimentacoes existe com estrutura completa
CREATE TABLE IF NOT EXISTS estoque_movimentacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Produto
    produto_id INT NOT NULL,
    
    -- Tipo de movimentação
    tipo ENUM('entrada', 'saida', 'ajuste_positivo', 'ajuste_negativo', 'reserva', 
              'liberacao_reserva', 'baixa_producao', 'entrada_producao', 
              'venda', 'devolucao', 'transferencia') NOT NULL,
    
    -- Quantidade movimentada (sempre positiva, tipo indica direção)
    quantidade DECIMAL(15,4) NOT NULL,
    
    -- Saldo ANTES e DEPOIS da movimentação (essencial para Kardex)
    estoque_anterior DECIMAL(15,4) NOT NULL DEFAULT 0,
    estoque_posterior DECIMAL(15,4) NOT NULL DEFAULT 0,
    
    -- Origem da movimentação (rastreabilidade)
    origem_tela VARCHAR(100) COMMENT 'Nome da tela/módulo que originou',
    origem_rota VARCHAR(200) COMMENT 'Rota/endpoint que originou',
    
    -- Referência ao documento
    referencia_tipo VARCHAR(50) COMMENT 'orcamento, op, venda, compra, ajuste, pdv, nfe, etc',
    referencia_id INT COMMENT 'ID do documento',
    referencia_codigo VARCHAR(100) COMMENT 'Código legível (ex: ORC-0049, OP-123)',
    
    -- Custo no momento
    custo_unitario DECIMAL(15,4),
    valor_total DECIMAL(15,4),
    
    -- Localização
    local_id INT DEFAULT 1,
    local_nome VARCHAR(100),
    
    -- Observações detalhadas
    observacao TEXT,
    
    -- Dados do usuário
    usuario_id INT,
    usuario_nome VARCHAR(100),
    ip_address VARCHAR(45),
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Índices para consultas rápidas
    INDEX idx_produto (produto_id),
    INDEX idx_tipo (tipo),
    INDEX idx_referencia (referencia_tipo, referencia_id),
    INDEX idx_data (created_at),
    INDEX idx_origem (origem_tela),
    
    FOREIGN KEY (produto_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Adicionar colunas que podem não existir
ALTER TABLE estoque_movimentacoes 
ADD COLUMN IF NOT EXISTS origem_tela VARCHAR(100) COMMENT 'Nome da tela/módulo que originou';

ALTER TABLE estoque_movimentacoes 
ADD COLUMN IF NOT EXISTS origem_rota VARCHAR(200) COMMENT 'Rota/endpoint que originou';

ALTER TABLE estoque_movimentacoes 
ADD COLUMN IF NOT EXISTS referencia_codigo VARCHAR(100) COMMENT 'Código legível';

ALTER TABLE estoque_movimentacoes 
ADD COLUMN IF NOT EXISTS usuario_nome VARCHAR(100);

ALTER TABLE estoque_movimentacoes 
ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45);

ALTER TABLE estoque_movimentacoes 
ADD COLUMN IF NOT EXISTS local_nome VARCHAR(100);

ALTER TABLE estoque_movimentacoes 
ADD COLUMN IF NOT EXISTS valor_total DECIMAL(15,4);

-- View para Kardex por produto
CREATE OR REPLACE VIEW vw_kardex_produto AS
SELECT 
    em.id,
    em.produto_id,
    p.name AS produto_nome,
    p.internal_code AS produto_codigo,
    em.tipo,
    CASE em.tipo
        WHEN 'entrada' THEN 'Entrada'
        WHEN 'saida' THEN 'Saída'
        WHEN 'ajuste_positivo' THEN 'Ajuste (+)'
        WHEN 'ajuste_negativo' THEN 'Ajuste (-)'
        WHEN 'reserva' THEN 'Reserva'
        WHEN 'liberacao_reserva' THEN 'Liberação Reserva'
        WHEN 'baixa_producao' THEN 'Baixa Produção'
        WHEN 'entrada_producao' THEN 'Entrada Produção'
        WHEN 'venda' THEN 'Venda'
        WHEN 'devolucao' THEN 'Devolução'
        WHEN 'transferencia' THEN 'Transferência'
        ELSE em.tipo
    END AS tipo_descricao,
    CASE 
        WHEN em.tipo IN ('entrada', 'ajuste_positivo', 'liberacao_reserva', 'entrada_producao', 'devolucao') 
        THEN em.quantidade 
        ELSE 0 
    END AS entrada,
    CASE 
        WHEN em.tipo IN ('saida', 'ajuste_negativo', 'reserva', 'baixa_producao', 'venda', 'transferencia') 
        THEN em.quantidade 
        ELSE 0 
    END AS saida,
    em.estoque_anterior,
    em.estoque_posterior,
    em.origem_tela,
    em.referencia_tipo,
    em.referencia_id,
    em.referencia_codigo,
    em.observacao,
    em.usuario_nome,
    em.created_at
FROM estoque_movimentacoes em
JOIN products p ON p.id = em.produto_id
ORDER BY em.created_at DESC;

-- View resumo de estoque com movimentações
CREATE OR REPLACE VIEW vw_estoque_resumo AS
SELECT 
    p.id AS produto_id,
    p.name AS produto_nome,
    p.internal_code AS produto_codigo,
    p.barcode,
    COALESCE(p.stock_quantity, 0) AS estoque_atual,
    (SELECT COUNT(*) FROM estoque_movimentacoes em WHERE em.produto_id = p.id) AS total_movimentacoes,
    (SELECT MAX(created_at) FROM estoque_movimentacoes em WHERE em.produto_id = p.id) AS ultima_movimentacao,
    (SELECT SUM(quantidade) FROM estoque_movimentacoes em 
     WHERE em.produto_id = p.id AND em.tipo IN ('entrada', 'ajuste_positivo', 'entrada_producao', 'devolucao')) AS total_entradas,
    (SELECT SUM(quantidade) FROM estoque_movimentacoes em 
     WHERE em.produto_id = p.id AND em.tipo IN ('saida', 'ajuste_negativo', 'baixa_producao', 'venda')) AS total_saidas
FROM products p
WHERE p.active = 1;

SELECT 'Sistema Kardex de Estoque configurado!' AS resultado;
