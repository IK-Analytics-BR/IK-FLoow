-- Tabela de pacotes comerciais dos produtos (planejamento e vendas)

CREATE TABLE IF NOT EXISTS produto_pacotes (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    produto_id INT NOT NULL,
    descricao VARCHAR(255) NOT NULL,
    unidade_comercial VARCHAR(50) NOT NULL,
    unidades_por_pacote DECIMAL(18,6) NOT NULL DEFAULT 1.000000,
    peso_pacote_kg DECIMAL(18,6) DEFAULT NULL,
    preco_pacote DECIMAL(18,6) DEFAULT NULL,
    preco_unidade DECIMAL(18,6) DEFAULT NULL,
    custo_unitario_produto DECIMAL(18,6) DEFAULT NULL,
    custo_total_pacote DECIMAL(18,6) DEFAULT NULL,
    margem_unitaria_percent DECIMAL(18,6) DEFAULT NULL,
    margem_pacote_percent DECIMAL(18,6) DEFAULT NULL,
    ativo TINYINT(1) NOT NULL DEFAULT 1,
    padrao_planejamento TINYINT(1) NOT NULL DEFAULT 0,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_produto_pacotes_produto (produto_id),
    CONSTRAINT fk_produto_pacotes_produto FOREIGN KEY (produto_id) REFERENCES products(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
