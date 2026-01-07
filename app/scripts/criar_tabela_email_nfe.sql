-- =====================================================
-- TABELA DE CONFIGURAÇÃO DE EMAIL PARA NF-e
-- =====================================================
-- Cada empresa pode ter sua própria configuração de email
-- para envio automático de NF-e, DANFE, CC-e, etc.

CREATE TABLE IF NOT EXISTS email_config_nfe (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    
    -- Configurações SMTP
    smtp_server VARCHAR(255) NOT NULL COMMENT 'Servidor SMTP (ex: smtp.gmail.com)',
    smtp_port INT NOT NULL DEFAULT 587 COMMENT 'Porta SMTP (587=TLS, 465=SSL)',
    smtp_ssl TINYINT(1) DEFAULT 0 COMMENT '1=SSL, 0=TLS',
    
    -- Credenciais
    email_usuario VARCHAR(255) NOT NULL COMMENT 'Email/usuário para autenticação',
    email_senha VARCHAR(255) NOT NULL COMMENT 'Senha ou App Password',
    email_remetente VARCHAR(255) NOT NULL COMMENT 'Email que aparece como remetente',
    nome_remetente VARCHAR(255) COMMENT 'Nome que aparece como remetente',
    
    -- Configurações de envio
    enviar_nfe_autorizada TINYINT(1) DEFAULT 1 COMMENT 'Enviar email ao autorizar NF-e',
    enviar_nfe_cancelada TINYINT(1) DEFAULT 1 COMMENT 'Enviar email ao cancelar NF-e',
    enviar_cce TINYINT(1) DEFAULT 1 COMMENT 'Enviar email ao emitir CC-e',
    
    -- Anexos
    anexar_xml TINYINT(1) DEFAULT 1 COMMENT 'Anexar XML da NF-e',
    anexar_danfe TINYINT(1) DEFAULT 1 COMMENT 'Anexar DANFE em PDF',
    
    -- Email de cópia
    email_copia VARCHAR(255) COMMENT 'Email para cópia (CC)',
    email_copia_oculta VARCHAR(255) COMMENT 'Email para cópia oculta (BCC)',
    
    -- Assuntos personalizados
    assunto_nfe_autorizada VARCHAR(255) DEFAULT 'NF-e Autorizada - {numero}/{serie}',
    assunto_nfe_cancelada VARCHAR(255) DEFAULT 'NF-e Cancelada - {numero}/{serie}',
    assunto_cce VARCHAR(255) DEFAULT 'Carta de Correção - NF-e {numero}/{serie}',
    
    -- Mensagem personalizada (corpo do email)
    mensagem_padrao TEXT COMMENT 'Mensagem padrão do corpo do email',
    
    -- Status
    ativo TINYINT(1) DEFAULT 1,
    
    -- Auditoria
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE KEY uk_empresa (empresa_id),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    
    INDEX idx_ativo (ativo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABELA DE LOG DE ENVIO DE EMAILS
-- =====================================================
CREATE TABLE IF NOT EXISTS email_log_nfe (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    
    -- Referência
    tipo_documento ENUM('nfe', 'cce', 'cancelamento', 'inutilizacao') NOT NULL,
    chave_nfe VARCHAR(44),
    numero_nfe INT,
    serie_nfe INT,
    
    -- Destinatário
    email_destinatario VARCHAR(255) NOT NULL,
    nome_destinatario VARCHAR(255),
    
    -- Status
    status ENUM('enviado', 'erro', 'pendente') DEFAULT 'pendente',
    mensagem_erro TEXT,
    
    -- Timestamps
    data_envio DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_empresa (empresa_id),
    INDEX idx_chave (chave_nfe),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- INSERIR CONFIGURAÇÃO DE EXEMPLO (COMENTADO)
-- =====================================================
-- INSERT INTO email_config_nfe (
--     empresa_id, smtp_server, smtp_port, smtp_ssl,
--     email_usuario, email_senha, email_remetente, nome_remetente,
--     enviar_nfe_autorizada, enviar_nfe_cancelada, enviar_cce,
--     anexar_xml, anexar_danfe
-- ) VALUES (
--     9, 'smtp.gmail.com', 587, 0,
--     'seu_email@gmail.com', 'sua_app_password', 'nfe@suaempresa.com.br', 'IK Analytics - NF-e',
--     1, 1, 1,
--     1, 1
-- );
