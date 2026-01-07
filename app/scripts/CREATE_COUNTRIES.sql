-- =====================================================
-- CRIAR TABELA DE PAÍSES PADRÃO DO SISTEMA
-- =====================================================

USE supply_chain_system;

CREATE TABLE IF NOT EXISTS countries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(3) NOT NULL UNIQUE,          -- Código ISO (ex.: BR, PY, AR, US)
    name VARCHAR(100) NOT NULL,               -- Nome do país (ex.: Brasil, Paraguai)
    tax_id_label VARCHAR(50) NOT NULL,        -- Rótulo do documento fiscal principal (CNPJ, RUC, EIN, CUIT, etc.)
    zip_label VARCHAR(50) NOT NULL,           -- Rótulo do campo de CEP/Código Postal (CEP, ZIP Code, etc.)
    default_currency_code VARCHAR(3) NOT NULL,-- Moeda funcional padrão (BRL, PYG, ARS, USD, etc.)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Inserir países base (não duplica se já existir)
INSERT INTO countries (code, name, tax_id_label, zip_label, default_currency_code)
VALUES
    ('BR', 'Brasil', 'CNPJ', 'CEP', 'BRL'),
    ('PY', 'Paraguai', 'RUC', 'Código Postal', 'PYG'),
    ('AR', 'Argentina', 'CUIT / CUIL', 'Código Postal', 'ARS'),
    ('US', 'Estados Unidos', 'EIN (Federal Tax ID)', 'ZIP Code', 'USD'),
    ('CL', 'Chile', 'RUT', 'Código Postal', 'CLP'),
    ('MX', 'México', 'RFC', 'Código Postal', 'MXN'),
    ('CA', 'Canadá', 'Business Number', 'Postal Code', 'CAD'),
    ('DE', 'Alemanha', 'USt-IdNr.', 'Postleitzahl', 'EUR'),
    ('PT', 'Portugal', 'NIF', 'Código Postal', 'EUR')
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    tax_id_label = VALUES(tax_id_label),
    zip_label = VALUES(zip_label),
    default_currency_code = VALUES(default_currency_code);
