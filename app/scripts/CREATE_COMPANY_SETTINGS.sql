-- =====================================================
-- CRIAR TABELA DE CONFIGURAÇÕES DA EMPRESA
-- =====================================================

USE supply_chain_system;

-- Criar tabela de configurações da empresa
CREATE TABLE IF NOT EXISTS company_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL DEFAULT 'Minha Empresa',
    legal_name VARCHAR(255),
    cnpj VARCHAR(18),
    ie VARCHAR(20),
    phone VARCHAR(20),
    email VARCHAR(100),
    website VARCHAR(100),
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    country VARCHAR(50) DEFAULT 'Brasil',
    logo_path VARCHAR(255),
    logo_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Inserir registro padrão se não existir
INSERT INTO company_settings (company_name, legal_name)
SELECT 'Minha Empresa', 'Minha Empresa LTDA'
WHERE NOT EXISTS (SELECT 1 FROM company_settings LIMIT 1);

-- Criar pasta para logos (será criada pelo Python)
-- app/static/uploads/logos/

SELECT '✅ Tabela company_settings criada com sucesso!' AS resultado;
