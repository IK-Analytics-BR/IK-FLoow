-- ============================================
-- TABELA DE CONFIGURAÇÕES DO PDV
-- Data: 2025-10-24
-- Autor: Sistema IK Flow
-- ============================================

CREATE TABLE IF NOT EXISTS pdv_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Identificação
    pdv_name VARCHAR(100) DEFAULT 'PDV Principal' COMMENT 'Nome do PDV',
    pdv_number INT DEFAULT 1 COMMENT 'Número do PDV',
    
    -- Configurações de Estoque
    allow_negative_stock BOOLEAN DEFAULT FALSE COMMENT 'Permitir venda sem estoque',
    check_stock_realtime BOOLEAN DEFAULT TRUE COMMENT 'Verificar estoque em tempo real',
    show_stock_quantity BOOLEAN DEFAULT TRUE COMMENT 'Mostrar quantidade em estoque',
    
    -- Configurações de Quantidade
    ask_quantity BOOLEAN DEFAULT TRUE COMMENT 'Perguntar quantidade antes de adicionar',
    default_quantity DECIMAL(10,3) DEFAULT 1.000 COMMENT 'Quantidade padrão',
    allow_decimal_quantity BOOLEAN DEFAULT TRUE COMMENT 'Permitir quantidade decimal',
    
    -- Configurações de Preço e Desconto
    allow_price_change BOOLEAN DEFAULT FALSE COMMENT 'Permitir alterar preço',
    show_discount_button BOOLEAN DEFAULT TRUE COMMENT 'Mostrar botão de desconto',
    allow_item_discount BOOLEAN DEFAULT TRUE COMMENT 'Permitir desconto por item',
    allow_total_discount BOOLEAN DEFAULT TRUE COMMENT 'Permitir desconto no total',
    max_discount_percent DECIMAL(5,2) DEFAULT 10.00 COMMENT 'Desconto máximo (%)',
    require_manager_approval BOOLEAN DEFAULT FALSE COMMENT 'Exigir aprovação gerente para desconto',
    
    -- Configurações de Cliente
    require_customer BOOLEAN DEFAULT FALSE COMMENT 'Obrigar informar cliente',
    default_customer_id INT NULL COMMENT 'Cliente padrão (A Vista)',
    allow_customer_registration BOOLEAN DEFAULT TRUE COMMENT 'Permitir cadastro rápido',
    
    -- Configurações de Pagamento
    require_payment_confirmation BOOLEAN DEFAULT TRUE COMMENT 'Confirmar forma de pagamento',
    allow_multiple_payments BOOLEAN DEFAULT TRUE COMMENT 'Permitir pagamento misto',
    print_receipt_auto BOOLEAN DEFAULT FALSE COMMENT 'Imprimir cupom automaticamente',
    
    -- Configurações de Interface
    show_product_image BOOLEAN DEFAULT FALSE COMMENT 'Mostrar imagem do produto',
    show_barcode BOOLEAN DEFAULT TRUE COMMENT 'Mostrar código de barras',
    auto_focus_product_field BOOLEAN DEFAULT TRUE COMMENT 'Focar automaticamente no campo produto',
    beep_on_scan BOOLEAN DEFAULT FALSE COMMENT 'Emitir beep ao escanear',
    
    -- Configurações de Atalhos
    enable_f2_customer BOOLEAN DEFAULT TRUE COMMENT 'F2 - Buscar cliente',
    enable_f4_discount BOOLEAN DEFAULT TRUE COMMENT 'F4 - Desconto',
    enable_f5_cancel BOOLEAN DEFAULT TRUE COMMENT 'F5 - Cancelar item',
    enable_f6_search BOOLEAN DEFAULT TRUE COMMENT 'F6 - Buscar produto',
    enable_f9_finish BOOLEAN DEFAULT TRUE COMMENT 'F9 - Finalizar venda',
    
    -- Configurações de Segurança
    require_supervisor_cancel BOOLEAN DEFAULT FALSE COMMENT 'Exigir supervisor para cancelar venda',
    log_all_operations BOOLEAN DEFAULT TRUE COMMENT 'Registrar todas operações',
    
    -- Configurações de Impressão
    printer_name VARCHAR(100) NULL COMMENT 'Nome da impressora',
    paper_width INT DEFAULT 80 COMMENT 'Largura do papel (mm)',
    print_company_logo BOOLEAN DEFAULT TRUE COMMENT 'Imprimir logo da empresa',
    print_customer_copy BOOLEAN DEFAULT FALSE COMMENT 'Imprimir via cliente automaticamente',
    
    -- Metadados
    active BOOLEAN DEFAULT TRUE COMMENT 'Configuração ativa',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by INT NULL COMMENT 'Usuário que atualizou',
    
    -- Chaves estrangeiras
    FOREIGN KEY (default_customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Configurações personalizadas do PDV';

-- ============================================
-- INSERIR CONFIGURAÇÃO PADRÃO
-- ============================================

INSERT INTO pdv_settings (
    pdv_name,
    pdv_number,
    allow_negative_stock,
    check_stock_realtime,
    show_stock_quantity,
    ask_quantity,
    default_quantity,
    allow_decimal_quantity,
    allow_price_change,
    show_discount_button,
    allow_item_discount,
    allow_total_discount,
    max_discount_percent,
    require_manager_approval,
    require_customer,
    allow_customer_registration,
    require_payment_confirmation,
    allow_multiple_payments,
    print_receipt_auto,
    show_product_image,
    show_barcode,
    auto_focus_product_field,
    beep_on_scan,
    enable_f2_customer,
    enable_f4_discount,
    enable_f5_cancel,
    enable_f6_search,
    enable_f9_finish,
    require_supervisor_cancel,
    log_all_operations,
    paper_width,
    print_company_logo,
    print_customer_copy,
    active
)
VALUES (
    'PDV Principal',                -- pdv_name
    1,                              -- pdv_number
    FALSE,                          -- allow_negative_stock
    TRUE,                           -- check_stock_realtime
    TRUE,                           -- show_stock_quantity
    TRUE,                           -- ask_quantity
    1.000,                          -- default_quantity
    TRUE,                           -- allow_decimal_quantity
    FALSE,                          -- allow_price_change
    TRUE,                           -- show_discount_button
    TRUE,                           -- allow_item_discount
    TRUE,                           -- allow_total_discount
    10.00,                          -- max_discount_percent
    FALSE,                          -- require_manager_approval
    FALSE,                          -- require_customer
    TRUE,                           -- allow_customer_registration
    TRUE,                           -- require_payment_confirmation
    TRUE,                           -- allow_multiple_payments
    FALSE,                          -- print_receipt_auto
    FALSE,                          -- show_product_image
    TRUE,                           -- show_barcode
    TRUE,                           -- auto_focus_product_field
    FALSE,                          -- beep_on_scan
    TRUE,                           -- enable_f2_customer
    TRUE,                           -- enable_f4_discount
    TRUE,                           -- enable_f5_cancel
    TRUE,                           -- enable_f6_search
    TRUE,                           -- enable_f9_finish
    FALSE,                          -- require_supervisor_cancel
    TRUE,                           -- log_all_operations
    80,                             -- paper_width
    TRUE,                           -- print_company_logo
    FALSE,                          -- print_customer_copy
    TRUE                            -- active
)
ON DUPLICATE KEY UPDATE
    updated_at = CURRENT_TIMESTAMP;

-- ============================================
-- ÍNDICES PARA PERFORMANCE
-- ============================================

CREATE INDEX idx_pdv_settings_active ON pdv_settings(active);
CREATE INDEX idx_pdv_settings_pdv_number ON pdv_settings(pdv_number);

-- ============================================
-- COMENTÁRIOS ADICIONAIS
-- ============================================

-- Configurações podem ser expandidas conforme necessidade
-- Cada PDV pode ter sua própria configuração
-- Configurações inativas são mantidas para histórico
