# Sistema DNA de Produto - Correias Industriais

## Visão Geral

Sistema inteligente para identificação, matching e reaproveitamento de correias industriais baseado em especificações técnicas (DNA do Produto).

**Problema Atual:**
- Especificações da correia estão no nome/descrição (não estruturadas)
- Não há anexo de Desenho Técnico
- Não há sistema de matching entre produtos similares
- Não há processo para reaproveitar produto em estoque com especificações compatíveis

**Solução:**
- Cadastro estruturado de especificações técnicas (DNA)
- Anexos de arquivos/imagens (Desenho Técnico)
- Algoritmo de matching por DNA
- Fluxo de produção para derivação de produtos

---

## FASE 1: Cadastro Estruturado de Especificações Técnicas

### 1.1 Nova Tabela `produto_especificacoes_tecnicas`

```sql
CREATE TABLE produto_especificacoes_tecnicas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    produto_id INT NOT NULL,
    
    -- DIMENSÕES PRINCIPAIS
    largura_mm DECIMAL(10,2) COMMENT 'Largura em milímetros',
    comprimento_mm DECIMAL(10,2) COMMENT 'Comprimento em milímetros',
    espessura_mm DECIMAL(10,2) COMMENT 'Espessura em milímetros',
    
    -- TIPO E MATERIAL
    tipo_correia VARCHAR(50) COMMENT 'PV, Sincronizada, Transportadora, etc',
    material_base VARCHAR(100) COMMENT 'PVC, PU, Borracha, etc',
    material_revestimento VARCHAR(100) COMMENT 'Revestimento superficial',
    cor VARCHAR(50),
    
    -- CARACTERÍSTICAS TÉCNICAS
    perfil VARCHAR(50) COMMENT 'Perfil: PJ, H, L, XL, etc',
    passo_mm DECIMAL(10,2) COMMENT 'Passo (para sincronizadas)',
    numero_dentes INT COMMENT 'Número de dentes (sincronizadas)',
    dureza_shore DECIMAL(5,2) COMMENT 'Dureza Shore A',
    
    -- LONAS E CAMADAS
    numero_lonas INT COMMENT 'Quantidade de lonas',
    tipo_lona VARCHAR(50) COMMENT 'EP, NN, etc',
    
    -- EMENDAS E ACABAMENTO
    tipo_emenda VARCHAR(50) COMMENT 'Vulcanizada, Mecânica, Sem emenda',
    acabamento_borda VARCHAR(50) COMMENT 'Selada, Cortada, etc',
    
    -- APLICAÇÃO
    aplicacao VARCHAR(200) COMMENT 'Uso: Transporte, Sincronização, etc',
    temperatura_max DECIMAL(5,1) COMMENT 'Temperatura máxima operação °C',
    temperatura_min DECIMAL(5,1) COMMENT 'Temperatura mínima operação °C',
    
    -- NORMAS E CERTIFICAÇÕES
    norma_tecnica VARCHAR(100) COMMENT 'ISO, DIN, etc',
    certificacoes VARCHAR(200),
    
    -- METADADOS
    codigo_dna VARCHAR(100) UNIQUE COMMENT 'Código gerado para matching',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (produto_id) REFERENCES products(id) ON DELETE CASCADE,
    INDEX idx_tipo_correia (tipo_correia),
    INDEX idx_material (material_base),
    INDEX idx_perfil (perfil),
    INDEX idx_codigo_dna (codigo_dna)
);
```

### 1.2 Geração do Código DNA

O código DNA é gerado automaticamente baseado nas especificações principais:

```
DNA = TIPO-MATERIAL-PERFIL-DUREZA-LONAS-EMENDA
Exemplo: SIN-PU-H100-65-2L-VUL
```

**Componentes:**
- `SIN` = Sincronizada, `PV` = PV, `TRA` = Transportadora
- `PU` = Poliuretano, `PVC` = PVC, `BOR` = Borracha
- `H100` = Perfil H 100
- `65` = Dureza Shore 65
- `2L` = 2 Lonas
- `VUL` = Vulcanizada, `MEC` = Mecânica

---

## FASE 2: Anexos e Desenho Técnico

### 2.1 Nova Tabela `produto_anexos`

```sql
CREATE TABLE produto_anexos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    produto_id INT NOT NULL,
    
    tipo_anexo ENUM('desenho_tecnico', 'foto', 'datasheet', 'certificado', 'outro') NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT,
    
    -- ARQUIVO
    nome_arquivo VARCHAR(255) NOT NULL,
    extensao VARCHAR(10) NOT NULL,
    tamanho_bytes BIGINT,
    caminho_arquivo VARCHAR(500) NOT NULL COMMENT 'Caminho no servidor',
    
    -- CONTROLE
    versao INT DEFAULT 1,
    principal TINYINT(1) DEFAULT 0 COMMENT '1 = Anexo principal do tipo',
    ativo TINYINT(1) DEFAULT 1,
    
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (produto_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_produto_tipo (produto_id, tipo_anexo)
);
```

