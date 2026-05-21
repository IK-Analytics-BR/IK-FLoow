-- ============================================================
-- FIX: Inserir Encadeamentos Produtivos Latentes
-- Usa JOIN para resolver IDs dos municípios pelo nome
-- ============================================================

USE supply_chain_system;
SET SQL_SAFE_UPDATES = 0;

-- Verificar nomes exatos dos municípios-chave
SELECT id, nome FROM dev_eco_municipios 
WHERE nome IN ('Três Lagoas', 'Dourados', 'Bonito', 'Maracaju', 'Corumbá', 
               'Sidrolândia', 'Aquidauana', 'Naviraí', 'Campo Grande', 
               'Ponta Porã', 'Rio Brilhante', 'Costa Rica')
ORDER BY nome;

-- Limpar tentativas anteriores
DELETE FROM dev_eco_encadeamento_latente;

-- Inserir usando variáveis para cada município
SET @tres_lagoas = (SELECT id FROM dev_eco_municipios WHERE nome LIKE 'Três Lagoas%' LIMIT 1);
SET @dourados = (SELECT id FROM dev_eco_municipios WHERE nome LIKE 'Dourados%' LIMIT 1);
SET @bonito = (SELECT id FROM dev_eco_municipios WHERE nome LIKE 'Bonito%' LIMIT 1);
SET @maracaju = (SELECT id FROM dev_eco_municipios WHERE nome LIKE 'Maracaju%' LIMIT 1);
SET @corumba = (SELECT id FROM dev_eco_municipios WHERE nome LIKE 'Corumbá%' LIMIT 1);
SET @sidrolandia = (SELECT id FROM dev_eco_municipios WHERE nome LIKE 'Sidrolândia%' LIMIT 1);
SET @aquidauana = (SELECT id FROM dev_eco_municipios WHERE nome LIKE 'Aquidauana%' LIMIT 1);
SET @navirai = (SELECT id FROM dev_eco_municipios WHERE nome LIKE 'Naviraí%' LIMIT 1);
SET @campo_grande = (SELECT id FROM dev_eco_municipios WHERE nome LIKE 'Campo Grande%' LIMIT 1);
SET @ponta_pora = (SELECT id FROM dev_eco_municipios WHERE nome LIKE 'Ponta Porã%' LIMIT 1);
SET @rio_brilhante = (SELECT id FROM dev_eco_municipios WHERE nome LIKE 'Rio Brilhante%' LIMIT 1);
SET @costa_rica = (SELECT id FROM dev_eco_municipios WHERE nome LIKE 'Costa Rica%' LIMIT 1);

-- Verificar se encontrou todos
SELECT 
    @tres_lagoas as tres_lagoas, @dourados as dourados, @bonito as bonito,
    @maracaju as maracaju, @corumba as corumba, @sidrolandia as sidrolandia,
    @aquidauana as aquidauana, @navirai as navirai, @campo_grande as campo_grande,
    @ponta_pora as ponta_pora, @rio_brilhante as rio_brilhante, @costa_rica as costa_rica;

-- Inserir encadeamentos
INSERT INTO dev_eco_encadeamento_latente 
(municipio_id, materia_prima, producao_atual_ton, valor_producao_atual, industria_ausente, cnae_potencial, demanda_estimada_ton, importacao_regional, gap_valor, empregos_potenciais, investimento_estimado, impacto_pib_estimado, payback_estimado_anos, viabilidade, prioridade) VALUES
-- 1. Três Lagoas: celulose → papel tissue/embalagens
(@tres_lagoas, 'Celulose', 7500000, 28000000000, 'Fábrica de Papel Tissue/Embalagens', '17.21', 500000, 2800000000, 3500000000, 850, 450000000, 890000000, 3.5, 'Alta', 'Alta'),
-- 2. Dourados: soja → esmagadora/biodiesel
(@dourados, 'Soja em Grão', 3200000, 8500000000, 'Esmagadora de Soja / Biodiesel', '10.41', 1500000, 4200000000, 5800000000, 420, 380000000, 720000000, 4.0, 'Alta', 'Crítica'),
-- 3. Bonito: frutas → polpas/sucos
(@bonito, 'Frutas Regionais (Guavira, Bocaiuva)', 8500, 25000000, 'Indústria de Polpas e Sucos Nativos', '10.33', 15000, 85000000, 120000000, 180, 15000000, 45000000, 2.5, 'Alta', 'Alta'),
-- 4. Maracaju: milho → ração animal
(@maracaju, 'Milho 2ª Safra', 2800000, 4200000000, 'Fábrica de Ração Animal Premium', '10.66', 800000, 1200000000, 1800000000, 320, 120000000, 380000000, 3.0, 'Alta', 'Alta'),
-- 5. Corumbá: minério → pelotização
(@corumba, 'Minério de Ferro', 5000000, 12000000000, 'Usina de Pelotização', '07.10', 3000000, 8500000000, 6500000000, 600, 850000000, 1200000000, 5.0, 'Média', 'Alta'),
-- 6. Sidrolândia: frango → processados
(@sidrolandia, 'Frango Abatido', 450000, 3200000000, 'Fábrica de Empanados/Processados', '10.12', 200000, 1500000000, 2100000000, 550, 180000000, 420000000, 3.0, 'Alta', 'Crítica'),
-- 7. Aquidauana: leite → queijos especiais
(@aquidauana, 'Leite in natura', 85000, 280000000, 'Laticínio de Queijos Artesanais/Especiais', '10.52', 120000, 450000000, 380000000, 150, 25000000, 85000000, 2.0, 'Alta', 'Alta'),
-- 8. Naviraí: mandioca → fécula/amido
(@navirai, 'Mandioca', 320000, 180000000, 'Fecularia / Amido Modificado', '10.63', 250000, 520000000, 450000000, 220, 45000000, 120000000, 2.5, 'Alta', 'Média'),
-- 9. Campo Grande: TI → data center
(@campo_grande, 'Mão de obra qualificada TI', 0, 0, 'Data Center / Hub de Cloud Computing', '63.11', 0, 2500000000, 3200000000, 1200, 250000000, 580000000, 3.5, 'Alta', 'Crítica'),
-- 10. Ponta Porã: fronteira → zona processamento
(@ponta_pora, 'Fluxo Comercial Fronteira', 0, 3500000000, 'Zona de Processamento de Exportação', '52.11', 0, 1800000000, 2500000000, 800, 200000000, 450000000, 3.0, 'Média', 'Alta'),
-- 11. Rio Brilhante: cana → biogás
(@rio_brilhante, 'Vinhaça e Palha de Cana', 2500000, 0, 'Usina de Biogás/Biometano', '35.21', 0, 350000000, 480000000, 120, 85000000, 180000000, 4.0, 'Alta', 'Alta'),
-- 12. Costa Rica: algodão → fiação
(@costa_rica, 'Algodão em Pluma', 180000, 2800000000, 'Fiação e Tecelagem Básica', '13.11', 120000, 1500000000, 1800000000, 450, 150000000, 320000000, 3.5, 'Média', 'Média');

-- Verificação
SELECT '=== ENCADEAMENTOS INSERIDOS ===' as info;
SELECT COUNT(*) as total FROM dev_eco_encadeamento_latente;
SELECT e.industria_ausente, m.nome as municipio, e.viabilidade, e.prioridade, 
       FORMAT(e.gap_valor, 0) as gap_valor
FROM dev_eco_encadeamento_latente e 
JOIN dev_eco_municipios m ON e.municipio_id = m.id
ORDER BY e.gap_valor DESC;
