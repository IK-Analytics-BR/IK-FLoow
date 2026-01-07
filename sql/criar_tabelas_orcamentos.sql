-- ============================================================
-- SCRIPT SQL: Criar tabelas do módulo ORÇAMENTOS
-- Data: 16/12/2025
-- Executar na AWS: mysql -u USER -p supply_chain_system < criar_tabelas_orcamentos.sql
-- ============================================================

-- 1. TABELA PRINCIPAL DE ORÇAMENTOS
-- ============================================================
CREATE TABLE IF NOT EXISTS orcamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero VARCHAR(20) UNIQUE,
    
    -- Dados principais (Aba Dados)
    cliente_id INT,
    vendedor_id INT,
    vendedor2_id INT,
    contato VARCHAR(100),
    tipo_pedido VARCHAR(50),
    canal_relacionamento VARCHAR(50),
    empresa_id INT,
    data_emissao DATE DEFAULT (CURRENT_DATE),
    data_validade DATE,
    condicao_pagamento VARCHAR(100),
    forma_pagamento_id INT,
    prazo_entrega VARCHAR(100),
    
    -- Dados de transporte (Aba Transporte)
    frete_por_conta ENUM('emitente', 'destinatario', 'terceiros', 'sem_frete') DEFAULT 'emitente',
    obs_frete TEXT,
    perfil_transporte VARCHAR(50),
    transportadora_id INT,
    especie VARCHAR(50),
    volumes_quantidade INT,
    peso_bruto DECIMAL(10,3),
    peso_liquido DECIMAL(10,3),
    veiculo_placa VARCHAR(10),
    veiculo_uf VARCHAR(2),
    veiculo_rntc VARCHAR(20),
    
    -- Informações adicionais
    referencia_cliente VARCHAR(100),
    obs_validade TEXT,
    obs_entrega TEXT,
    obs_embalagem TEXT,
    obs_garantia TEXT,
    obs_certificado TEXT,
    icms_incluso TINYINT(1) DEFAULT 1,
    ipi_incluso TINYINT(1) DEFAULT 0,
    
    -- Valores calculados
    valor_produtos DECIMAL(15,2) DEFAULT 0,
    percentual_desconto DECIMAL(5,2) DEFAULT 0,
    valor_desconto DECIMAL(15,2) DEFAULT 0,
    valor_frete DECIMAL(15,2) DEFAULT 0,
    valor_total DECIMAL(15,2) DEFAULT 0,
    
    -- Observações (Aba Outros)
    observacoes TEXT,
    observacoes_internas TEXT,
    
    -- Comissão
    comissao_vendedor1_percent DECIMAL(5,2) DEFAULT 0,
    comissao_vendedor1_valor DECIMAL(15,2) DEFAULT 0,
    comissao_vendedor2_percent DECIMAL(5,2) DEFAULT 0,
    comissao_vendedor2_valor DECIMAL(15,2) DEFAULT 0,
    
    -- Status e controle
    status ENUM('rascunho', 'enviado', 'aprovado', 'reprovado', 'convertido', 'cancelado') DEFAULT 'rascunho',
    data_aprovacao DATETIME,
    data_reprovacao DATETIME,
    pedido_id INT,
    
    -- Auditoria
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (cliente_id) REFERENCES customers(id) ON DELETE SET NULL,
    FOREIGN KEY (vendedor_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (vendedor2_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE SET NULL,
    FOREIGN KEY (transportadora_id) REFERENCES transportadoras(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    
    INDEX idx_orcamentos_cliente (cliente_id),
    INDEX idx_orcamentos_vendedor (vendedor_id),
    INDEX idx_orcamentos_status (status),
    INDEX idx_orcamentos_data (data_emissao),
    INDEX idx_orcamentos_empresa (empresa_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 2. TABELA DE ITENS DO ORÇAMENTO
-- ============================================================
CREATE TABLE IF NOT EXISTS orcamento_itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    orcamento_id INT NOT NULL,
    produto_id INT,
    sequencia INT DEFAULT 1,
    
    -- Dados do produto
    quantidade DECIMAL(15,4) DEFAULT 1,
    unidade VARCHAR(10) DEFAULT 'UN',
    
    -- Preços
    preco_tabela DECIMAL(15,4),
    preco_unitario DECIMAL(15,4),
    percentual_desconto DECIMAL(5,2) DEFAULT 0,
    valor_desconto DECIMAL(15,2) DEFAULT 0,
    valor_total DECIMAL(15,2) DEFAULT 0,
    
    -- Dimensões (para correias/produtos especiais)
    largura DECIMAL(10,2),
    comprimento DECIMAL(10,2),
    espessura DECIMAL(10,2),
    tipo_correia VARCHAR(50),
    material VARCHAR(100),
    
    -- Observações
    observacao TEXT,
    
    -- Auditoria
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (orcamento_id) REFERENCES orcamentos(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES products(id) ON DELETE SET NULL,
    
    INDEX idx_orcamento_itens_orcamento (orcamento_id),
    INDEX idx_orcamento_itens_produto (produto_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 3. TABELA DE DUPLICATAS/PARCELAS
-- ============================================================
CREATE TABLE IF NOT EXISTS orcamento_duplicatas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    orcamento_id INT NOT NULL,
    numero INT NOT NULL,
    vencimento DATE,
    valor DECIMAL(15,2),
    forma_pagamento VARCHAR(50),
    forma_pagamento_id INT,
    status ENUM('pendente', 'pago', 'cancelado') DEFAULT 'pendente',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (orcamento_id) REFERENCES orcamentos(id) ON DELETE CASCADE,
    
    INDEX idx_orcamento_duplicatas_orcamento (orcamento_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 4. TABELA DE HISTÓRICO DO ORÇAMENTO
-- ============================================================
CREATE TABLE IF NOT EXISTS orcamento_historico (
    id INT AUTO_INCREMENT PRIMARY KEY,
    orcamento_id INT NOT NULL,
    acao VARCHAR(50) NOT NULL,
    descricao TEXT,
    dados_anteriores JSON,
    dados_novos JSON,
    usuario_id INT,
    usuario_nome VARCHAR(100),
    ip_address VARCHAR(45),
    data_evento DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (orcamento_id) REFERENCES orcamentos(id) ON DELETE CASCADE,
    
    INDEX idx_orcamento_historico_orcamento (orcamento_id),
    INDEX idx_orcamento_historico_data (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 5. TRIGGER PARA GERAR NÚMERO AUTOMÁTICO DO ORÇAMENTO
-- ============================================================
DELIMITER //

DROP TRIGGER IF EXISTS gerar_numero_orcamento//

CREATE TRIGGER gerar_numero_orcamento
BEFORE INSERT ON orcamentos
FOR EACH ROW
BEGIN
    DECLARE proximo_numero INT;
    DECLARE ano_atual CHAR(4);
    
    SET ano_atual = YEAR(CURRENT_DATE);
    
    SELECT COALESCE(MAX(
        CAST(SUBSTRING_INDEX(numero, '-', -1) AS UNSIGNED)
    ), 0) + 1
    INTO proximo_numero
    FROM orcamentos
    WHERE numero LIKE CONCAT('ORC-', ano_atual, '-%');
    
    SET NEW.numero = CONCAT('ORC-', ano_atual, '-', LPAD(proximo_numero, 5, '0'));
END//

DELIMITER ;


-- ============================================================
-- VERIFICAÇÃO
-- ============================================================
SELECT 'Tabelas criadas com sucesso!' AS status;

SHOW TABLES LIKE 'orcamento%';

SELECT 
    TABLE_NAME,
    TABLE_ROWS
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = DATABASE() 
AND TABLE_NAME LIKE 'orcamento%';