### 2.2 Estrutura de Pastas

```
/uploads/
└── produtos/
    └── {produto_id}/
        ├── desenhos/
        │   ├── desenho_v1.pdf
        │   └── desenho_v2.pdf
        ├── fotos/
        │   ├── foto_principal.jpg
        │   └── foto_detalhe.jpg
        └── datasheets/
            └── ficha_tecnica.pdf
```

---

## FASE 3: Sistema de Matching (DNA Match)

### 3.1 Conceito de Matching

Quando um cliente solicita uma correia, o sistema busca:

1. **Match Exato**: Produto idêntico em estoque
2. **Match Derivável**: Produto com mesmo DNA mas dimensão maior (pode ser cortado)
3. **Match Parcial**: Mesmo tipo/material, dimensões diferentes

### 3.2 Nova Tabela `produto_matching_regras`

```sql
CREATE TABLE produto_matching_regras (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    tipo_correia VARCHAR(50) NOT NULL,
    
    -- CAMPOS QUE DEVEM SER IGUAIS PARA MATCH
    match_material_base TINYINT(1) DEFAULT 1,
    match_material_revestimento TINYINT(1) DEFAULT 1,
    match_perfil TINYINT(1) DEFAULT 1,
    match_dureza TINYINT(1) DEFAULT 1,
    match_lonas TINYINT(1) DEFAULT 1,
    match_tipo_emenda TINYINT(1) DEFAULT 1,
    
    -- CAMPOS QUE PODEM VARIAR (DERIVAÇÃO)
    permite_corte_largura TINYINT(1) DEFAULT 1,
    permite_corte_comprimento TINYINT(1) DEFAULT 1,
    
    -- TOLERÂNCIAS
    tolerancia_dureza DECIMAL(5,2) DEFAULT 0 COMMENT 'Variação permitida na dureza',
    
    -- ETAPAS PARA DERIVAÇÃO
    etapas_corte_largura VARCHAR(200) COMMENT 'IDs das etapas para corte de largura',
    etapas_corte_comprimento VARCHAR(200) COMMENT 'IDs das etapas para corte de comprimento',
    
    ativo TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3.3 Stored Procedure de Matching

```sql
DELIMITER //
CREATE PROCEDURE sp_buscar_match_produto(
    IN p_tipo_correia VARCHAR(50),
    IN p_material_base VARCHAR(100),
    IN p_perfil VARCHAR(50),
    IN p_dureza_shore DECIMAL(5,2),
    IN p_largura_mm DECIMAL(10,2),
    IN p_comprimento_mm DECIMAL(10,2)
)
BEGIN
    -- Busca produtos com DNA compatível e estoque disponível
    SELECT 
        p.id,
        p.name,
        p.stock_quantity,
        e.largura_mm,
        e.comprimento_mm,
        e.codigo_dna,
        CASE 
            WHEN e.largura_mm = p_largura_mm AND e.comprimento_mm = p_comprimento_mm 
                THEN 'EXATO'
            WHEN e.largura_mm >= p_largura_mm AND e.comprimento_mm >= p_comprimento_mm 
                THEN 'DERIVAVEL'
            ELSE 'PARCIAL'
        END AS tipo_match,
        (e.largura_mm - p_largura_mm) AS sobra_largura_mm,
        (e.comprimento_mm - p_comprimento_mm) AS sobra_comprimento_mm
    FROM products p
    INNER JOIN produto_especificacoes_tecnicas e ON e.produto_id = p.id
    WHERE e.tipo_correia = p_tipo_correia
      AND e.material_base = p_material_base
      AND e.perfil = p_perfil
      AND ABS(e.dureza_shore - p_dureza_shore) <= 2 -- tolerância
      AND p.stock_quantity > 0
      AND e.largura_mm >= p_largura_mm
      AND e.comprimento_mm >= p_comprimento_mm
    ORDER BY 
        CASE 
            WHEN e.largura_mm = p_largura_mm AND e.comprimento_mm = p_comprimento_mm THEN 1
            ELSE 2
        END,
        (e.largura_mm - p_largura_mm) + (e.comprimento_mm - p_comprimento_mm) ASC;
