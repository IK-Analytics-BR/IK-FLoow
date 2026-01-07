-- Script para criar a tabela de técnicos
-- Autor: Sistema de Gestão de Suprimentos
-- Data: 2025-09-08

-- Tabela de Técnicos
CREATE TABLE IF NOT EXISTS technicians (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    registration_number VARCHAR(20) NOT NULL,
    specialty VARCHAR(50),
    phone VARCHAR(20),
    email VARCHAR(100),
    document_number VARCHAR(20),
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(10),
    notes TEXT,
    status ENUM('active', 'inactive', 'on_leave') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE KEY (registration_number)
);

-- Inserir um técnico de exemplo
INSERT INTO technicians (name, registration_number, specialty, phone, email, document_number, address, city, state, zip_code, notes, status, active)
VALUES ('José Silva', 'TECH-001', 'Manutenção Elétrica', '(11) 98765-4321', 'jose.silva@exemplo.com', '123.456.789-00', 'Rua dos Técnicos, 123', 'São Paulo', 'SP', '01234-567', 'Especialista em manutenção de equipamentos industriais', 'active', TRUE);
