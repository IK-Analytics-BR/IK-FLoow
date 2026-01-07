"""
Rotas de Configuração de Produção
- Jornada de trabalho
- Tempos por produto/etapa
- Feriados
- Capacidade por etapa
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.database import get_db
from app.services.previsao_producao_service import get_previsao_service
from functools import wraps
from datetime import datetime

config_producao_bp = Blueprint('config_producao', __name__, url_prefix='/industria/config')


def admin_required(f):
    """Decorator para exigir role de admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in ['admin', 'adm']:
            flash('Acesso negado. Apenas administradores.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


# =========================================================
# TEMPOS DE PRODUÇÃO POR PRODUTO/ETAPA
# =========================================================

@config_producao_bp.route('/tempos-producao')
@login_required
@admin_required
def tempos_producao():
    """Tela de configuração de tempos por produto/etapa"""
    db = get_db()
    
    # Filtros
    filtro_produto = request.args.get('produto', '')
    filtro_etapa = request.args.get('etapa', '')
    
    # Buscar produtos com tempos configurados
    query = """
        SELECT 
            p.id as produto_id,
            p.name as produto_nome,
            COALESCE(p.barcode, p.id) as produto_codigo,
            e.id as etapa_id,
            e.nome as etapa_nome,
            e.ordem as etapa_ordem,
            COALESCE(pt.tempo_padrao_minutos, 0) as tempo_padrao,
            COALESCE(pt.tempo_medio_historico, 0) as tempo_historico,
            COALESCE(pt.tempo_minimo_historico, 0) as tempo_minimo,
            COALESCE(pt.tempo_maximo_historico, 0) as tempo_maximo,
            COALESCE(pt.qtd_amostras, 0) as qtd_amostras,
            COALESCE(pt.ajuste_manual, 0) as ajuste_manual,
            pt.ultima_atualizacao_historico,
            pt.observacao
        FROM products p
        CROSS JOIN producao_etapas e
        LEFT JOIN produtos_tempo_etapa pt ON pt.produto_id = p.id AND pt.etapa_id = e.id
        WHERE e.ativo = 1
    """
    params = []
    
    if filtro_produto:
        query += " AND (p.name LIKE %s OR p.barcode LIKE %s)"
        params.extend([f'%{filtro_produto}%', f'%{filtro_produto}%'])
    
    if filtro_etapa:
        query += " AND e.id = %s"
        params.append(filtro_etapa)
    
    query += " ORDER BY p.name, e.ordem LIMIT 500"
    
    tempos = db.fetch_all(query, params) or []
    
    # Buscar lista de etapas para filtro
    etapas = db.fetch_all("SELECT id, nome FROM producao_etapas WHERE ativo = 1 ORDER BY ordem") or []
    
    # Agrupar por produto
    produtos_tempos = {}
    for t in tempos:
        if t['produto_id'] not in produtos_tempos:
            produtos_tempos[t['produto_id']] = {
                'produto_id': t['produto_id'],
                'produto_nome': t['produto_nome'],
                'produto_codigo': t['produto_codigo'],
                'etapas': []
            }
        produtos_tempos[t['produto_id']]['etapas'].append(t)
    
    return render_template('industria/config_tempos_producao.html',
                          produtos_tempos=list(produtos_tempos.values()),
                          etapas=etapas,
                          filtro_produto=filtro_produto,
                          filtro_etapa=filtro_etapa)


@config_producao_bp.route('/tempos-producao/salvar', methods=['POST'])
@login_required
@admin_required
def salvar_tempo_producao():
    """Salva tempo de produção de um produto/etapa"""
    db = get_db()
    
    produto_id = request.form.get('produto_id')
    etapa_id = request.form.get('etapa_id')
    tempo_padrao = request.form.get('tempo_padrao', 0)
    observacao = request.form.get('observacao', '')
    
    if not produto_id or not etapa_id:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    
    try:
        tempo_padrao = int(tempo_padrao) if tempo_padrao else 0
    except:
        tempo_padrao = 0
    
    # Inserir ou atualizar
    query = """
        INSERT INTO produtos_tempo_etapa (produto_id, etapa_id, tempo_padrao_minutos, ajuste_manual, observacao)
        VALUES (%s, %s, %s, 1, %s)
        ON DUPLICATE KEY UPDATE
            tempo_padrao_minutos = %s,
            ajuste_manual = 1,
            observacao = %s,
            updated_at = NOW()
    """
    db.execute_query(query, [produto_id, etapa_id, tempo_padrao, observacao, tempo_padrao, observacao])
    
    return jsonify({'success': True})


@config_producao_bp.route('/tempos-producao/calcular-historico', methods=['POST'])
@login_required
@admin_required
def calcular_historico():
    """Recalcula tempos históricos a partir do log de produção"""
    db = get_db()
    
    try:
        # Chamar stored procedure
        db.execute_query("CALL sp_calcular_tempos_historicos()")
        
        # Contar registros atualizados
        result = db.fetch_one("SELECT COUNT(*) as cnt FROM produtos_tempo_etapa WHERE qtd_amostras > 0")
        qtd = result['cnt'] if result else 0
        
        return jsonify({
            'success': True, 
            'message': f'Histórico recalculado. {qtd} combinações produto/etapa atualizadas.'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =========================================================
# FERIADOS
# =========================================================

@config_producao_bp.route('/feriados')
@login_required
@admin_required
def feriados():
    """Tela de configuração de feriados"""
    db = get_db()
    
    ano = request.args.get('ano', datetime.now().year)
    
    feriados = db.fetch_all("""
        SELECT f.*, e.razao_social as empresa_nome
        FROM config_feriados f
        LEFT JOIN empresas e ON f.empresa_id = e.id
        WHERE YEAR(f.data) = %s OR f.recorrente_anual = 1
        ORDER BY MONTH(f.data), DAY(f.data)
    """, [ano]) or []
    
    empresas = db.fetch_all("SELECT id, razao_social FROM empresas WHERE ativo = 1 ORDER BY razao_social") or []
    
    return render_template('industria/config_feriados.html',
                          feriados=feriados,
                          empresas=empresas,
                          ano=ano)


@config_producao_bp.route('/feriados/salvar', methods=['POST'])
@login_required
@admin_required
def salvar_feriado():
    """Salva feriado"""
    db = get_db()
    
    feriado_id = request.form.get('id')
    empresa_id = request.form.get('empresa_id') or None
    data = request.form.get('data')
    descricao = request.form.get('descricao')
    tipo = request.form.get('tipo', 'feriado')
    recorrente = 1 if request.form.get('recorrente_anual') else 0
    
    if not data or not descricao:
        return jsonify({'success': False, 'error': 'Data e descrição são obrigatórios'}), 400
    
    if feriado_id:
        query = """
            UPDATE config_feriados SET
                empresa_id = %s, data = %s, descricao = %s, tipo = %s, recorrente_anual = %s
            WHERE id = %s
        """
        db.execute_query(query, [empresa_id, data, descricao, tipo, recorrente, feriado_id])
    else:
        query = """
            INSERT INTO config_feriados (empresa_id, data, descricao, tipo, recorrente_anual)
            VALUES (%s, %s, %s, %s, %s)
        """
        db.execute_query(query, [empresa_id, data, descricao, tipo, recorrente])
    
    return jsonify({'success': True})


@config_producao_bp.route('/feriados/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_feriado():
    """Remove feriado"""
    db = get_db()
    
    feriado_id = request.form.get('id')
    if not feriado_id:
        return jsonify({'success': False, 'error': 'ID não informado'}), 400
    
    db.execute_query("DELETE FROM config_feriados WHERE id = %s", [feriado_id])
    return jsonify({'success': True})


# =========================================================
# CAPACIDADE POR ETAPA
# =========================================================

@config_producao_bp.route('/capacidade-etapas')
@login_required
@admin_required
def capacidade_etapas():
    """Tela de configuração de capacidade por etapa"""
    db = get_db()
    
    etapas = db.fetch_all("""
        SELECT e.id, e.nome, e.ordem,
               COALESCE(c.capacidade_diaria_lotes, 10) as capacidade_diaria,
               COALESCE(c.capacidade_simultanea, 1) as capacidade_simultanea,
               COALESCE(c.tempo_setup_minutos, 0) as tempo_setup,
               c.observacao
        FROM producao_etapas e
        LEFT JOIN config_capacidade_etapa c ON c.etapa_id = e.id AND c.empresa_id IS NULL
        WHERE e.ativo = 1
        ORDER BY e.ordem
    """) or []
    
    return render_template('industria/config_capacidade_etapas.html', etapas=etapas)


@config_producao_bp.route('/capacidade-etapas/salvar', methods=['POST'])
@login_required
@admin_required
def salvar_capacidade_etapa():
    """Salva capacidade de uma etapa"""
    db = get_db()
    
    etapa_id = request.form.get('etapa_id')
    capacidade_diaria = request.form.get('capacidade_diaria', 10)
    capacidade_simultanea = request.form.get('capacidade_simultanea', 1)
    tempo_setup = request.form.get('tempo_setup', 0)
    observacao = request.form.get('observacao', '')
    
    if not etapa_id:
        return jsonify({'success': False, 'error': 'Etapa não informada'}), 400
    
    query = """
        INSERT INTO config_capacidade_etapa 
        (empresa_id, etapa_id, capacidade_diaria_lotes, capacidade_simultanea, tempo_setup_minutos, observacao)
        VALUES (NULL, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            capacidade_diaria_lotes = %s,
            capacidade_simultanea = %s,
            tempo_setup_minutos = %s,
            observacao = %s,
            updated_at = NOW()
    """
    db.execute_query(query, [
        etapa_id, capacidade_diaria, capacidade_simultanea, tempo_setup, observacao,
        capacidade_diaria, capacidade_simultanea, tempo_setup, observacao
    ])
    
    return jsonify({'success': True})


# =========================================================
# API DE PREVISÃO
# =========================================================

@config_producao_bp.route('/api/previsao/lote/<int:lote_id>')
@login_required
def api_previsao_lote(lote_id):
    """Retorna previsão de conclusão de um lote"""
    service = get_previsao_service()
    result = service.calcular_previsao_lote(lote_id)
    
    if result['previsao']:
        result['previsao'] = result['previsao'].strftime('%d/%m/%Y %H:%M')
    
    return jsonify(result)


@config_producao_bp.route('/api/previsao/op/<int:op_id>')
@login_required
def api_previsao_op(op_id):
    """Retorna previsão de conclusão de uma OP"""
    service = get_previsao_service()
    result = service.calcular_previsao_op(op_id)
    
    if result['previsao']:
        result['previsao'] = result['previsao'].strftime('%d/%m/%Y %H:%M')
    
    return jsonify(result)


@config_producao_bp.route('/api/previsao/orcamento/<int:orcamento_id>')
@login_required
def api_previsao_orcamento(orcamento_id):
    """Retorna previsão de produção para um orçamento"""
    service = get_previsao_service()
    result = service.calcular_previsao_orcamento(orcamento_id)
    
    if result['previsao_producao']:
        result['previsao_producao'] = result['previsao_producao'].strftime('%d/%m/%Y')
    
    return jsonify(result)


@config_producao_bp.route('/api/previsao/calcular', methods=['POST'])
@login_required
def api_calcular_previsao():
    """
    Calcula previsão de produção para uma lista de itens
    Usado para calcular previsão em tempo real no formulário de orçamento
    
    Body JSON:
    {
        "itens": [
            {"produto_id": 1, "quantidade": 10},
            {"produto_id": 2, "quantidade": 5}
        ],
        "dias_transporte": 3
    }
    """
    from flask import request
    from datetime import datetime, timedelta
    
    data = request.get_json() or {}
    itens = data.get('itens', [])
    dias_transporte = int(data.get('dias_transporte', 0))
    
    if not itens:
        return jsonify({
            'sucesso': False,
            'mensagem': 'Nenhum item informado',
            'previsao_producao': None,
            'previsao_entrega': None
        })
    
    service = get_previsao_service()
    db = get_db()
    
    # Calcular tempo total de produção
    tempo_total = 0
    detalhes_itens = []
    
    for item in itens:
        produto_id = item.get('produto_id')
        quantidade = float(item.get('quantidade', 1))
        
        if not produto_id:
            continue
        
        # Buscar nome do produto
        prod = db.fetch_one("SELECT name FROM products WHERE id = %s", [produto_id])
        produto_nome = prod['name'] if prod else f'Produto {produto_id}'
        
        # Calcular tempo do produto
        tempo_produto = service.get_tempo_total_produto(produto_id)
        tempo_item = int(tempo_produto * quantidade)
        tempo_total += tempo_item
        
        detalhes_itens.append({
            'produto_id': produto_id,
            'produto_nome': produto_nome,
            'quantidade': quantidade,
            'tempo_unitario_min': tempo_produto,
            'tempo_total_min': tempo_item
        })
    
    # Estimar fila atual
    try:
        result = db.fetch_one("SELECT AVG(qtd_aguardando) as media FROM vw_resumo_etapas_producao")
        fila_media = float(result['media']) if result and result['media'] else 0
    except:
        fila_media = 0
    
    tempo_fila = int(fila_media * 30)  # 30 min por lote na fila
    tempo_total_com_fila = tempo_total + tempo_fila
    
    # Calcular data de conclusão da produção
    previsao_producao = service.adicionar_minutos_uteis(datetime.now(), tempo_total_com_fila)
    
    # Calcular data de entrega (produção + transporte)
    previsao_entrega = previsao_producao + timedelta(days=dias_transporte) if previsao_producao else None
    
    # Converter para horas para exibição
    horas_producao = tempo_total_com_fila / 60
    dias_producao = horas_producao / 8  # Assumindo 8h/dia
    
    return jsonify({
        'sucesso': True,
        'previsao_producao': previsao_producao.strftime('%Y-%m-%d') if previsao_producao else None,
        'previsao_producao_formatada': previsao_producao.strftime('%d/%m/%Y') if previsao_producao else None,
        'previsao_entrega': previsao_entrega.strftime('%Y-%m-%d') if previsao_entrega else None,
        'previsao_entrega_formatada': previsao_entrega.strftime('%d/%m/%Y') if previsao_entrega else None,
        'tempo_producao_minutos': tempo_total,
        'tempo_fila_minutos': tempo_fila,
        'tempo_total_minutos': tempo_total_com_fila,
        'horas_producao': round(horas_producao, 1),
        'dias_producao': round(dias_producao, 1),
        'dias_transporte': dias_transporte,
        'detalhes_itens': detalhes_itens
    })


@config_producao_bp.route('/api/gargalos')
@login_required
def api_gargalos():
    """Retorna análise de gargalos"""
    service = get_previsao_service()
    gargalos = service.get_analise_gargalos()
    return jsonify(gargalos)


# =========================================================
# DASHBOARD DE PRODUÇÃO (FASE D)
# =========================================================

@config_producao_bp.route('/dashboard')
@login_required
def dashboard_producao():
    """Dashboard de produção com visão de gargalos"""
    db = get_db()
    
    # Tentar buscar etapas da view, se não existir buscar da tabela
    etapas_resumo = []
    try:
        etapas_resumo = db.fetch_all("""
            SELECT * FROM vw_resumo_etapas_producao
            ORDER BY ordem
        """) or []
    except Exception as e:
        print(f"[DASHBOARD] View não existe, buscando etapas base: {e}")
        # Fallback: buscar etapas diretamente
        try:
            etapas_resumo = db.fetch_all("""
                SELECT 
                    e.id AS etapa_id,
                    e.nome AS etapa_nome,
                    e.ordem,
                    0 AS qtd_aguardando,
                    0 AS qtd_em_producao,
                    0 AS qtd_pausados,
                    0 AS qtd_total,
                    0 AS tempo_medio_fila_minutos,
                    10 AS capacidade_diaria,
                    1 AS capacidade_simultanea,
                    'normal' AS status_gargalo
                FROM producao_etapas e
                WHERE e.ativo = 1
                ORDER BY e.ordem
            """) or []
        except Exception as e2:
            print(f"[DASHBOARD] Erro ao buscar etapas: {e2}")
    
    # Calcular totais
    total_aguardando = sum(e.get('qtd_aguardando', 0) or 0 for e in etapas_resumo)
    total_em_producao = sum(e.get('qtd_em_producao', 0) or 0 for e in etapas_resumo)
    total_pausados = sum(e.get('qtd_pausados', 0) or 0 for e in etapas_resumo)
    total_lotes = sum(e.get('qtd_total', 0) or 0 for e in etapas_resumo)
    
    # Contar gargalos
    gargalos_criticos = len([e for e in etapas_resumo if e.get('status_gargalo') == 'critico'])
    gargalos_atencao = len([e for e in etapas_resumo if e.get('status_gargalo') == 'atencao'])
    
    # Buscar OPs em produção com etapa atual
    ops_ativas = []
    try:
        ops_ativas = db.fetch_all("""
            SELECT op.id, op.numero_op, op.produto_id, p.name as produto_nome,
                   op.quantidade, op.status, op.data_prevista,
                   op.data_inicio_producao, op.created_at,
                   c.name as cliente_nome,
                   COUNT(l.id) as qtd_lotes,
                   COALESCE(SUM(CASE WHEN l.status = 'concluido' THEN l.quantidade ELSE 0 END), 0) as qtd_concluida,
                   (SELECT e.nome FROM op_lotes ol 
                    LEFT JOIN producao_etapas e ON ol.etapa_atual_id = e.id 
                    WHERE ol.ordem_producao_id = op.id AND ol.status != 'concluido'
                    ORDER BY e.ordem DESC LIMIT 1) as etapa_atual
            FROM ordens_producao op
            JOIN products p ON op.produto_id = p.id
            LEFT JOIN customers c ON op.cliente_id = c.id
            LEFT JOIN op_lotes l ON l.ordem_producao_id = op.id
            WHERE op.status IN ('em_producao', 'pendente')
            GROUP BY op.id
            ORDER BY op.data_prevista ASC
            LIMIT 20
        """) or []
    except Exception as e:
        print(f"[DASHBOARD] Erro ao buscar OPs: {e}")
    
    # Buscar timeline de lotes por etapa para o Gantt
    timeline_lotes = []
    try:
        timeline_lotes = db.fetch_all("""
            SELECT 
                l.id as lote_id,
                l.ordem_producao_id,
                op.numero_op,
                p.name as produto_nome,
                l.etapa_atual_id,
                e.nome as etapa_nome,
                e.ordem as etapa_ordem,
                l.status as lote_status,
                l.status_operador,
                l.created_at as lote_criado,
                op.data_inicio_producao,
                op.data_prevista,
                TIMESTAMPDIFF(HOUR, COALESCE(op.data_inicio_producao, op.created_at), NOW()) as horas_decorridas,
                TIMESTAMPDIFF(HOUR, NOW(), op.data_prevista) as horas_restantes
            FROM op_lotes l
            JOIN ordens_producao op ON l.ordem_producao_id = op.id
            JOIN products p ON op.produto_id = p.id
            LEFT JOIN producao_etapas e ON l.etapa_atual_id = e.id
            WHERE op.status IN ('em_producao', 'pendente')
              AND l.status NOT IN ('concluido', 'cancelado')
            ORDER BY op.data_prevista, e.ordem
            LIMIT 50
        """) or []
    except Exception as e:
        print(f"[DASHBOARD] Erro ao buscar timeline: {e}")
    
    from datetime import datetime
    return render_template('industria/dashboard_gantt.html',
                          etapas=etapas_resumo,
                          total_aguardando=total_aguardando,
                          total_em_producao=total_em_producao,
                          total_pausados=total_pausados,
                          total_lotes=total_lotes,
                          gargalos_criticos=gargalos_criticos,
                          gargalos_atencao=gargalos_atencao,
                          ops_ativas=ops_ativas,
                          timeline_lotes=timeline_lotes,
                          now=datetime.now)


@config_producao_bp.route('/api/dashboard/refresh')
@login_required
def api_dashboard_refresh():
    """API para refresh automático do dashboard"""
    db = get_db()
    
    # Buscar resumo por etapa
    etapas_resumo = []
    try:
        etapas_resumo = db.fetch_all("""
            SELECT * FROM vw_resumo_etapas_producao
            ORDER BY ordem
        """) or []
    except:
        try:
            etapas_resumo = db.fetch_all("""
                SELECT e.id AS etapa_id, e.nome AS etapa_nome, e.ordem,
                       0 AS qtd_aguardando, 0 AS qtd_em_producao, 0 AS qtd_pausados,
                       0 AS qtd_total, 0 AS tempo_medio_fila_minutos, 'normal' AS status_gargalo
                FROM producao_etapas e WHERE e.ativo = 1 ORDER BY e.ordem
            """) or []
        except:
            pass
    
    # Calcular totais
    totais = {
        'aguardando': sum(e['qtd_aguardando'] or 0 for e in etapas_resumo),
        'em_producao': sum(e['qtd_em_producao'] or 0 for e in etapas_resumo),
        'pausados': sum(e['qtd_pausados'] or 0 for e in etapas_resumo),
        'total': sum(e['qtd_total'] or 0 for e in etapas_resumo),
        'gargalos_criticos': len([e for e in etapas_resumo if e['status_gargalo'] == 'critico']),
        'gargalos_atencao': len([e for e in etapas_resumo if e['status_gargalo'] == 'atencao'])
    }
    
    # Preparar dados das etapas para JSON
    etapas_json = []
    for e in etapas_resumo:
        etapas_json.append({
            'etapa_id': e['etapa_id'],
            'etapa_nome': e['etapa_nome'],
            'ordem': e['ordem'],
            'qtd_aguardando': e['qtd_aguardando'] or 0,
            'qtd_em_producao': e['qtd_em_producao'] or 0,
            'qtd_pausados': e['qtd_pausados'] or 0,
            'qtd_total': e['qtd_total'] or 0,
            'tempo_medio_fila': round(e['tempo_medio_fila_minutos'] or 0),
            'capacidade_diaria': e['capacidade_diaria'],
            'status_gargalo': e['status_gargalo']
        })
    
    return jsonify({
        'totais': totais,
        'etapas': etapas_json,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    })