END //
DELIMITER ;
```

---

## FASE 4: Fluxo de Derivação de Produto

### 4.1 Conceito

Quando um produto "derivável" é encontrado:

```
[Produto Base 300mm] → [Corte] → [Produto Pedido 15mm] + [Sobra 285mm]
      ↓                              ↓                        ↓
  Baixa Estoque              Novo Produto              Novo Estoque
```

### 4.2 Nova Tabela `produto_derivacoes`

```sql
CREATE TABLE produto_derivacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- ORIGEM
    produto_origem_id INT NOT NULL COMMENT 'Produto base que será derivado',
    quantidade_origem DECIMAL(10,4) NOT NULL COMMENT 'Quantidade usada do origem',
    
    -- DESTINO PRINCIPAL (pedido)
    produto_destino_id INT NOT NULL COMMENT 'Produto resultante para o pedido',
    quantidade_destino DECIMAL(10,4) NOT NULL,
    
    -- SOBRA (novo estoque)
    produto_sobra_id INT COMMENT 'Produto criado com a sobra',
    quantidade_sobra DECIMAL(10,4),
    
    -- VÍNCULO
    ordem_producao_id INT COMMENT 'OP que realizou a derivação',
    orcamento_id INT COMMENT 'Orçamento que originou',
    
    -- CONTROLE
    status ENUM('pendente', 'em_producao', 'concluida', 'cancelada') DEFAULT 'pendente',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INT,
    
    FOREIGN KEY (produto_origem_id) REFERENCES products(id),
    FOREIGN KEY (produto_destino_id) REFERENCES products(id),
    FOREIGN KEY (produto_sobra_id) REFERENCES products(id),
    FOREIGN KEY (ordem_producao_id) REFERENCES ordens_producao(id),
    FOREIGN KEY (orcamento_id) REFERENCES orcamentos(id)
);
```

### 4.3 Fluxo de Produção Simplificado

Para derivação, o produto **NÃO passa por todas as etapas**:

```
ETAPAS NORMAIS:        1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10
ETAPAS DERIVAÇÃO:                      5 → 6         → 10
                                      (Corte) (Acabamento) (Expedição)
```

### 4.4 Tabela de Mapeamento de Etapas para Derivação

```sql
CREATE TABLE derivacao_etapas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo_derivacao ENUM('corte_largura', 'corte_comprimento', 'corte_ambos') NOT NULL,
    tipo_correia VARCHAR(50),
    etapa_id INT NOT NULL,
    sequencia INT NOT NULL,
    obrigatoria TINYINT(1) DEFAULT 1,
    
    FOREIGN KEY (etapa_id) REFERENCES producao_etapas(id),
    INDEX idx_tipo (tipo_derivacao, tipo_correia)
);
```

---

## FASE 5: Interface do Usuário

### 5.1 Cadastro de Produto - Nova Aba "Especificações Técnicas"

```
┌─────────────────────────────────────────────────────────────────┐
│ [Dados] [Fiscal] [Estoque] [Especificações] [Anexos] [DNA]     │
├─────────────────────────────────────────────────────────────────┤
│ ESPECIFICAÇÕES TÉCNICAS DA CORREIA                              │
│                                                                  │
│ ┌─ DIMENSÕES ─────────────────────────────────────────────────┐ │
│ │ Largura (mm): [____150____]  Comprimento (mm): [___3000___] │ │
│ │ Espessura (mm): [____5.0____]                                │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ┌─ TIPO E MATERIAL ───────────────────────────────────────────┐ │
│ │ Tipo: [Sincronizada ▼]  Perfil: [H100 ▼]                    │ │
│ │ Material Base: [Poliuretano ▼]  Revestimento: [_________]   │ │
│ │ Cor: [Preto ▼]  Dureza Shore: [___65___]                    │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ┌─ ESTRUTURA ─────────────────────────────────────────────────┐ │
│ │ Nº Lonas: [__2__]  Tipo Lona: [EP ▼]                        │ │
│ │ Tipo Emenda: [Vulcanizada ▼]  Acabamento Borda: [Selada ▼]  │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ┌─ DNA DO PRODUTO ────────────────────────────────────────────┐ │
│ │ Código DNA: SIN-PU-H100-65-2L-VUL                    [Gerar]│ │
│ │ ⚠️ Este código identifica produtos compatíveis               │ │
│ └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Nova Aba "Anexos"

