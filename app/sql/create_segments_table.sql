-- Criar tabela de segmentos
CREATE TABLE IF NOT EXISTS segments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Adicionar coluna de segmento na tabela de clientes
ALTER TABLE customers
ADD COLUMN segment_id INT NULL,
ADD CONSTRAINT fk_customer_segment
    FOREIGN KEY (segment_id)
    REFERENCES segments(id)
    ON DELETE SET NULL;

-- Adicionar coluna de segmento na tabela de fornecedores
ALTER TABLE suppliers
ADD COLUMN segment_id INT NULL,
ADD CONSTRAINT fk_supplier_segment
    FOREIGN KEY (segment_id)
    REFERENCES segments(id)
    ON DELETE SET NULL;

-- Inserir alguns segmentos iniciais
INSERT INTO segments (name, description) VALUES
('Indústria', 'Empresas do setor industrial'),
('Comércio', 'Empresas do setor comercial'),
('Serviços', 'Empresas do setor de serviços'),
('Agronegócio', 'Empresas do setor agrícola'),
('Tecnologia', 'Empresas do setor de tecnologia'),
('Saúde', 'Empresas do setor de saúde'),
('Educação', 'Empresas do setor educacional'),
('Construção', 'Empresas do setor de construção civil'),
('Transporte', 'Empresas do setor de transporte e logística'),
('Alimentação', 'Empresas do setor alimentício');
