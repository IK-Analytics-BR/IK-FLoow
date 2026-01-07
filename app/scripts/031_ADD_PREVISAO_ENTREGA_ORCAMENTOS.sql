-- =====================================================
-- SCRIPT 031: ADICIONAR CAMPOS DE PREVISÃO EM ORÇAMENTOS
-- Data: 2025-12-26
-- Descrição: Adiciona campos para previsão de produção e entrega
-- =====================================================

-- 1. Adicionar campos na tabela orcamentos
ALTER TABLE orcamentos 
ADD COLUMN IF NOT EXISTS data_previsao_producao DATE DEFAULT NULL 
    COMMENT 'Data prevista para conclusão da produção (calculada ou manual)',
ADD COLUMN IF NOT EXISTS data_previsao_entrega DATE DEFAULT NULL 
    COMMENT 'Data prevista para entrega ao cliente (produção + transporte)',
ADD COLUMN IF NOT EXISTS previsao_manual TINYINT(1) DEFAULT 0 
    COMMENT '1 = previsão definida manualmente, 0 = calculada automaticamente',
ADD COLUMN IF NOT EXISTS dias_transporte INT DEFAULT 0 
    COMMENT 'Dias estimados para transporte até o cliente';

-- 2. Criar tabela para armazenar tempo médio de produção por produto
CREATE TABLE IF NOT EXISTS produtos_tempo_producao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    produto_id INT NOT NULL,
    etapa_id INT DEFAULT NULL COMMENT 'Se NULL = tempo total do produto',
    tempo_medio_minutos INT DEFAULT 0 COMMENT 'Média de tempo em minutos',
    tempo_minimo_minutos INT DEFAULT 0 COMMENT 'Menor tempo registrado',
    tempo_maximo_minutos INT DEFAULT 0 COMMENT 'Maior tempo registrado',
    quantidade_amostras INT DEFAULT 0 COMMENT 'Quantas produções usadas no cálculo',
    ultima_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_produto_etapa (produto_id, etapa_id),
    FOREIGN KEY (produto_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (etapa_id) REFERENCES producao_etapas(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Histórico de tempo de produção por produto para cálculo de previsões';

-- 3. Criar tabela para previsão por item do orçamento (futuro)
CREATE TABLE IF NOT EXISTS orcamento_itens_previsao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    orcamento_id INT NOT NULL,
    grupo_id INT DEFAULT NULL COMMENT 'ID do grupo no orçamento',
    produto_id INT NOT NULL,
    quantidade INT NOT NULL DEFAULT 1,
    tempo_estimado_minutos INT DEFAULT 0 COMMENT 'Tempo estimado para produzir este item',
    posicao_fila INT DEFAULT 0 COMMENT 'Posição estimada na fila de produção',
    tempo_fila_minutos INT DEFAULT 0 COMMENT 'Tempo estimado de espera na fila',
    data_previsao_inicio DATE DEFAULT NULL COMMENT 'Quando deve iniciar produção',
    data_previsao_conclusao DATE DEFAULT NULL COMMENT 'Quando deve concluir produção',
    observacao VARCHAR(255) DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (orcamento_id) REFERENCES orcamentos(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Previsão de produção por item do orçamento';

-- 4. Índices para performance
CREATE INDEX IF NOT EXISTS idx_orcamentos_previsao_producao ON orcamentos(data_previsao_producao);
CREATE INDEX IF NOT EXISTS idx_orcamentos_previsao_entrega ON orcamentos(data_previsao_entrega);
CREATE INDEX IF NOT EXISTS idx_produtos_tempo_produto ON produtos_tempo_producao(produto_id);

-- 5. Verificação
SELECT 'Script 031 executado com sucesso!' AS status;

-- Mostrar estrutura atualizada
DESCRIBE orcamentos;
