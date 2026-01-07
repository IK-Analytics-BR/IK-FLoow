"""Criar VIEWs para cálculos de tempo produtivo"""
import sys
sys.path.insert(0, '.')
from app.database import Database

db = Database()

views = [
    # VIEW 1: Resumo de pausas por operador/dia
    """
    CREATE OR REPLACE VIEW vw_producao_pausas_resumo AS
    SELECT 
        pp.operador_id,
        u.name AS operador_nome,
        DATE(pp.inicio) AS data,
        COUNT(*) AS total_pausas,
        SUM(CASE WHEN m.tipo = 'produtivo' THEN COALESCE(pp.duracao_minutos, 0) ELSE 0 END) AS minutos_produtivos,
        SUM(CASE WHEN m.tipo = 'improdutivo' THEN COALESCE(pp.duracao_minutos, 0) ELSE 0 END) AS minutos_improdutivos,
        SUM(COALESCE(pp.duracao_minutos, 0)) AS minutos_totais
    FROM producao_pausas pp
    INNER JOIN users u ON u.id = pp.operador_id
    INNER JOIN producao_pausas_motivos m ON m.id = pp.motivo_id
    WHERE pp.fim IS NOT NULL
    GROUP BY pp.operador_id, DATE(pp.inicio)
    """,
    
    # VIEW 2: Tempo produtivo por lote
    """
    CREATE OR REPLACE VIEW vw_lote_tempo_producao AS
    SELECT 
        l.id AS lote_id,
        l.ordem_producao_id,
        op.numero_op,
        l.quantidade,
        l.etapa_atual_id,
        e.nome AS etapa_nome,
        l.operador_id,
        u.name AS operador_nome,
        l.data_inicio_operador,
        l.data_fim_operador,
        l.status_operador,
        TIMESTAMPDIFF(MINUTE, l.data_inicio_operador, COALESCE(l.data_fim_operador, NOW())) AS tempo_bruto_min,
        COALESCE((
            SELECT SUM(pp.duracao_minutos) 
            FROM producao_pausas pp 
            INNER JOIN producao_pausas_motivos m ON m.id = pp.motivo_id
            WHERE pp.lote_id = l.id AND m.tipo = 'improdutivo' AND pp.fim IS NOT NULL
        ), 0) AS pausas_improdutivas_min,
        COALESCE((
            SELECT SUM(pp.duracao_minutos) 
            FROM producao_pausas pp 
            INNER JOIN producao_pausas_motivos m ON m.id = pp.motivo_id
            WHERE pp.lote_id = l.id AND m.tipo = 'produtivo' AND pp.fim IS NOT NULL
        ), 0) AS pausas_produtivas_min,
        TIMESTAMPDIFF(MINUTE, l.data_inicio_operador, COALESCE(l.data_fim_operador, NOW())) 
            - COALESCE((
                SELECT SUM(pp.duracao_minutos) 
                FROM producao_pausas pp 
                INNER JOIN producao_pausas_motivos m ON m.id = pp.motivo_id
                WHERE pp.lote_id = l.id AND m.tipo = 'improdutivo' AND pp.fim IS NOT NULL
            ), 0) AS tempo_produtivo_min
    FROM op_lotes l
    INNER JOIN ordens_producao op ON op.id = l.ordem_producao_id
    LEFT JOIN producao_etapas e ON e.id = l.etapa_atual_id
    LEFT JOIN users u ON u.id = l.operador_id
    WHERE l.data_inicio_operador IS NOT NULL
    """,
    
    # VIEW 3: Produtividade do operador
    """
    CREATE OR REPLACE VIEW vw_operador_produtividade AS
    SELECT 
        l.operador_id,
        u.name AS operador_nome,
        DATE(l.data_inicio_operador) AS data,
        COUNT(DISTINCT l.id) AS total_lotes,
        SUM(l.quantidade) AS total_unidades,
        SUM(TIMESTAMPDIFF(MINUTE, l.data_inicio_operador, COALESCE(l.data_fim_operador, NOW()))) AS tempo_bruto_total_min,
        SUM(COALESCE((
            SELECT SUM(pp.duracao_minutos) 
            FROM producao_pausas pp 
            INNER JOIN producao_pausas_motivos m ON m.id = pp.motivo_id
            WHERE pp.lote_id = l.id AND m.tipo = 'improdutivo' AND pp.fim IS NOT NULL
        ), 0)) AS pausas_improdutivas_total_min,
        SUM(TIMESTAMPDIFF(MINUTE, l.data_inicio_operador, COALESCE(l.data_fim_operador, NOW()))) 
            - SUM(COALESCE((
                SELECT SUM(pp.duracao_minutos) 
                FROM producao_pausas pp 
                INNER JOIN producao_pausas_motivos m ON m.id = pp.motivo_id
                WHERE pp.lote_id = l.id AND m.tipo = 'improdutivo' AND pp.fim IS NOT NULL
            ), 0)) AS tempo_produtivo_total_min
    FROM op_lotes l
    INNER JOIN users u ON u.id = l.operador_id
    WHERE l.data_inicio_operador IS NOT NULL
    GROUP BY l.operador_id, DATE(l.data_inicio_operador)
    """,
    
    # VIEW 4: Tempo médio por produto
    """
    CREATE OR REPLACE VIEW vw_tempo_medio_produto AS
    SELECT 
        op.produto_id,
        p.name AS produto_nome,
        COUNT(DISTINCT l.id) AS total_lotes_concluidos,
        SUM(l.quantidade) AS total_unidades,
        AVG(
            TIMESTAMPDIFF(MINUTE, l.data_inicio_operador, l.data_fim_operador) 
            - COALESCE((
                SELECT SUM(pp.duracao_minutos) 
                FROM producao_pausas pp 
                INNER JOIN producao_pausas_motivos m ON m.id = pp.motivo_id
                WHERE pp.lote_id = l.id AND m.tipo = 'improdutivo' AND pp.fim IS NOT NULL
            ), 0)
        ) AS tempo_medio_lote_min,
        CASE 
            WHEN SUM(l.quantidade) > 0 THEN
                SUM(
                    TIMESTAMPDIFF(MINUTE, l.data_inicio_operador, l.data_fim_operador) 
                    - COALESCE((
                        SELECT SUM(pp.duracao_minutos) 
                        FROM producao_pausas pp 
                        INNER JOIN producao_pausas_motivos m ON m.id = pp.motivo_id
                        WHERE pp.lote_id = l.id AND m.tipo = 'improdutivo' AND pp.fim IS NOT NULL
                    ), 0)
                ) / SUM(l.quantidade)
            ELSE 0 
        END AS tempo_medio_unitario_min
    FROM op_lotes l
    INNER JOIN ordens_producao op ON op.id = l.ordem_producao_id
    INNER JOIN products p ON p.id = op.produto_id
    WHERE l.data_fim_operador IS NOT NULL
    GROUP BY op.produto_id
    """
]

print("Criando VIEWs para cálculos de tempo...")
for i, v in enumerate(views):
    try:
        db.execute(v)
        print(f"  VIEW {i+1} criada com sucesso!")
    except Exception as e:
        print(f"  VIEW {i+1} erro: {e}")

print("\nVIEWs criadas!")
print("\nVIEWs disponíveis:")
print("  - vw_producao_pausas_resumo: Pausas por operador/dia")
print("  - vw_lote_tempo_producao: Tempo por lote (bruto/produtivo)")
print("  - vw_operador_produtividade: Produtividade diária do operador")
print("  - vw_tempo_medio_produto: Tempo médio por produto")
