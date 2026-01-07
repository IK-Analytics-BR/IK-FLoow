-- =====================================================
-- MÓDULO: ORDEM DE PRODUÇÃO INDUSTRIAL
-- Data: 28/10/2025
-- Descrição: Sistema completo de gestão de ordens de produção
--            com templates inteligentes e controle de custos
-- =====================================================

USE supply_chain_system;

-- =====================================================
-- TABELA 1: produto_templates_producao
-- Armazena templates de produção (histórico de como produzir cada produto)
-- =====================================================

CREATE TABLE IF NOT EXISTS produto_templates_producao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    produto_id INT NOT NULL COMMENT 'Produto que será produzido',
    versao INT NOT NULL DEFAULT 1 COMMENT 'Versão do template (v1, v2, v3...)',
    nome_template VARCHAR(200) NOT NULL COMMENT 'Nome descritivo do template',
    custo_total_base DECIMAL(15,2) DEFAULT 0 COMMENT 'Custo total na época da criação',
    tempo_producao_horas DECIMAL(10,2) COMMENT 'Tempo estimado de produção em horas',
    ativo TINYINT(1) DEFAULT 1 COMMENT '1 = Template ativo (só 1 por produto)',
    observacoes TEXT COMMENT 'Observações sobre o template',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT COMMENT 'ID do usuário que criou',
    
    -- Foreign Keys
    CONSTRAINT fk_template_produto 
        FOREIGN KEY (produto_id) 
        REFERENCES products(id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE,
    
    -- Indexes
    INDEX idx_produto (produto_id),
    INDEX idx_ativo (ativo),
    INDEX idx_versao (versao),
    
    -- Constraint: Apenas 1 template ativo por produto
    UNIQUE KEY uq_produto_ativo (produto_id, ativo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Templates de produção por produto';


-- =====================================================
-- TABELA 2: produto_template_itens
-- Itens que compõem cada template (insumos, serviços, consumo)
-- =====================================================

CREATE TABLE IF NOT EXISTS produto_template_itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_id INT NOT NULL COMMENT 'ID do template',
    tipo_item ENUM('servico', 'materia_prima', 'consumo_interno') NOT NULL COMMENT 'Tipo do item',
    produto_id INT NOT NULL COMMENT 'ID do produto/serviço',
    descricao VARCHAR(255) COMMENT 'Descrição do item (snapshot)',
    quantidade DECIMAL(15,4) NOT NULL COMMENT 'Quantidade necessária',
    unidade_medida VARCHAR(20) COMMENT 'Unidade de medida',
    custo_unitario_base DECIMAL(15,8) COMMENT 'Custo unitário na época do template',
    custo_total_base DECIMAL(15,2) COMMENT 'Custo total do item (qtd × custo unit)',
    observacoes TEXT COMMENT 'Observações sobre o item',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_template_item_template 
        FOREIGN KEY (template_id) 
        REFERENCES produto_templates_producao(id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    
    CONSTRAINT fk_template_item_produto 
        FOREIGN KEY (produto_id) 
        REFERENCES products(id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE,
    
    -- Indexes
    INDEX idx_template (template_id),
    INDEX idx_tipo_item (tipo_item),
    INDEX idx_produto (produto_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Itens dos templates de produção';


-- =====================================================
-- TABELA 3: ordens_producao
-- Cabeçalho das ordens de produção
-- =====================================================

CREATE TABLE IF NOT EXISTS ordens_producao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_op VARCHAR(50) NOT NULL UNIQUE COMMENT 'Número da OP (ex: OP-2025-0001)',
    empresa_id INT NOT NULL COMMENT 'Empresa que está produzindo',
    cliente_id INT NOT NULL COMMENT 'Cliente que solicitou',
    produto_id INT NOT NULL COMMENT 'Produto a ser produzido',
    quantidade DECIMAL(15,4) NOT NULL COMMENT 'Quantidade a produzir',
    
    -- Template usado
    template_usado_id INT COMMENT 'Template usado como base (se houver)',
    usou_template TINYINT(1) DEFAULT 0 COMMENT '1 = Usou template, 0 = Manual',
    
    -- Custos
    custo_total_template DECIMAL(15,2) DEFAULT 0 COMMENT 'Custo do template (histórico)',
    custo_total_atual DECIMAL(15,2) DEFAULT 0 COMMENT 'Custo real calculado',
    variacao_custo_percentual DECIMAL(10,2) DEFAULT 0 COMMENT 'Variação % entre template e atual',
    
    -- Datas
    data_solicitacao DATE NOT NULL COMMENT 'Data que o cliente solicitou',
    data_prevista DATE COMMENT 'Data prevista de conclusão',
    data_inicio_producao DATE COMMENT 'Data que iniciou a produção',
    data_conclusao DATE COMMENT 'Data que foi concluída',
    
    -- Status
    status ENUM('pendente', 'em_producao', 'concluida', 'cancelada') NOT NULL DEFAULT 'pendente',
    
    -- Observações
    observacoes TEXT COMMENT 'Observações gerais da OP',
    motivo_cancelamento TEXT COMMENT 'Motivo do cancelamento (se cancelada)',
    
    -- Auditoria
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT COMMENT 'ID do usuário que criou',
    updated_by INT COMMENT 'ID do último usuário que atualizou',
    
    -- Foreign Keys
    CONSTRAINT fk_op_empresa 
        FOREIGN KEY (empresa_id) 
        REFERENCES empresas(id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE,
    
    CONSTRAINT fk_op_cliente 
        FOREIGN KEY (cliente_id) 
        REFERENCES customers(id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE,
    
    CONSTRAINT fk_op_produto 
        FOREIGN KEY (produto_id) 
        REFERENCES products(id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE,
    
    CONSTRAINT fk_op_template 
        FOREIGN KEY (template_usado_id) 
        REFERENCES produto_templates_producao(id) 
        ON DELETE SET NULL 
        ON UPDATE CASCADE,
    
    -- Indexes
    INDEX idx_numero_op (numero_op),
    INDEX idx_empresa (empresa_id),
    INDEX idx_cliente (cliente_id),
    INDEX idx_produto (produto_id),
    INDEX idx_status (status),
    INDEX idx_data_solicitacao (data_solicitacao),
    INDEX idx_data_prevista (data_prevista)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Ordens de produção';


-- =====================================================
-- TABELA 4: ordem_producao_itens
-- Itens de cada ordem de produção (insumos, serviços, consumo)
-- =====================================================

CREATE TABLE IF NOT EXISTS ordem_producao_itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ordem_producao_id INT NOT NULL COMMENT 'ID da ordem de produção',
    tipo_item ENUM('servico', 'materia_prima', 'consumo_interno') NOT NULL COMMENT 'Tipo do item',
    produto_id INT NOT NULL COMMENT 'ID do produto/serviço',
    descricao VARCHAR(255) COMMENT 'Descrição do item (snapshot)',
    quantidade DECIMAL(15,4) NOT NULL COMMENT 'Quantidade necessária',
    unidade_medida VARCHAR(20) COMMENT 'Unidade de medida',
    
    -- Custos (histórico vs atual)
    custo_unitario_template DECIMAL(15,8) COMMENT 'Custo unitário do template (histórico)',
    custo_unitario_atual DECIMAL(15,8) NOT NULL COMMENT 'Custo unitário real na data da OP',
    variacao_custo_percentual DECIMAL(10,2) DEFAULT 0 COMMENT 'Variação % do custo',
    
    custo_total DECIMAL(15,2) NOT NULL COMMENT 'Custo total do item (qtd × custo atual)',
    
    -- Controle
    veio_template TINYINT(1) DEFAULT 0 COMMENT '1 = Veio do template, 0 = Adicionado manual',
    observacoes TEXT COMMENT 'Observações sobre o item',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_op_item_op 
        FOREIGN KEY (ordem_producao_id) 
        REFERENCES ordens_producao(id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    
    CONSTRAINT fk_op_item_produto 
        FOREIGN KEY (produto_id) 
        REFERENCES products(id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE,
    
    -- Indexes
    INDEX idx_ordem_producao (ordem_producao_id),
    INDEX idx_tipo_item (tipo_item),
    INDEX idx_produto (produto_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Itens das ordens de produção';


-- =====================================================
-- VIEWS ÚTEIS
-- =====================================================

-- View: Resumo de Ordens de Produção
CREATE OR REPLACE VIEW vw_ordens_producao_resumo AS
SELECT 
    op.id,
    op.numero_op,
    e.nome_fantasia as empresa_nome,
    c.name as cliente_nome,
    p.name as produto_nome,
    op.quantidade,
    op.status,
    op.data_solicitacao,
    op.data_prevista,
    op.data_conclusao,
    op.custo_total_atual,
    op.usou_template,
    CASE 
        WHEN op.usou_template = 1 THEN CONCAT('v', t.versao)
        ELSE 'Manual'
    END as template_info,
    op.variacao_custo_percentual,
    op.created_at
FROM ordens_producao op
INNER JOIN empresas e ON op.empresa_id = e.id
INNER JOIN customers c ON op.cliente_id = c.id
INNER JOIN products p ON op.produto_id = p.id
LEFT JOIN produto_templates_producao t ON op.template_usado_id = t.id
ORDER BY op.created_at DESC;


-- View: Itens por Ordem de Produção
CREATE OR REPLACE VIEW vw_ordem_producao_itens_detalhado AS
SELECT 
    opi.id,
    opi.ordem_producao_id,
    op.numero_op,
    opi.tipo_item,
    p.name as produto_nome,
    opi.descricao,
    opi.quantidade,
    opi.unidade_medida,
    opi.custo_unitario_template,
    opi.custo_unitario_atual,
    opi.variacao_custo_percentual,
    opi.custo_total,
    opi.veio_template,
    CASE 
        WHEN opi.tipo_item = 'servico' THEN '🔧 Serviço'
        WHEN opi.tipo_item = 'materia_prima' THEN '📦 Matéria Prima'
        WHEN opi.tipo_item = 'consumo_interno' THEN '🧰 Consumo Interno'
    END as tipo_item_label
FROM ordem_producao_itens opi
INNER JOIN ordens_producao op ON opi.ordem_producao_id = op.id
INNER JOIN products p ON opi.produto_id = p.id
ORDER BY opi.ordem_producao_id, opi.tipo_item, p.name;


-- View: Templates Ativos por Produto
CREATE OR REPLACE VIEW vw_templates_ativos AS
SELECT 
    t.id,
    t.produto_id,
    p.name as produto_nome,
    t.versao,
    t.nome_template,
    t.custo_total_base,
    t.tempo_producao_horas,
    COUNT(ti.id) as total_itens,
    t.created_at,
    t.updated_at
FROM produto_templates_producao t
INNER JOIN products p ON t.produto_id = p.id
LEFT JOIN produto_template_itens ti ON t.id = ti.template_id
WHERE t.ativo = 1
GROUP BY t.id
ORDER BY p.name, t.versao DESC;


-- =====================================================
-- DADOS DE EXEMPLO
-- =====================================================

-- Exemplo 1: Template para "Máquina XYZ"
INSERT INTO produto_templates_producao (produto_id, versao, nome_template, custo_total_base, tempo_producao_horas, ativo, observacoes)
VALUES 
(1, 1, 'Template Padrão - Máquina XYZ v1', 640.00, 16.0, 1, 'Template inicial criado em Jan/2025');

-- Itens do template (assumindo IDs de produtos existentes)
INSERT INTO produto_template_itens (template_id, tipo_item, produto_id, descricao, quantidade, unidade_medida, custo_unitario_base, custo_total_base)
VALUES 
-- Serviços (Mão de Obra)
(1, 'servico', 2, 'Montagem Mecânica', 8.00, 'hora', 50.00, 400.00),
(1, 'servico', 3, 'Soldagem', 4.00, 'hora', 60.00, 240.00),

-- Matéria Prima
(1, 'materia_prima', 4, 'Aço Inox 304', 10.00, 'kg', 18.00, 180.00),
(1, 'materia_prima', 5, 'Parafusos M8', 50.00, 'un', 0.50, 25.00),

-- Consumo Interno
(1, 'consumo_interno', 6, 'Lixa Grão 80', 5.00, 'un', 2.00, 10.00);


-- Exemplo 2: Ordem de Produção usando o template
INSERT INTO ordens_producao (
    numero_op, empresa_id, cliente_id, produto_id, quantidade,
    template_usado_id, usou_template,
    custo_total_template, custo_total_atual, variacao_custo_percentual,
    data_solicitacao, data_prevista, status
)
VALUES (
    'OP-2025-0001', 1, 1, 1, 5.0,
    1, 1,
    640.00, 700.00, 9.38,
    CURDATE(), DATE_ADD(CURDATE(), INTERVAL 15 DAY), 'pendente'
);


-- =====================================================
-- TRIGGERS ÚTEIS
-- =====================================================

-- Trigger: Gerar número da OP automaticamente
DELIMITER //
CREATE TRIGGER trg_gerar_numero_op
BEFORE INSERT ON ordens_producao
FOR EACH ROW
BEGIN
    DECLARE ultimo_numero INT;
    DECLARE ano_atual VARCHAR(4);
    
    IF NEW.numero_op IS NULL OR NEW.numero_op = '' THEN
        SET ano_atual = YEAR(CURDATE());
        
        SELECT COALESCE(MAX(CAST(SUBSTRING(numero_op, -4) AS UNSIGNED)), 0) + 1
        INTO ultimo_numero
        FROM ordens_producao
        WHERE numero_op LIKE CONCAT('OP-', ano_atual, '-%');
        
        SET NEW.numero_op = CONCAT('OP-', ano_atual, '-', LPAD(ultimo_numero, 4, '0'));
    END IF;
END//
DELIMITER ;


-- Trigger: Calcular variação de custo automaticamente
DELIMITER //
CREATE TRIGGER trg_calcular_variacao_custo
BEFORE UPDATE ON ordens_producao
FOR EACH ROW
BEGIN
    IF NEW.custo_total_template > 0 THEN
        SET NEW.variacao_custo_percentual = 
            ((NEW.custo_total_atual - NEW.custo_total_template) / NEW.custo_total_template) * 100;
    END IF;
END//
DELIMITER ;


-- =====================================================
-- CONSULTAS ÚTEIS PARA TESTES
-- =====================================================

-- Ver todos os templates ativos
SELECT * FROM vw_templates_ativos;

-- Ver todas as OPs
SELECT * FROM vw_ordens_producao_resumo;

-- Ver itens de uma OP específica
SELECT * FROM vw_ordem_producao_itens_detalhado WHERE ordem_producao_id = 1;

-- Buscar produtos que TÊM template
SELECT DISTINCT
    p.id,
    p.name,
    t.versao,
    t.custo_total_base,
    t.tempo_producao_horas
FROM products p
INNER JOIN produto_templates_producao t ON p.id = t.produto_id
WHERE t.ativo = 1
  AND p.active = TRUE
  AND p.category IN (SELECT id FROM product_categories WHERE categoria_fiscal = 'produto')
ORDER BY p.name;

-- Buscar produtos SEM template (para primeira produção)
SELECT 
    p.id,
    p.name
FROM products p
LEFT JOIN produto_templates_producao t ON p.id = t.produto_id AND t.ativo = 1
WHERE t.id IS NULL
  AND p.active = TRUE
  AND p.category IN (SELECT id FROM product_categories WHERE categoria_fiscal = 'produto')
ORDER BY p.name;


-- =====================================================
-- FIM DO SCRIPT
-- =====================================================
