-- Questionário de Visita – Indústria de Salgados Congelados
-- Tabela para armazenar respostas estruturadas do questionário

CREATE TABLE IF NOT EXISTS customer_visit_questionnaires (
    id INT AUTO_INCREMENT PRIMARY KEY,

    empresa_id INT NULL,
    cliente_id INT NULL,
    orcamento_id INT NULL,

    cliente_nome VARCHAR(255) NOT NULL,
    cliente_email VARCHAR(255) NULL,
    cliente_cnpj VARCHAR(32) NULL,
    cliente_telefone VARCHAR(64) NULL,
    contato_nome VARCHAR(255) NULL,

    segmento_principal VARCHAR(255) NULL,

    -- Todas as respostas em formato estruturado (JSON)
    respostas_json JSON NOT NULL,

    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,

    enviado_email TINYINT(1) NOT NULL DEFAULT 0,
    enviado_email_em DATETIME NULL,

    INDEX idx_cliente (cliente_id),
    INDEX idx_orcamento (orcamento_id),
    INDEX idx_data (criado_em)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
