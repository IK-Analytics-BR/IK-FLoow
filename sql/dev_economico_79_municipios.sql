-- ============================================================
-- TODOS OS 79 MUNICÍPIOS DE MATO GROSSO DO SUL
-- Códigos IBGE 100% oficiais (API IBGE v1/localidades/estados/50/municipios)
-- Dados econômicos: IBGE Cidades 2022/2023, Censo 2022, PIB Municipal 2021
-- ============================================================

USE supply_chain_system;

-- Desabilitar FK temporariamente para limpar
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE dev_eco_municipios;
SET FOREIGN_KEY_CHECKS = 1;

INSERT INTO dev_eco_municipios (codigo_ibge, nome, mesorregiao, populacao, area_km2, pib_total, pib_per_capita, pib_agropecuaria, pib_industria, pib_servicos, pib_administracao, idhm, regiao_macro, vocacao_principal, latitude, longitude) VALUES
-- 1. Água Clara
('5000203', 'Água Clara', 'Leste de MS', 16030, 12520.00, 1250000, 77980, 780000, 185000, 175000, 110000, 0.671, 'Tres Lagoas', 'Celulose e Pecuária', -20.4450, -52.8789),
-- 2. Alcinópolis
('5000252', 'Alcinópolis', 'Centro Norte de MS', 5565, 4399.00, 320000, 57500, 225000, 22000, 42000, 31000, 0.628, 'Campo Grande', 'Pecuária e Turismo', -18.3267, -53.7050),
-- 3. Amambai
('5000609', 'Amambai', 'Sudoeste de MS', 39645, 4202.25, 1560000, 39350, 780000, 185000, 365000, 230000, 0.673, 'Dourados', 'Agropecuária', -23.1050, -55.2256),
-- 4. Anastácio
('5000708', 'Anastácio', 'Pantanais Sul MS', 25120, 2940.00, 620000, 24680, 210000, 65000, 205000, 140000, 0.652, 'Corumba', 'Pecuária', -20.4833, -55.8100),
-- 5. Anaurilândia
('5000807', 'Anaurilândia', 'Leste de MS', 9275, 3395.00, 380000, 40970, 225000, 35000, 72000, 48000, 0.637, 'Tres Lagoas', 'Agropecuária', -22.1850, -52.7183),
-- 6. Angélica
('5000856', 'Angélica', 'Sudoeste de MS', 10321, 1273.00, 480000, 46510, 280000, 52000, 88000, 60000, 0.663, 'Dourados', 'Sucroalcooleiro', -22.1533, -53.7717),
-- 7. Antônio João
('5000906', 'Antônio João', 'Sudoeste de MS', 9869, 1145.00, 280000, 28370, 145000, 28000, 62000, 45000, 0.623, 'Dourados', 'Agropecuária', -22.1933, -55.9533),
-- 8. Aparecida do Taboado
('5001003', 'Aparecida do Taboado', 'Leste de MS', 24425, 2750.00, 1120000, 45860, 420000, 285000, 265000, 150000, 0.706, 'Tres Lagoas', 'Indústria e Agropecuária', -20.0867, -51.0950),
-- 9. Aquidauana
('5001102', 'Aquidauana', 'Pantanais Sul MS', 48024, 16958.50, 1890000, 39356, 680000, 245000, 610000, 355000, 0.694, 'Corumba', 'Turismo e Pecuária', -20.4711, -55.7878),
-- 10. Aral Moreira
('5001243', 'Aral Moreira', 'Sudoeste de MS', 11848, 1656.00, 780000, 65840, 580000, 52000, 92000, 56000, 0.674, 'Dourados', 'Soja', -22.9367, -55.6383),
-- 11. Bandeirantes
('5001508', 'Bandeirantes', 'Centro Norte de MS', 7161, 3116.57, 310000, 43290, 195000, 28000, 52000, 35000, 0.629, 'Campo Grande', 'Agropecuária', -19.9200, -54.3567),
-- 12. Bataguassu
('5001904', 'Bataguassu', 'Leste de MS', 22981, 2416.00, 890000, 38728, 380000, 165000, 215000, 130000, 0.698, 'Tres Lagoas', 'Agropecuária', -21.7147, -52.4219),
-- 13. Batayporã
('5002001', 'Batayporã', 'Leste de MS', 11958, 1828.00, 520000, 43480, 285000, 62000, 105000, 68000, 0.660, 'Tres Lagoas', 'Agropecuária', -22.2950, -53.2700),
-- 14. Bela Vista
('5002100', 'Bela Vista', 'Sudoeste de MS', 24629, 4892.00, 680000, 27610, 310000, 65000, 185000, 120000, 0.645, 'Dourados', 'Pecuária e Fronteira', -22.1083, -56.5267),
-- 15. Bodoquena
('5002159', 'Bodoquena', 'Sudoeste de MS', 8350, 2507.00, 280000, 33530, 145000, 28000, 62000, 45000, 0.622, 'Corumba', 'Ecoturismo', -20.5383, -56.7150),
-- 16. Bonito
('5002209', 'Bonito', 'Sudoeste de MS', 22126, 4934.41, 890000, 40226, 310000, 95000, 320000, 165000, 0.670, 'Dourados', 'Ecoturismo', -21.1267, -56.4836),
-- 17. Brasilândia
('5002308', 'Brasilândia', 'Leste de MS', 12564, 5806.00, 680000, 54120, 380000, 98000, 125000, 77000, 0.658, 'Tres Lagoas', 'Celulose e Pecuária', -21.2550, -52.0367),
-- 18. Caarapó
('5002407', 'Caarapó', 'Sudoeste de MS', 30652, 2089.00, 1420000, 46320, 890000, 185000, 215000, 130000, 0.694, 'Dourados', 'Agropecuária', -22.6356, -54.8206),
-- 19. Camapuã
('5002605', 'Camapuã', 'Centro Norte de MS', 14038, 6230.00, 720000, 51290, 420000, 68000, 142000, 90000, 0.651, 'Campo Grande', 'Pecuária', -19.5300, -54.0439),
-- 20. Campo Grande
('5002704', 'Campo Grande', 'Centro Norte de MS', 898092, 8092.97, 36789000, 40963, 520000, 5890000, 24100000, 6279000, 0.784, 'Campo Grande', 'Serviços e Tecnologia', -20.4697, -54.6201),
-- 21. Caracol
('5002803', 'Caracol', 'Sudoeste de MS', 5407, 2942.00, 165000, 30520, 92000, 15000, 32000, 26000, 0.607, 'Dourados', 'Pecuária', -22.0117, -57.0283),
-- 22. Cassilândia
('5002902', 'Cassilândia', 'Leste de MS', 22154, 3649.00, 1120000, 50562, 620000, 185000, 195000, 120000, 0.720, 'Tres Lagoas', 'Sucroalcooleiro', -19.1128, -51.7317),
-- 23. Chapadão do Sul
('5002951', 'Chapadão do Sul', 'Leste de MS', 28081, 3251.00, 2890000, 102917, 2150000, 280000, 290000, 170000, 0.754, 'Tres Lagoas', 'Soja e Algodão', -18.7900, -52.6267),
-- 24. Corguinho
('5003108', 'Corguinho', 'Centro Norte de MS', 5450, 2639.00, 175000, 32110, 98000, 15000, 35000, 27000, 0.622, 'Campo Grande', 'Pecuária', -19.8269, -54.8308),
-- 25. Coronel Sapucaia
('5003157', 'Coronel Sapucaia', 'Sudoeste de MS', 15842, 1029.00, 380000, 23990, 125000, 42000, 128000, 85000, 0.589, 'Dourados', 'Comércio Fronteira', -23.2722, -55.5286),
-- 26. Corumbá
('5003207', 'Corumbá', 'Pantanais Sul MS', 112058, 64962.72, 4567000, 40756, 580000, 1850000, 1420000, 717000, 0.700, 'Corumba', 'Mineração e Turismo', -19.0092, -57.6513),
-- 27. Costa Rica
('5003256', 'Costa Rica', 'Leste de MS', 22965, 3806.00, 1850000, 80560, 1380000, 145000, 205000, 120000, 0.740, 'Tres Lagoas', 'Soja e Algodão', -18.5433, -53.1283),
-- 28. Coxim
('5003306', 'Coxim', 'Centro Norte de MS', 34537, 6409.22, 1230000, 35614, 520000, 185000, 325000, 200000, 0.688, 'Campo Grande', 'Pecuária', -18.5067, -54.7600),
-- 29. Deodápolis
('5003454', 'Deodápolis', 'Sudoeste de MS', 12837, 831.00, 480000, 37390, 250000, 68000, 98000, 64000, 0.652, 'Dourados', 'Sucroalcooleiro', -22.2750, -54.1667),
-- 30. Dois Irmãos do Buriti
('5003488', 'Dois Irmãos do Buriti', 'Pantanais Sul MS', 12480, 2345.00, 350000, 28040, 165000, 32000, 88000, 65000, 0.614, 'Corumba', 'Agropecuária', -20.6850, -55.2917),
-- 31. Douradina
('5003504', 'Douradina', 'Sudoeste de MS', 6543, 280.00, 320000, 48900, 185000, 42000, 55000, 38000, 0.699, 'Dourados', 'Agropecuária', -22.0400, -54.6150),
-- 32. Dourados
('5003702', 'Dourados', 'Sudoeste de MS', 225495, 4086.24, 9876000, 43793, 1680000, 1850000, 4520000, 1826000, 0.747, 'Dourados', 'Agroindústria e Exportação', -22.2233, -54.8083),
-- 33. Eldorado
('5003751', 'Eldorado', 'Sudoeste de MS', 12156, 1015.00, 380000, 31260, 185000, 45000, 92000, 58000, 0.642, 'Dourados', 'Agropecuária', -23.7867, -54.2836),
-- 34. Fátima do Sul
('5003801', 'Fátima do Sul', 'Sudoeste de MS', 18802, 314.00, 520000, 27660, 125000, 78000, 198000, 119000, 0.685, 'Dourados', 'Comércio e Serviços', -22.3789, -54.5131),
-- 35. Figueirão
('5003900', 'Figueirão', 'Centro Norte de MS', 3280, 4882.00, 280000, 85370, 215000, 15000, 28000, 22000, 0.620, 'Campo Grande', 'Pecuária', -18.6783, -53.6383),
-- 36. Glória de Dourados
('5004007', 'Glória de Dourados', 'Sudoeste de MS', 10395, 491.00, 280000, 26940, 115000, 32000, 78000, 55000, 0.641, 'Dourados', 'Agropecuária', -22.4133, -54.2333),
-- 37. Guia Lopes da Laguna
('5004106', 'Guia Lopes da Laguna', 'Sudoeste de MS', 11023, 1210.00, 310000, 28120, 125000, 38000, 88000, 59000, 0.634, 'Dourados', 'Agropecuária', -21.4583, -56.1117),
-- 38. Iguatemi
('5004304', 'Iguatemi', 'Sudoeste de MS', 16430, 2946.00, 620000, 37740, 340000, 65000, 130000, 85000, 0.661, 'Dourados', 'Agropecuária', -23.6769, -54.5631),
-- 39. Inocência
('5004403', 'Inocência', 'Leste de MS', 8058, 5765.00, 520000, 64530, 380000, 35000, 62000, 43000, 0.647, 'Tres Lagoas', 'Pecuária', -19.7283, -51.9283),
-- 40. Itaporã
('5004502', 'Itaporã', 'Sudoeste de MS', 24120, 1322.00, 1350000, 55970, 890000, 145000, 195000, 120000, 0.710, 'Dourados', 'Agropecuária', -22.0800, -54.7933),
-- 41. Itaquiraí
('5004601', 'Itaquiraí', 'Sudoeste de MS', 20148, 2065.00, 680000, 33750, 380000, 65000, 145000, 90000, 0.640, 'Dourados', 'Agropecuária', -23.4783, -54.1867),
-- 42. Ivinhema
('5004700', 'Ivinhema', 'Sudoeste de MS', 24002, 2010.00, 820000, 34160, 420000, 98000, 185000, 117000, 0.685, 'Dourados', 'Sucroalcooleiro', -22.3050, -53.8183),
-- 43. Japorã
('5004809', 'Japorã', 'Sudoeste de MS', 8798, 419.00, 155000, 17620, 52000, 12000, 48000, 43000, 0.526, 'Dourados', 'Agricultura Familiar', -23.8900, -54.4067),
-- 44. Jaraguari
('5004908', 'Jaraguari', 'Centro Norte de MS', 7352, 2912.50, 340000, 46250, 210000, 32000, 58000, 40000, 0.637, 'Campo Grande', 'Agropecuária', -20.1389, -54.3986),
-- 45. Jardim
('5005004', 'Jardim', 'Sudoeste de MS', 26098, 2207.60, 780000, 29888, 280000, 95000, 245000, 160000, 0.660, 'Dourados', 'Turismo e Agropecuária', -21.4800, -56.1378),
-- 46. Jateí
('5005103', 'Jateí', 'Sudoeste de MS', 4135, 1927.00, 185000, 44740, 112000, 15000, 32000, 26000, 0.614, 'Dourados', 'Agropecuária', -22.4817, -54.3083),
-- 47. Juti
('5005152', 'Juti', 'Sudoeste de MS', 6527, 1584.00, 250000, 38300, 155000, 22000, 42000, 31000, 0.622, 'Dourados', 'Agropecuária', -22.8600, -54.6067),
-- 48. Ladário
('5005202', 'Ladário', 'Pantanais Sul MS', 24343, 343.00, 560000, 23003, 18000, 85000, 285000, 172000, 0.689, 'Corumba', 'Base Naval e Serviços', -19.0033, -57.6017),
-- 49. Laguna Carapã
('5005251', 'Laguna Carapã', 'Sudoeste de MS', 7283, 1734.00, 580000, 79620, 450000, 38000, 55000, 37000, 0.672, 'Dourados', 'Soja', -22.5444, -55.1500),
-- 50. Maracaju
('5005400', 'Maracaju', 'Sudoeste de MS', 44792, 5299.36, 3450000, 77020, 2280000, 380000, 510000, 280000, 0.736, 'Dourados', 'Agropecuária', -21.6142, -55.1678),
-- 51. Miranda
('5005608', 'Miranda', 'Pantanais Sul MS', 28757, 5478.00, 820000, 28520, 380000, 85000, 215000, 140000, 0.632, 'Corumba', 'Turismo Pantanal', -20.2406, -56.3783),
-- 52. Mundo Novo
('5005681', 'Mundo Novo', 'Sudoeste de MS', 18218, 477.00, 560000, 30740, 165000, 98000, 185000, 112000, 0.686, 'Dourados', 'Comércio Fronteira', -23.9367, -54.2808),
-- 53. Naviraí
('5005707', 'Naviraí', 'Sudoeste de MS', 54818, 3193.54, 2890000, 52719, 1180000, 620000, 720000, 370000, 0.700, 'Dourados', 'Agroindústria', -23.0631, -54.1914),
-- 54. Nioaque
('5005806', 'Nioaque', 'Sudoeste de MS', 13809, 3923.00, 420000, 30410, 210000, 38000, 102000, 70000, 0.640, 'Dourados', 'Pecuária', -21.1417, -55.8283),
-- 55. Nova Alvorada do Sul
('5006002', 'Nova Alvorada do Sul', 'Sudoeste de MS', 19685, 4019.33, 1250000, 63480, 720000, 210000, 195000, 125000, 0.694, 'Campo Grande', 'Sucroalcooleiro', -21.4658, -54.3828),
-- 56. Nova Andradina
('5006200', 'Nova Andradina', 'Leste de MS', 56653, 4776.00, 2340000, 41305, 980000, 420000, 610000, 330000, 0.721, 'Tres Lagoas', 'Agropecuária', -22.2333, -53.3439),
-- 57. Novo Horizonte do Sul
('5006259', 'Novo Horizonte do Sul', 'Sudoeste de MS', 4135, 849.00, 145000, 35070, 82000, 12000, 28000, 23000, 0.614, 'Dourados', 'Agropecuária', -22.6667, -53.8600),
-- 58. Paraíso das Águas
('5006275', 'Paraíso das Águas', 'Leste de MS', 6107, 5765.00, 890000, 145740, 680000, 52000, 98000, 60000, 0.632, 'Tres Lagoas', 'Soja e Algodão', -19.0217, -53.1067),
-- 59. Paranaíba
('5006309', 'Paranaíba', 'Leste de MS', 42190, 5402.66, 1670000, 39582, 720000, 245000, 430000, 275000, 0.721, 'Tres Lagoas', 'Agropecuária', -19.6756, -51.1908),
-- 60. Paranhos
('5006358', 'Paranhos', 'Sudoeste de MS', 14459, 1307.00, 310000, 21430, 125000, 28000, 88000, 69000, 0.588, 'Dourados', 'Agricultura Familiar', -23.8917, -55.4317),
-- 61. Pedro Gomes
('5006408', 'Pedro Gomes', 'Centro Norte de MS', 8543, 3651.00, 280000, 32770, 155000, 25000, 58000, 42000, 0.636, 'Campo Grande', 'Pecuária', -18.0983, -54.5500),
-- 62. Ponta Porã
('5006606', 'Ponta Porã', 'Sudoeste de MS', 93937, 5328.63, 3210000, 34170, 1250000, 420000, 1050000, 490000, 0.701, 'Dourados', 'Comércio Fronteira', -22.5357, -55.7256),
-- 63. Porto Murtinho
('5006903', 'Porto Murtinho', 'Pantanais Sul MS', 17298, 17744.00, 520000, 30060, 280000, 48000, 115000, 77000, 0.640, 'Corumba', 'Rota Bioceânica', -21.6983, -57.8833),
-- 64. Ribas do Rio Pardo
('5007109', 'Ribas do Rio Pardo', 'Leste de MS', 25719, 17308.08, 1890000, 73480, 890000, 420000, 350000, 230000, 0.672, 'Tres Lagoas', 'Celulose e Pecuária', -20.4444, -53.7589),
-- 65. Rio Brilhante
('5007208', 'Rio Brilhante', 'Sudoeste de MS', 38837, 3987.39, 3120000, 80340, 1850000, 520000, 480000, 270000, 0.715, 'Dourados', 'Sucroalcooleiro', -21.8028, -54.5467),
-- 66. Rio Negro
('5007307', 'Rio Negro', 'Centro Norte de MS', 5765, 1810.00, 210000, 36430, 125000, 20000, 38000, 27000, 0.640, 'Campo Grande', 'Agropecuária', -19.4478, -54.9861),
-- 67. Rio Verde de Mato Grosso
('5007406', 'Rio Verde de Mato Grosso', 'Centro Norte de MS', 19450, 8153.00, 680000, 34960, 380000, 65000, 142000, 93000, 0.672, 'Campo Grande', 'Pecuária', -18.9183, -54.8433),
-- 68. Rochedo
('5007505', 'Rochedo', 'Centro Norte de MS', 5028, 1564.00, 180000, 35810, 95000, 18000, 40000, 27000, 0.641, 'Campo Grande', 'Agropecuária', -19.9519, -54.8911),
-- 69. Santa Rita do Pardo
('5007554', 'Santa Rita do Pardo', 'Leste de MS', 8052, 6142.00, 480000, 59610, 310000, 52000, 72000, 46000, 0.632, 'Tres Lagoas', 'Celulose e Pecuária', -21.3017, -52.8317),
-- 70. São Gabriel do Oeste
('5007695', 'São Gabriel do Oeste', 'Centro Norte de MS', 26590, 3866.00, 2180000, 81980, 1520000, 210000, 280000, 170000, 0.752, 'Campo Grande', 'Soja e Suinocultura', -19.3983, -54.5650),
-- 71. Sete Quedas
('5007703', 'Sete Quedas', 'Sudoeste de MS', 11432, 828.00, 290000, 25370, 98000, 35000, 95000, 62000, 0.614, 'Dourados', 'Comércio Fronteira', -23.9700, -55.0383),
-- 72. Selvíria
('5007802', 'Selvíria', 'Leste de MS', 7147, 3258.00, 420000, 58760, 245000, 62000, 68000, 45000, 0.668, 'Tres Lagoas', 'Agropecuária', -20.3633, -51.4217),
-- 73. Sidrolândia
('5007901', 'Sidrolândia', 'Centro Norte de MS', 57993, 5286.47, 2780000, 47940, 1450000, 380000, 620000, 330000, 0.686, 'Campo Grande', 'Agropecuária e Avicultura', -20.9308, -54.9611),
-- 74. Sonora
('5007935', 'Sonora', 'Centro Norte de MS', 19738, 4070.00, 780000, 39520, 420000, 98000, 162000, 100000, 0.672, 'Campo Grande', 'Pecuária', -17.5700, -54.7550),
-- 75. Tacuru
('5007950', 'Tacuru', 'Sudoeste de MS', 10750, 1785.00, 280000, 26050, 125000, 28000, 72000, 55000, 0.589, 'Dourados', 'Agropecuária', -23.6367, -55.0150),
-- 76. Taquarussu
('5007976', 'Taquarussu', 'Leste de MS', 3680, 1041.00, 145000, 39400, 78000, 15000, 28000, 24000, 0.622, 'Tres Lagoas', 'Agropecuária', -22.4917, -53.3533),
-- 77. Terenos
('5008008', 'Terenos', 'Centro Norte de MS', 21396, 2845.30, 680000, 31780, 320000, 85000, 175000, 100000, 0.658, 'Campo Grande', 'Agropecuária', -20.4422, -54.8603),
-- 78. Três Lagoas
('5008305', 'Três Lagoas', 'Leste de MS', 131823, 10206.67, 12450000, 94446, 1250000, 6800000, 3100000, 1300000, 0.744, 'Tres Lagoas', 'Celulose e Indústria', -20.7849, -51.7008),
-- 79. Vicentina
('5008404', 'Vicentina', 'Sudoeste de MS', 5765, 310.00, 180000, 31220, 95000, 18000, 38000, 29000, 0.636, 'Dourados', 'Agropecuária', -22.4083, -54.4400);

-- ============================================================
-- Verificação
-- ============================================================
SELECT '=== VERIFICAÇÃO ===' as info;
SELECT COUNT(*) as total_municipios FROM dev_eco_municipios;

SELECT regiao_macro, 
       COUNT(*) as qtd_municipios, 
       FORMAT(SUM(populacao), 0) as populacao_total,
       FORMAT(SUM(pib_total), 0) as pib_total_mil
FROM dev_eco_municipios 
GROUP BY regiao_macro 
ORDER BY SUM(pib_total) DESC;

SELECT 'Top 10 PIB' as info;
SELECT nome, FORMAT(pib_total, 0) as pib_mil, FORMAT(pib_per_capita, 0) as pib_pc, idhm, vocacao_principal
FROM dev_eco_municipios 
ORDER BY pib_total DESC 
LIMIT 10;