```
┌─────────────────────────────────────────────────────────────────┐
│ [Dados] [Fiscal] [Estoque] [Especificações] [Anexos] [DNA]     │
├─────────────────────────────────────────────────────────────────┤
│ ANEXOS DO PRODUTO                           [+ Adicionar Anexo] │
│                                                                  │
│ ┌─ DESENHO TÉCNICO ★ ─────────────────────────────────────────┐ │
│ │ 📄 desenho_correia_h100.pdf          v2    12/2025          │ │
│ │    Desenho técnico principal                     [👁] [🗑]  │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ┌─ FOTOS ──────────────────────────────────────────────────────┐ │
│ │ 🖼️ foto_correia.jpg ★               v1    12/2025          │ │
│ │    Foto do produto acabado                       [👁] [🗑]  │ │
│ │ 🖼️ foto_detalhe.jpg                  v1    12/2025          │ │
│ │    Detalhe da emenda                             [👁] [🗑]  │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ┌─ DATASHEETS ─────────────────────────────────────────────────┐ │
│ │ 📄 ficha_tecnica_pu.pdf              v1    12/2025          │ │
│ │    Ficha técnica do material                     [👁] [🗑]  │ │
│ └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Orçamento - Sugestão de Match

```
┌─────────────────────────────────────────────────────────────────┐
│ ADICIONAR ITEM AO ORÇAMENTO                                     │
├─────────────────────────────────────────────────────────────────┤
│ Produto: Correia Sincronizada H100 150mm x 3000mm               │
│ Quantidade: 1                                                    │
│                                                                  │
│ ┌─ 🧬 MATCH DE PRODUTO ENCONTRADO! ───────────────────────────┐ │
│ │                                                              │ │
│ │ ✅ MATCH DERIVÁVEL                                           │ │
│ │                                                              │ │
│ │ Produto em estoque: Correia Sincronizada H100 300mm x 5000mm │ │
│ │ Estoque disponível: 2 unidades                               │ │
│ │ DNA: SIN-PU-H100-65-2L-VUL (compatível)                      │ │
│ │                                                              │ │
│ │ 📋 Processo de Derivação:                                    │ │
│ │ • Cortar largura: 300mm → 150mm (sobra: 150mm)              │ │
│ │ • Cortar comprimento: 5000mm → 3000mm (sobra: 2000mm)       │ │
│ │                                                              │ │
│ │ ⏱️ Tempo estimado: 2h (apenas etapas de corte)               │ │
│ │ 💰 Custo estimado: R$ 150,00                                 │ │
│ │                                                              │ │
│ │ [Usar Produto Derivado]  [Produzir do Zero]                  │ │
│ └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## CRONOGRAMA DE IMPLEMENTAÇÃO

### Semana 1-2: FASE 1 - Cadastro Estruturado
- [ ] Criar tabela `produto_especificacoes_tecnicas`
- [ ] Criar formulário de especificações no cadastro de produto
- [ ] Implementar geração automática do código DNA
- [ ] Migrar dados existentes (extrair do nome/descrição)

### Semana 3: FASE 2 - Anexos
- [ ] Criar tabela `produto_anexos`
- [ ] Criar estrutura de pastas para uploads
- [ ] Implementar upload de arquivos
- [ ] Criar visualizador de anexos (PDF, imagens)

### Semana 4-5: FASE 3 - Sistema de Matching
- [ ] Criar tabela `produto_matching_regras`
- [ ] Implementar stored procedure de matching
- [ ] Criar API de busca de match
- [ ] Integrar com orçamento

### Semana 6-7: FASE 4 - Fluxo de Derivação
- [ ] Criar tabela `produto_derivacoes`
- [ ] Criar tabela `derivacao_etapas`
- [ ] Implementar fluxo de OP simplificado para derivação
- [ ] Controle de estoque (baixa origem, entrada destino e sobra)

### Semana 8: FASE 5 - Interface e Testes
- [ ] Refinar interfaces
- [ ] Testes integrados
- [ ] Documentação
- [ ] Treinamento

---

## ARQUIVOS A CRIAR/MODIFICAR

### Novos Arquivos:
```
app/
├── routes/
│   └── produto_especificacoes_routes.py
├── services/
│   └── produto_matching_service.py
├── templates/
│   └── produtos/
│       ├── produto_especificacoes_form.html
│       ├── produto_anexos.html
│       └── produto_matching_modal.html
└── scripts/
    └── 050_SISTEMA_DNA_PRODUTO.sql
```

### Arquivos a Modificar:
```
app/templates/produtos/form_produto.html  → Adicionar abas
app/routes/produtos_routes.py            → Integrar especificações
app/templates/comercial/orcamento_*.html → Modal de matching
```

---

## PRÓXIMOS PASSOS

**Implementar primeiro a FASE 1 (Cadastro Estruturado)?**

Isso permitirá:
1. Estruturar as especificações das correias
2. Gerar código DNA para cada produto
3. Preparar base para matching futuro

---

**Última Atualização:** 27/12/2025
