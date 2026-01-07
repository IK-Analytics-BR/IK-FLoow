-- Script para criar tabelas do módulo de Usuários e Permissões
-- Autor: Sistema de Gestão de Suprimentos
-- Data: 2025-09-08

-- Tabela de Usuários
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
    last_login TIMESTAMP NULL,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE KEY (username),
    UNIQUE KEY (email),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Tabela de Permissões
CREATE TABLE IF NOT EXISTS permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY (name)
);

-- Tabela de Relação entre Usuários e Permissões
CREATE TABLE IF NOT EXISTS user_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    permission_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY (user_id, permission_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (permission_id) REFERENCES permissions(id)
);

-- Tabela de Logs de Atividades
CREATE TABLE IF NOT EXISTS activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INT,
    details TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Tabela de Sessões
CREATE TABLE IF NOT EXISTS sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_token VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Inserir usuário administrador padrão se não existir
-- Senha: admin123 (apenas para desenvolvimento)
INSERT INTO users (name, username, email, password_hash, salt, role, active)
SELECT 'Administrador', 'admin', 'admin@example.com', 
       '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', -- SHA-256 hash de 'admin' + salt
       '123456789abcdef', 'admin', TRUE
FROM dual
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin');

-- Inserir permissões padrão
INSERT INTO permissions (name, description)
VALUES 
    ('financeiro.visualizar', 'Permite visualizar dados financeiros'),
    ('financeiro.editar', 'Permite editar dados financeiros'),
    ('estoque.visualizar', 'Permite visualizar dados de estoque'),
    ('estoque.editar', 'Permite editar dados de estoque'),
    ('compras.visualizar', 'Permite visualizar pedidos de compra'),
    ('compras.editar', 'Permite editar pedidos de compra'),
    ('compras.aprovar', 'Permite aprovar pedidos de compra'),
    ('relatorios.visualizar', 'Permite visualizar relatórios')
ON DUPLICATE KEY UPDATE description = VALUES(description);

-- Procedimento para registrar atividade
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS log_activity(
    IN p_user_id INT,
    IN p_action VARCHAR(100),
    IN p_entity_type VARCHAR(50),
    IN p_entity_id INT,
    IN p_details TEXT,
    IN p_ip_address VARCHAR(45)
)
BEGIN
    INSERT INTO activity_logs (user_id, action, entity_type, entity_id, details, ip_address)
    VALUES (p_user_id, p_action, p_entity_type, p_entity_id, p_details, p_ip_address);
END //
DELIMITER ;

-- Função para verificar se um usuário tem uma permissão específica
DELIMITER //
CREATE FUNCTION IF NOT EXISTS user_has_permission(
    p_user_id INT,
    p_permission_name VARCHAR(100)
)
RETURNS BOOLEAN
DETERMINISTIC
BEGIN
    DECLARE v_has_permission BOOLEAN;
    DECLARE v_is_admin BOOLEAN;
    
    -- Verificar se o usuário é administrador
    SELECT role = 'admin' INTO v_is_admin
    FROM users
    WHERE id = p_user_id AND active = TRUE;
    
    -- Administradores têm todas as permissões
    IF v_is_admin THEN
        RETURN TRUE;
    END IF;
    
    -- Verificar se o usuário tem a permissão específica
    SELECT COUNT(*) > 0 INTO v_has_permission
    FROM user_permissions up
    JOIN permissions p ON up.permission_id = p.id
    WHERE up.user_id = p_user_id AND p.name = p_permission_name;
    
    RETURN v_has_permission;
END //
DELIMITER ;

-- Trigger para atualizar a data de último login
DELIMITER //
CREATE TRIGGER IF NOT EXISTS update_last_login_after_session_insert
AFTER INSERT ON sessions
FOR EACH ROW
BEGIN
    UPDATE users
    SET last_login = NOW()
    WHERE id = NEW.user_id;
END //
DELIMITER ;
