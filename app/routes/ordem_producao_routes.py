"""
Blueprint para Gestão de Ordens de Produção Industrial
Módulo Indústria - Sistema de Templates Inteligentes
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify

try:
    from app.database import get_db
    from app.utils.auth import login_required
    from app.utils.search_utils import parse_star_search, build_multi_part_like_where
except ImportError:
    # Execução no modo main_mysql.py (imports relativos ao diretório /app)
    from database import get_db
    from functools import wraps

    def login_required(f):
        """Requer login para acessar (modo main_mysql.py / sem app.utils.auth)."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'username' not in session:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    from utils.search_utils import parse_star_search, build_multi_part_like_where

from functools import wraps
try:
    from utils.permissoes_helper import tem_permissao
except ImportError:
    from app.utils.permissoes_helper import tem_permissao

# Decorators para permissões granulares de Indústria
def industria_ops_visualizar_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Por favor, faça login para acessar esta página.', 'danger')
            return redirect(url_for('login'))
        if not tem_permissao('industria.ops', 'visualizar'):
            flash('Você não tem permissão para visualizar ordens de produção.', 'danger')
            return redirect(url_for('bem_vindo'))
        return f(*args, **kwargs)
    return decorated_function

def industria_ops_criar_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Por favor, faça login para acessar esta página.', 'danger')
            return redirect(url_for('login'))
        if not tem_permissao('industria.ops', 'criar'):
            flash('Você não tem permissão para criar ordens de produção.', 'danger')
            return redirect(url_for('ordem_producao.listar_ops'))
        return f(*args, **kwargs)
    return decorated_function

def industria_ops_editar_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Por favor, faça login para acessar esta página.', 'danger')
            return redirect(url_for('login'))
        if not tem_permissao('industria.ops', 'editar'):
            flash('Você não tem permissão para editar ordens de produção.', 'danger')
            return redirect(url_for('ordem_producao.listar_ops'))
        return f(*args, **kwargs)
    return decorated_function

def industria_ops_excluir_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Por favor, faça login para acessar esta página.', 'danger')
            return redirect(url_for('login'))
        if not tem_permissao('industria.ops', 'excluir'):
            flash('Você não tem permissão para excluir ordens de produção.', 'danger')
            return redirect(url_for('ordem_producao.listar_ops'))
        return f(*args, **kwargs)
    return decorated_function
from datetime import datetime, date
from decimal import Decimal
from decimal import InvalidOperation

# Helper Kardex
try:
    from utils.estoque_helper import registrar_movimentacao
except ImportError:
    registrar_movimentacao = None

# Criar blueprint
ordem_producao_bp = Blueprint('ordem_producao', __name__, url_prefix='/industria/ordem-producao')


@ordem_producao_bp.route('/producao/gantt')
@login_required
def producao_gantt():
    """Tela de produção estilo Kanban (cards) com troca de etapa."""
    db = get_db()

    status_filtro = (request.args.get('status') or '').strip()
    etapa_filtro = (request.args.get('etapa_id') or '').strip()
    grupo_etapas_filtro = (request.args.get('grupo_etapas_id') or '').strip()
    q_filtro = (request.args.get('q') or '').strip()
    etapas_visiveis_raw = request.args.getlist('etapas')
    etapas_visiveis = []
    for v in etapas_visiveis_raw:
        try:
            etapas_visiveis.append(int(v))
        except Exception:
            pass

    grupos_etapas = db.fetch_all("""
        SELECT id, nome, ordem, ativo, cor_hex, descricao
        FROM producao_etapas_grupos
        WHERE ativo = 1
        ORDER BY ordem, id
    """) or []

    etapas_params = []
    etapas_where = "WHERE e.ativo = 1"
    if grupo_etapas_filtro:
        etapas_where += " AND e.grupo_etapas_id = %s"
        etapas_params.append(grupo_etapas_filtro)

    etapas = db.fetch_all(f"""
        SELECT e.id, e.nome, e.ordem, e.cor_hex, e.icone, e.descricao,
               e.grupo_etapas_id,
               g.nome AS grupo_etapas_nome,
               g.ordem AS grupo_etapas_ordem,
               g.cor_hex AS grupo_etapas_cor_hex,
               g.descricao AS grupo_etapas_descricao
        FROM producao_etapas e
        LEFT JOIN producao_etapas_grupos g ON g.id = e.grupo_etapas_id
        {etapas_where}
        ORDER BY e.ordem, e.id
    """, tuple(etapas_params) if etapas_params else None) or []

    # Lista completa (para dropdown de colunas) também respeita filtro de grupo
    etapas_todas = etapas

    try:
        query = """
            SELECT
                v.id,
                v.numero_op,
                v.cliente_nome,
                v.produto_nome,
                v.status,
                v.data_solicitacao,
                v.data_prevista,
                v.created_at,
                op.data_inicio_producao,
                op.data_conclusao,
                op.etapa_atual_id,
                e.nome AS etapa_nome,
                e.cor_hex AS etapa_cor_hex,
                e.icone AS etapa_icone
            FROM vw_ordens_producao_resumo v
            INNER JOIN ordens_producao op ON op.id = v.id
            LEFT JOIN producao_etapas e ON e.id = op.etapa_atual_id
            WHERE 1=1
        """
        params = []

        if status_filtro:
            query += " AND v.status = %s"
            params.append(status_filtro)
        else:
            # Padrão: não exibir concluídas/canceladas no Gantt (apenas se filtrar explicitamente)
            query += " AND v.status NOT IN ('concluida', 'cancelada')"

        if etapa_filtro:
            query += " AND op.etapa_atual_id = %s"
            params.append(etapa_filtro)

        # Filtro de colunas visíveis do Kanban (multi-seleção)
        # 0 = Sem Etapa (NULL)
        if etapas_visiveis:
            etapas_sem = [x for x in etapas_visiveis if x != 0]
            inclui_sem_etapa = 0 in etapas_visiveis

            if etapas_sem and inclui_sem_etapa:
                placeholders = ','.join(['%s'] * len(etapas_sem))
                query += f" AND (op.etapa_atual_id IN ({placeholders}) OR op.etapa_atual_id IS NULL)"
                params.extend(etapas_sem)
            elif etapas_sem:
                placeholders = ','.join(['%s'] * len(etapas_sem))
                query += f" AND op.etapa_atual_id IN ({placeholders})"
                params.extend(etapas_sem)
            elif inclui_sem_etapa:
                query += " AND op.etapa_atual_id IS NULL"

        if q_filtro:
            query += " AND (v.cliente_nome LIKE %s OR v.produto_nome LIKE %s OR v.numero_op LIKE %s)"
            like = f"%{q_filtro}%"
            params.extend([like, like, like])

        query += " ORDER BY COALESCE(v.data_prevista, v.data_solicitacao, v.created_at) ASC, v.id DESC"

        # Buscar lotes (subdivisões) para permitir avanço parcial entre etapas
        query2 = """
            SELECT
                l.id AS lote_id,
                l.sequencia AS lote_sequencia,
                l.quantidade AS lote_quantidade,
                l.align_side AS lote_align_side,
                l.etapa_atual_id AS lote_etapa_atual_id,
                l.status_operador,
                l.arara,
                l.data_atribuicao,
                l.data_inicio_operador,
                l.data_fim_operador,
                u_lider.name AS lider_nome,
                u_operador.name AS operador_nome,
                u_atribuidor.name AS atribuido_por_nome,
                v.id AS op_id,
                v.numero_op,
                v.cliente_nome,
                v.produto_nome,
                v.status,
                v.data_solicitacao,
                v.data_prevista,
                v.created_at,
                op.data_inicio_producao,
                op.data_conclusao,
                op.quantidade AS op_quantidade_total,
                e.nome AS etapa_nome,
                e.cor_hex AS etapa_cor_hex,
                e.icone AS etapa_icone,
                og.id AS grupo_id,
                o.id AS orcamento_id,
                o.numero AS orcamento_numero,
                (SELECT MAX(log.created_at) 
                 FROM op_lotes_etapas_log log 
                 WHERE log.lote_id = l.id 
                   AND log.etapa_nova_id = l.etapa_atual_id) AS data_chegada_etapa,
                pp.id AS pausa_id,
                pp.inicio AS pausa_inicio,
                ppm.nome AS pausa_motivo,
                ppm.tipo AS pausa_tipo,
                ppm.icone AS pausa_icone,
                ppm.cor_hex AS pausa_cor
            FROM op_lotes l
            INNER JOIN ordens_producao op ON op.id = l.ordem_producao_id
            INNER JOIN vw_ordens_producao_resumo v ON v.id = op.id
            LEFT JOIN producao_etapas e ON e.id = l.etapa_atual_id
            LEFT JOIN orcamento_op_itens oi ON oi.ordem_producao_id = v.id
            LEFT JOIN orcamento_op_grupos og ON og.id = oi.grupo_id
            LEFT JOIN orcamentos o ON o.id = og.orcamento_id
            LEFT JOIN lider_operadores lo ON lo.operador_id = l.operador_id
            LEFT JOIN users u_lider ON u_lider.id = lo.lider_id
            LEFT JOIN users u_operador ON u_operador.id = l.operador_id
            LEFT JOIN users u_atribuidor ON u_atribuidor.id = l.atribuido_por_id
            LEFT JOIN producao_pausas pp ON pp.lote_id = l.id AND pp.fim IS NULL
            LEFT JOIN producao_pausas_motivos ppm ON ppm.id = pp.motivo_id
            WHERE 1=1
        """

        # reutilizar filtros já aplicados
        # (montar novamente para manter o mesmo comportamento)
        params2 = []

        if status_filtro:
            query2 += " AND v.status = %s"
            params2.append(status_filtro)
        else:
            # Padrão: não exibir concluídas/canceladas no Gantt (apenas se filtrar explicitamente)
            query2 += " AND v.status NOT IN ('concluida', 'cancelada')"

        if etapa_filtro:
            query2 += " AND l.etapa_atual_id = %s"
            params2.append(etapa_filtro)

        if etapas_visiveis:
            etapas_sem = [x for x in etapas_visiveis if x != 0]
            if etapas_sem:
                placeholders = ','.join(['%s'] * len(etapas_sem))
                query2 += f" AND l.etapa_atual_id IN ({placeholders})"
                params2.extend(etapas_sem)

        if q_filtro:
            query2 += " AND (v.cliente_nome LIKE %s OR v.produto_nome LIKE %s OR v.numero_op LIKE %s)"
            like = f"%{q_filtro}%"
            params2.extend([like, like, like])

        query2 += " ORDER BY COALESCE(o.numero, '') DESC, v.id DESC"

        lotes = db.fetch_all(query2, tuple(params2) if params2 else None) or []

        # Filtrar lista de etapas (colunas) para renderização
        if etapas_visiveis:
            etapas_render = [e for e in etapas if int(e.get('id')) in etapas_visiveis]
        else:
            etapas_render = etapas

        # Cabeçalho agrupado (Grupo de Etapas -> qtd de colunas)
        grupos_header = []
        atual = None
        for e in etapas_render:
            gid = e.get('grupo_etapas_id')
            gnome = e.get('grupo_etapas_nome') or 'Sem Grupo'
            gcor = e.get('grupo_etapas_cor_hex')
            gdesc = e.get('grupo_etapas_descricao')
            key = str(gid) if gid else '0'
            if (not atual) or (atual.get('key') != key):
                atual = {'key': key, 'nome': gnome, 'cor_hex': gcor, 'descricao': gdesc, 'count': 0}
                grupos_header.append(atual)
            atual['count'] += 1

        # Montar grupos (linhas) e matriz grupo x etapa
        grupos = {}
        for it in lotes:
            gid = it.get('grupo_id')
            if not gid:
                # Se OP não tiver vínculo, não entra na visão por Grupo
                continue
            if gid not in grupos:
                grupos[gid] = {
                    'grupo_id': gid,
                    'orcamento_id': it.get('orcamento_id'),
                    'orcamento_numero': it.get('orcamento_numero'),
                    'cliente_nome': it.get('cliente_nome')
                }

        grupos_lista = list(grupos.values())
        grupos_lista.sort(key=lambda x: (x.get('orcamento_numero') or ''), reverse=True)

        ops_por_grupo_etapa = {}
        for g in grupos_lista:
            ops_por_grupo_etapa[g['grupo_id']] = {}
            for et in etapas_render:
                ops_por_grupo_etapa[g['grupo_id']][et['id']] = []

        for it in lotes:
            gid = it.get('grupo_id')
            etid = it.get('lote_etapa_atual_id')
            if not gid or not etid:
                continue
            if gid not in ops_por_grupo_etapa:
                continue
            if etid not in ops_por_grupo_etapa[gid]:
                continue
            ops_por_grupo_etapa[gid][etid].append(it)

        return render_template(
            'industria/producao_gantt.html',
            lotes=lotes,
            etapas=etapas_render,
            etapas_todas=etapas_todas,
            etapas_visiveis=etapas_visiveis,
            grupos_etapas=grupos_etapas,
            grupo_etapas_filtro=grupo_etapas_filtro,
            grupos_header=grupos_header,
            grupos=grupos_lista,
            ops_por_grupo_etapa=ops_por_grupo_etapa,
            status_filtro=status_filtro,
            etapa_filtro=etapa_filtro,
            q_filtro=q_filtro,
            full_width=True,
            menu_collapsed=True,
        )

    except Exception as e:
        flash(f'Erro ao carregar produção: {str(e)}', 'danger')
        return render_template(
            'industria/producao_gantt.html',
            lotes=[],
            etapas=etapas,
            etapas_todas=etapas,
            etapas_visiveis=etapas_visiveis,
            grupos_etapas=grupos_etapas,
            grupo_etapas_filtro=grupo_etapas_filtro,
            grupos_header=[],
            grupos=[],
            ops_por_grupo_etapa={},
            status_filtro=status_filtro,
            etapa_filtro=etapa_filtro,
            q_filtro=q_filtro,
            full_width=True,
            menu_collapsed=True,
        )


@ordem_producao_bp.route('/producao/gantt-v2')
@login_required
def producao_gantt_v2():
    db = get_db()

    status_filtro = (request.args.get('status') or '').strip()
    etapa_filtro = (request.args.get('etapa_id') or '').strip()
    grupo_etapas_filtro = (request.args.get('grupo_etapas_id') or '').strip()
    q_filtro = (request.args.get('q') or '').strip()
    etapas_visiveis_raw = request.args.getlist('etapas')
    etapas_visiveis = []
    for v in etapas_visiveis_raw:
        try:
            etapas_visiveis.append(int(v))
        except Exception:
            pass

    grupos_etapas = db.fetch_all("""
        SELECT id, nome, ordem, ativo, cor_hex, descricao
        FROM producao_etapas_grupos
        WHERE ativo = 1
        ORDER BY ordem, id
    """) or []

    etapas_params = []
    etapas_where = "WHERE e.ativo = 1"
    if grupo_etapas_filtro:
        etapas_where += " AND e.grupo_etapas_id = %s"
        etapas_params.append(grupo_etapas_filtro)

    etapas = db.fetch_all(f"""
        SELECT e.id, e.nome, e.ordem, e.cor_hex, e.icone, e.descricao,
               e.grupo_etapas_id,
               g.nome AS grupo_etapas_nome,
               g.ordem AS grupo_etapas_ordem,
               g.cor_hex AS grupo_etapas_cor_hex,
               g.descricao AS grupo_etapas_descricao
        FROM producao_etapas e
        LEFT JOIN producao_etapas_grupos g ON g.id = e.grupo_etapas_id
        {etapas_where}
        ORDER BY e.ordem, e.id
    """, tuple(etapas_params) if etapas_params else None) or []

    etapas_todas = etapas

    try:
        query2 = """
            SELECT
                l.id AS lote_id,
                l.sequencia AS lote_sequencia,
                l.quantidade AS lote_quantidade,
                l.align_side AS lote_align_side,
                l.etapa_atual_id AS lote_etapa_atual_id,
                v.id AS op_id,
                v.numero_op,
                v.cliente_nome,
                v.produto_nome,
                v.status,
                v.data_solicitacao,
                v.data_prevista,
                v.created_at,
                op.data_inicio_producao,
                op.data_conclusao,
                op.quantidade AS op_quantidade_total,
                e.nome AS etapa_nome,
                e.cor_hex AS etapa_cor_hex,
                e.icone AS etapa_icone,
                og.id AS grupo_id,
                o.id AS orcamento_id,
                o.numero AS orcamento_numero
            FROM op_lotes l
            INNER JOIN ordens_producao op ON op.id = l.ordem_producao_id
            INNER JOIN vw_ordens_producao_resumo v ON v.id = op.id
            LEFT JOIN producao_etapas e ON e.id = l.etapa_atual_id
            LEFT JOIN orcamento_op_itens oi ON oi.ordem_producao_id = v.id
            LEFT JOIN orcamento_op_grupos og ON og.id = oi.grupo_id
            LEFT JOIN orcamentos o ON o.id = og.orcamento_id
            WHERE 1=1
        """

        params2 = []
        if status_filtro:
            query2 += " AND v.status = %s"
            params2.append(status_filtro)
        else:
            query2 += " AND v.status NOT IN ('concluida', 'cancelada')"

        if etapa_filtro:
            query2 += " AND l.etapa_atual_id = %s"
            params2.append(etapa_filtro)

        if etapas_visiveis:
            etapas_sem = [x for x in etapas_visiveis if x != 0]
            if etapas_sem:
                placeholders = ','.join(['%s'] * len(etapas_sem))
                query2 += f" AND l.etapa_atual_id IN ({placeholders})"
                params2.extend(etapas_sem)

        if q_filtro:
            query2 += " AND (v.cliente_nome LIKE %s OR v.produto_nome LIKE %s OR v.numero_op LIKE %s)"
            like = f"%{q_filtro}%"
            params2.extend([like, like, like])

        query2 += " ORDER BY COALESCE(o.numero, '') DESC, v.id DESC"

        lotes = db.fetch_all(query2, tuple(params2) if params2 else None) or []

        if etapas_visiveis:
            etapas_render = [e for e in etapas if int(e.get('id')) in etapas_visiveis]
        else:
            etapas_render = etapas

        grupos_header = []
        atual = None
        for e in etapas_render:
            gid = e.get('grupo_etapas_id')
            gnome = e.get('grupo_etapas_nome') or 'Sem Grupo'
            gcor = e.get('grupo_etapas_cor_hex')
            gdesc = e.get('grupo_etapas_descricao')
            key = str(gid) if gid else '0'
            if (not atual) or (atual.get('key') != key):
                atual = {'key': key, 'nome': gnome, 'cor_hex': gcor, 'descricao': gdesc, 'count': 0}
                grupos_header.append(atual)
            atual['count'] += 1

        grupos = {}
        for it in lotes:
            gid = it.get('grupo_id')
            if not gid:
                continue
            if gid not in grupos:
                grupos[gid] = {
                    'grupo_id': gid,
                    'orcamento_id': it.get('orcamento_id'),
                    'orcamento_numero': it.get('orcamento_numero'),
                    'cliente_nome': it.get('cliente_nome')
                }

        grupos_lista = list(grupos.values())
        grupos_lista.sort(key=lambda x: (x.get('orcamento_numero') or ''), reverse=True)

        etapa_pos = {int(e.get('id')): idx for idx, e in enumerate(etapas_render)}

        ops_por_grupo = {}
        for it in lotes:
            gid = it.get('grupo_id')
            etid = it.get('lote_etapa_atual_id')
            op_id = it.get('op_id')
            if not gid or not etid or not op_id:
                continue
            try:
                etid_int = int(etid)
            except Exception:
                continue
            if etid_int not in etapa_pos:
                continue

            if gid not in ops_por_grupo:
                ops_por_grupo[gid] = {}
            if op_id not in ops_por_grupo[gid]:
                ops_por_grupo[gid][op_id] = {
                    'op_id': op_id,
                    'numero_op': it.get('numero_op'),
                    'cliente_nome': it.get('cliente_nome'),
                    'produto_nome': it.get('produto_nome'),
                    'status': it.get('status'),
                    'op_quantidade_total': it.get('op_quantidade_total'),
                    'op_url': url_for('ordem_producao.visualizar_op', id=op_id),
                    'etapas_data': {},
                    'span_inicio': etapa_pos[etid_int],
                    'span_fim': etapa_pos[etid_int],
                }

            opref = ops_por_grupo[gid][op_id]
            if etid_int not in opref['etapas_data']:
                opref['etapas_data'][etid_int] = {
                    'qty_total': Decimal('0'),
                    'lotes': []
                }

            try:
                qtd = Decimal(str(it.get('lote_quantidade') or 0))
            except Exception:
                qtd = Decimal('0')

            opref['etapas_data'][etid_int]['qty_total'] += qtd
            opref['etapas_data'][etid_int]['lotes'].append(it)

            pos = etapa_pos[etid_int]
            if pos < opref['span_inicio']:
                opref['span_inicio'] = pos
            if pos > opref['span_fim']:
                opref['span_fim'] = pos

        for gid, opsmap in (ops_por_grupo or {}).items():
            ops_por_grupo[gid] = list(opsmap.values())

        return render_template(
            'industria/producao_gantt_v2.html',
            lotes=lotes,
            etapas=etapas_render,
            etapas_todas=etapas_todas,
            etapas_visiveis=etapas_visiveis,
            grupos_etapas=grupos_etapas,
            grupo_etapas_filtro=grupo_etapas_filtro,
            grupos_header=grupos_header,
            grupos=grupos_lista,
            ops_por_grupo=ops_por_grupo,
            status_filtro=status_filtro,
            etapa_filtro=etapa_filtro,
            q_filtro=q_filtro,
            full_width=True,
            menu_collapsed=True,
        )

    except Exception as e:
        flash(f'Erro ao carregar produção: {str(e)}', 'danger')
        return render_template(
            'industria/producao_gantt_v2.html',
            lotes=[],
            etapas=etapas,
            etapas_todas=etapas,
            etapas_visiveis=etapas_visiveis,
            grupos_etapas=grupos_etapas,
            grupo_etapas_filtro=grupo_etapas_filtro,
            grupos_header=[],
            grupos=[],
            ops_por_grupo={},
            status_filtro=status_filtro,
            etapa_filtro=etapa_filtro,
            q_filtro=q_filtro,
            full_width=True,
            menu_collapsed=True,
        )


@ordem_producao_bp.route('/etapas')
@login_required
def etapas_lista():
    """Lista etapas de produção (CRUD básico)."""
    db = get_db()
    try:
        etapas = db.fetch_all("""
            SELECT e.id, e.nome, e.ordem, e.ativo, e.cor_hex, e.icone, e.descricao, e.grupo_etapas_id,
                   g.nome AS grupo_nome,
                   e.operador_padrao_id,
                   u.name AS operador_nome
            FROM producao_etapas e
            LEFT JOIN producao_etapas_grupos g ON g.id = e.grupo_etapas_id
            LEFT JOIN users u ON u.id = e.operador_padrao_id
            ORDER BY e.ordem, e.id
        """) or []
        return render_template('industria/producao_etapas_lista.html', etapas=etapas)
    except Exception as e:
        flash(f'Erro ao carregar etapas: {str(e)}', 'danger')
        return render_template('industria/producao_etapas_lista.html', etapas=[])


@ordem_producao_bp.route('/etapas/grupos')
@login_required
def etapas_grupos_lista():
    """Lista grupos de etapas (CRUD básico)."""
    db = get_db()
    try:
        grupos = db.fetch_all("""
            SELECT id, nome, ordem, ativo, cor_hex, descricao
            FROM producao_etapas_grupos
            ORDER BY ordem, id
        """) or []
        return render_template('industria/producao_etapas_grupos_lista.html', grupos=grupos)
    except Exception as e:
        flash(f'Erro ao carregar grupos: {str(e)}', 'danger')
        return render_template('industria/producao_etapas_grupos_lista.html', grupos=[])


@ordem_producao_bp.route('/etapas/grupos/novo', methods=['GET', 'POST'])
@login_required
def etapas_grupos_novo():
    """Cria um novo grupo de etapas."""
    db = get_db()
    if request.method == 'POST':
        try:
            nome = (request.form.get('nome') or '').strip()
            ordem = request.form.get('ordem') or 0
            ativo = 1 if (request.form.get('ativo') or '1') == '1' else 0
            cor_hex = (request.form.get('cor_hex') or '').strip() or None
            descricao = (request.form.get('descricao') or '').strip() or None

            if not nome:
                flash('Nome é obrigatório.', 'warning')
                return render_template('industria/producao_etapas_grupos_form.html', grupo=None)

            db.insert(
                "INSERT INTO producao_etapas_grupos (nome, ordem, ativo, cor_hex, descricao) VALUES (%s, %s, %s, %s, %s)",
                (nome, ordem, ativo, cor_hex, descricao)
            )
            flash('Grupo criado com sucesso!', 'success')
            return redirect(url_for('ordem_producao.etapas_grupos_lista'))
        except Exception as e:
            flash(f'Erro ao criar grupo: {str(e)}', 'danger')

    return render_template('industria/producao_etapas_grupos_form.html', grupo=None)


@ordem_producao_bp.route('/etapas/grupos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def etapas_grupos_editar(id):
    """Edita um grupo de etapas."""
    db = get_db()
    grupo = db.fetch_one("SELECT id, nome, ordem, ativo, cor_hex, descricao FROM producao_etapas_grupos WHERE id = %s", (id,))
    if not grupo:
        flash('Grupo não encontrado.', 'warning')
        return redirect(url_for('ordem_producao.etapas_grupos_lista'))

    if request.method == 'POST':
        try:
            nome = (request.form.get('nome') or '').strip()
            ordem = request.form.get('ordem') or 0
            ativo = 1 if (request.form.get('ativo') or '1') == '1' else 0
            cor_hex = (request.form.get('cor_hex') or '').strip() or None
            descricao = (request.form.get('descricao') or '').strip() or None

            if not nome:
                flash('Nome é obrigatório.', 'warning')
                return render_template('industria/producao_etapas_grupos_form.html', grupo=grupo)

            db.update(
                "UPDATE producao_etapas_grupos SET nome=%s, ordem=%s, ativo=%s, cor_hex=%s, descricao=%s, updated_at=NOW() WHERE id=%s",
                (nome, ordem, ativo, cor_hex, descricao, id)
            )
            flash('Grupo atualizado com sucesso!', 'success')
            return redirect(url_for('ordem_producao.etapas_grupos_lista'))
        except Exception as e:
            flash(f'Erro ao atualizar grupo: {str(e)}', 'danger')

    return render_template('industria/producao_etapas_grupos_form.html', grupo=grupo)


@ordem_producao_bp.route('/etapas/grupos/toggle/<int:id>', methods=['POST'])
@login_required
def etapas_grupos_toggle(id):
    """Ativa/desativa um grupo de etapas."""
    db = get_db()
    try:
        grupo = db.fetch_one("SELECT id, ativo FROM producao_etapas_grupos WHERE id=%s", (id,))
        if not grupo:
            flash('Grupo não encontrado.', 'warning')
            return redirect(url_for('ordem_producao.etapas_grupos_lista'))

        novo_ativo = 0 if int(grupo.get('ativo') or 0) == 1 else 1
        db.execute_query("UPDATE producao_etapas_grupos SET ativo=%s, updated_at=NOW() WHERE id=%s", (novo_ativo, id))
        flash('Grupo atualizado!', 'success')
    except Exception as e:
        flash(f'Erro ao alterar grupo: {str(e)}', 'danger')
    return redirect(url_for('ordem_producao.etapas_grupos_lista'))


@ordem_producao_bp.route('/etapas/nova', methods=['GET', 'POST'])
@login_required
def etapas_nova():
    """Cria uma nova etapa."""
    db = get_db()
    grupos_etapas = db.fetch_all("""
        SELECT id, nome
        FROM producao_etapas_grupos
        WHERE ativo = 1
        ORDER BY ordem, id
    """) or []
    if request.method == 'POST':
        try:
            nome = (request.form.get('nome') or '').strip()
            ordem = request.form.get('ordem') or 0
            ativo = 1 if (request.form.get('ativo') or '1') == '1' else 0
            cor_hex = (request.form.get('cor_hex') or '').strip() or None
            icone = (request.form.get('icone') or '').strip() or None
            descricao = (request.form.get('descricao') or '').strip() or None
            grupo_etapas_id = (request.form.get('grupo_etapas_id') or '').strip() or None

            if not nome:
                flash('Nome é obrigatório.', 'warning')
                return render_template('industria/producao_etapas_form.html', etapa=None, grupos_etapas=grupos_etapas)

            db.insert(
                "INSERT INTO producao_etapas (nome, ordem, ativo, cor_hex, icone, descricao, grupo_etapas_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (nome, ordem, ativo, cor_hex, icone, descricao, grupo_etapas_id)
            )
            flash('Etapa criada com sucesso!', 'success')
            return redirect(url_for('ordem_producao.etapas_lista'))
        except Exception as e:
            flash(f'Erro ao criar etapa: {str(e)}', 'danger')

    return render_template('industria/producao_etapas_form.html', etapa=None, grupos_etapas=grupos_etapas)


@ordem_producao_bp.route('/etapas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def etapas_editar(id):
    """Edita uma etapa."""
    db = get_db()
    etapa = db.fetch_one("SELECT id, nome, ordem, ativo, cor_hex, icone, descricao, grupo_etapas_id, operador_padrao_id FROM producao_etapas WHERE id = %s", (id,))
    if not etapa:
        flash('Etapa não encontrada.', 'warning')
        return redirect(url_for('ordem_producao.etapas_lista'))

    grupos_etapas = db.fetch_all("""
        SELECT id, nome
        FROM producao_etapas_grupos
        WHERE ativo = 1
        ORDER BY ordem, id
    """) or []
    
    # Buscar operadores (usuários com eh_operador = 1)
    operadores = db.fetch_all("""
        SELECT id, name FROM users 
        WHERE eh_operador = 1 AND status = 'active'
        ORDER BY name
    """) or []

    if request.method == 'POST':
        try:
            nome = (request.form.get('nome') or '').strip()
            ordem = request.form.get('ordem') or 0
            ativo = 1 if (request.form.get('ativo') or '1') == '1' else 0
            cor_hex = (request.form.get('cor_hex') or '').strip() or None
            icone = (request.form.get('icone') or '').strip() or None
            grupo_etapas_id = (request.form.get('grupo_etapas_id') or '').strip() or None
            descricao = (request.form.get('descricao') or '').strip() or None
            operador_padrao_id = (request.form.get('operador_padrao_id') or '').strip() or None

            if not nome:
                flash('Nome é obrigatório.', 'warning')
                return render_template('industria/producao_etapas_form.html', etapa=etapa, grupos_etapas=grupos_etapas, operadores=operadores)

            db.update(
                "UPDATE producao_etapas SET nome=%s, ordem=%s, ativo=%s, cor_hex=%s, icone=%s, descricao=%s, grupo_etapas_id=%s, operador_padrao_id=%s WHERE id=%s",
                (nome, ordem, ativo, cor_hex, icone, descricao, grupo_etapas_id, operador_padrao_id, id)
            )
            flash('Etapa atualizada com sucesso!', 'success')
            return redirect(url_for('ordem_producao.etapas_lista'))
        except Exception as e:
            flash(f'Erro ao atualizar etapa: {str(e)}', 'danger')

    return render_template('industria/producao_etapas_form.html', etapa=etapa, grupos_etapas=grupos_etapas, operadores=operadores)


@ordem_producao_bp.route('/etapas/toggle/<int:id>', methods=['POST'])
@login_required
def etapas_toggle(id):
    """Ativa/desativa uma etapa."""
    db = get_db()
    try:
        etapa = db.fetch_one("SELECT id, ativo FROM producao_etapas WHERE id=%s", (id,))
        if not etapa:
            flash('Etapa não encontrada.', 'warning')
            return redirect(url_for('ordem_producao.etapas_lista'))

        novo_ativo = 0 if int(etapa.get('ativo') or 0) == 1 else 1
        db.execute_query("UPDATE producao_etapas SET ativo=%s WHERE id=%s", (novo_ativo, id))
        flash('Etapa atualizada!', 'success')
    except Exception as e:
        flash(f'Erro ao alterar etapa: {str(e)}', 'danger')
    return redirect(url_for('ordem_producao.etapas_lista'))


def _aplicar_template_em_op(db, op_id, template_id):
    """Aplica um template na OP: limpa itens atuais, copia itens do template multiplicando pela quantidade do produto final."""
    op = db.fetch_one("SELECT id, produto_id, quantidade FROM ordens_producao WHERE id = %s", (op_id,))
    if not op:
        raise Exception('OP não encontrada')

    qtd_final = Decimal(str(op.get('quantidade') or 0))
    if qtd_final <= 0:
        qtd_final = Decimal('1')

    # Buscar itens do template
    itens = db.fetch_all("""
        SELECT tipo_item, produto_id, descricao, quantidade, unidade_medida, custo_unitario_base
        FROM produto_template_itens
        WHERE template_id = %s
        ORDER BY tipo_item, id
    """, (template_id,)) or []

    # Limpar itens atuais
    db.execute_query("DELETE FROM ordem_producao_itens WHERE ordem_producao_id = %s", (op_id,))

    custo_total_atual = Decimal('0')
    for it in itens:
        prod = db.fetch_one("SELECT name, unit_measure, cost_price FROM products WHERE id = %s", (it['produto_id'],))
        if not prod:
            continue

        qtd_base = Decimal(str(it.get('quantidade') or 0))
        qtd_item = (qtd_base * qtd_final).quantize(Decimal('0.0001'))
        custo_unit_atual = Decimal(str(prod.get('cost_price') or 0))
        custo_total_item = (qtd_item * custo_unit_atual).quantize(Decimal('0.01'))
        custo_total_atual += custo_total_item

        db.insert("""
            INSERT INTO ordem_producao_itens (
                ordem_producao_id, tipo_item, produto_id, descricao,
                quantidade, unidade_medida, custo_unitario_template,
                custo_unitario_atual, custo_total, veio_template
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
        """, (
            op_id,
            it['tipo_item'],
            it['produto_id'],
            (it.get('descricao') or prod.get('name')),
            str(qtd_item),
            (it.get('unidade_medida') or prod.get('unit_measure')),
            it.get('custo_unitario_base'),
            str(custo_unit_atual),
            str(custo_total_item)
        ))

    template = db.fetch_one("""
        SELECT id, custo_total_base
        FROM produto_templates_producao
        WHERE id = %s
    """, (template_id,))

    db.execute_query("""
        UPDATE ordens_producao
        SET usou_template = 1,
            template_usado_id = %s,
            custo_total_template = %s,
            custo_total_atual = %s
        WHERE id = %s
    """, (
        template_id,
        str((template or {}).get('custo_total_base') or 0),
        str(custo_total_atual),
        op_id
    ))


def _criar_template_a_partir_op(db, op_id):
    """Cria um template (ativo) a partir dos itens atuais da OP e retorna o template_id."""
    op = db.fetch_one("SELECT id, produto_id, quantidade, numero_op FROM ordens_producao WHERE id = %s", (op_id,))
    if not op:
        raise Exception('OP não encontrada')

    produto_id = op.get('produto_id')
    if not produto_id:
        raise Exception('OP sem produto final')

    qtd_final = Decimal(str(op.get('quantidade') or 0))
    if qtd_final <= 0:
        qtd_final = Decimal('1')

    # Itens atuais da OP
    itens = db.fetch_all("""
        SELECT tipo_item, produto_id, descricao, quantidade, unidade_medida, custo_unitario_atual
        FROM ordem_producao_itens
        WHERE ordem_producao_id = %s
        ORDER BY tipo_item, id
    """, (op_id,)) or []

    if not itens:
        raise Exception('A OP não possui itens para gerar um template.')

    # Próxima versão
    versao_atual = db.fetch_one(
        "SELECT MAX(versao) AS v FROM produto_templates_producao WHERE produto_id = %s",
        (produto_id,)
    )
    prox_versao = int((versao_atual or {}).get('v') or 0) + 1

    # Desativar template ativo anterior (se existir)
    db.execute_query(
        "UPDATE produto_templates_producao SET ativo = 0 WHERE produto_id = %s AND ativo = 1",
        (produto_id,)
    )

    nome_template = f"Template (OP {op.get('numero_op')})" if op.get('numero_op') else "Template gerado da OP"

    # Custo base: soma dos custos base por 1 unidade do produto final
    custo_total_base = Decimal('0')
    itens_normalizados = []
    for it in itens:
        qtd_op = Decimal(str(it.get('quantidade') or 0))
        qtd_base = (qtd_op / qtd_final).quantize(Decimal('0.0001'))
        custo_unit = Decimal(str(it.get('custo_unitario_atual') or 0))
        custo_total_item = (qtd_base * custo_unit).quantize(Decimal('0.01'))
        custo_total_base += custo_total_item
        itens_normalizados.append((it, qtd_base, custo_unit, custo_total_item))

    template_id = db.insert("""
        INSERT INTO produto_templates_producao (
            produto_id, versao, nome_template, custo_total_base, ativo, created_by
        ) VALUES (%s, %s, %s, %s, 1, %s)
    """, (
        produto_id,
        prox_versao,
        nome_template,
        str(custo_total_base),
        session.get('user_id')
    ))

    for it, qtd_base, custo_unit, custo_total_item in itens_normalizados:
        prod = db.fetch_one("SELECT unit_measure FROM products WHERE id = %s", (it['produto_id'],))
        unidade = it.get('unidade_medida') or (prod or {}).get('unit_measure')
        db.insert("""
            INSERT INTO produto_template_itens (
                template_id, tipo_item, produto_id, descricao,
                quantidade, unidade_medida, custo_unitario_base, custo_total_base
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            template_id,
            it['tipo_item'],
            it['produto_id'],
            it.get('descricao'),
            str(qtd_base),
            unidade,
            str(custo_unit),
            str(custo_total_item)
        ))

    return template_id


@ordem_producao_bp.route('/')
@industria_ops_visualizar_required
def listar_ops():
    """Lista todas as ordens de produção"""
    db = get_db()
    
    # Filtros
    status_filtro = request.args.get('status', '')
    cliente_filtro = request.args.get('cliente', '')
    
    try:
        query = """
            SELECT
                v.*,
                o.numero AS orcamento_numero,
                og.id AS grupo_id,
                og.orcamento_id
            FROM vw_ordens_producao_resumo v
            LEFT JOIN orcamento_op_itens oi ON oi.ordem_producao_id = v.id
            LEFT JOIN orcamento_op_grupos og ON og.id = oi.grupo_id
            LEFT JOIN orcamentos o ON o.id = og.orcamento_id
            WHERE 1=1
        """
        params = []
        
        if status_filtro:
            query += " AND status = %s"
            params.append(status_filtro)
        
        if cliente_filtro:
            query += " AND cliente_nome LIKE %s"
            params.append(f'%{cliente_filtro}%')
        
        query += " ORDER BY created_at DESC"
        
        ops = db.fetch_all(query, tuple(params) if params else None)
        
        # Buscar clientes para filtro
        clientes = db.fetch_all("SELECT id, name FROM customers WHERE active = TRUE ORDER BY name")
        
        return render_template('industria/ordem_producao_lista.html',
                             ops=ops,
                             clientes=clientes,
                             status_filtro=status_filtro,
                             cliente_filtro=cliente_filtro)
    except Exception as e:
        flash(f'Erro ao carregar ordens de produção: {str(e)}', 'danger')
        return render_template('industria/ordem_producao_lista.html', ops=[], clientes=[])


@ordem_producao_bp.route('/grupo/orcamento/<int:orcamento_id>')
def grupo_orcamento(orcamento_id):
    """Tela agrupadora das OPs geradas a partir de um orçamento."""
    db = get_db()

    try:
        grupo = db.fetch_one("""
            SELECT og.id, og.orcamento_id, og.empresa_id, og.cliente_id, og.criado_em,
                   o.numero AS orcamento_numero, o.status AS orcamento_status,
                   c.name AS cliente_nome,
                   e.nome_fantasia AS empresa_nome
            FROM orcamento_op_grupos og
            INNER JOIN orcamentos o ON o.id = og.orcamento_id
            INNER JOIN customers c ON c.id = og.cliente_id
            INNER JOIN empresas e ON e.id = og.empresa_id
            WHERE og.orcamento_id = %s
            LIMIT 1
        """, (orcamento_id,))

        if not grupo:
            flash('Nenhum romaneio de produção encontrado para este orçamento.', 'warning')
            return redirect(url_for('orcamentos.visualizar', id=orcamento_id))

        ops = db.fetch_all("""
            SELECT
                oi.id AS vinculo_id,
                oi.ordem_producao_id,
                oi.orcamento_item_id,
                oi.tem_template,
                op.numero_op,
                op.status,
                op.data_prevista,
                op.usou_template,
                op.tipo_op,
                op.obs_estoque,
                p.name AS produto_nome,
                oi.quantidade AS quantidade_orcamento
            FROM orcamento_op_itens oi
            INNER JOIN ordens_producao op ON op.id = oi.ordem_producao_id
            INNER JOIN products p ON p.id = oi.produto_id
            WHERE oi.orcamento_id = %s
            ORDER BY oi.id
        """, (orcamento_id,)) or []

        return render_template(
            'industria/ordem_producao_grupo.html',
            grupo=grupo,
            ops=ops
        )

    except Exception as e:
        flash(f'Erro ao carregar romaneio de produção: {str(e)}', 'danger')
        return redirect(url_for('orcamentos.visualizar', id=orcamento_id))


@ordem_producao_bp.route('/nova', methods=['GET'])
@industria_ops_criar_required
def nova_op():
    """Formulário para criar nova ordem de produção"""
    db = get_db()
    
    try:
        # Buscar empresas
        empresas = db.fetch_all("SELECT id, nome_fantasia FROM empresas WHERE ativo = TRUE ORDER BY nome_fantasia")
        
        # Buscar clientes
        clientes = db.fetch_all("SELECT id, name FROM customers WHERE active = TRUE ORDER BY name")

        return render_template('industria/ordem_producao_form.html',
                             empresas=empresas,
                             clientes=clientes,
                             produto_selecionado=None,
                             op=None)
    except Exception as e:
        flash(f'Erro ao carregar formulário: {str(e)}', 'danger')
        return redirect(url_for('ordem_producao.listar_ops'))


@ordem_producao_bp.route('/api/buscar-produtos-producao', methods=['GET'])
def api_buscar_produtos_producao():
    """API para buscar produtos finais (categoria_fiscal=produto_producao ou legado produto)."""
    db = get_db()
    termo = request.args.get('q', '')

    modo_all, parts = parse_star_search(termo)

    if not modo_all and (not parts or len(''.join(parts)) < 2):
        return jsonify([])

    try:
        where_parts = [
            "p.active = 1",
            "pc.categoria_fiscal IN ('produto_producao', 'produto')"
        ]
        params = []

        if modo_all:
            limit = 200
        else:
            clause, clause_params = build_multi_part_like_where(
                parts,
                ['p.internal_code', 'p.name', 'p.barcode']
            )
            if clause:
                where_parts.append(f"({clause})")
                params.extend(clause_params)
            limit = 50

        where_sql = " AND ".join(where_parts)

        produtos = db.fetch_all(f"""
            SELECT
                p.id,
                p.internal_code AS codigo,
                p.name AS nome,
                p.unit_measure AS unidade,
                p.cost_price AS custo
            FROM products p
            INNER JOIN product_categories pc ON p.category_id = pc.id
            WHERE {where_sql}
            ORDER BY p.name
            LIMIT {limit}
        """, params)

        return jsonify(produtos or [])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@ordem_producao_bp.route('/lotes/<int:lote_id>/mover', methods=['POST'])
@login_required
def mover_lote(lote_id):
    """Move um lote entre etapas. Se quantidade for menor que a do lote, divide (remanescente fica na etapa anterior)."""
    db = get_db()

    try:
        def _recalcular_align_sides(ordem_producao_id):
            itens = db.fetch_all(
                """
                SELECT l.id, l.etapa_atual_id, e.ordem
                FROM op_lotes l
                INNER JOIN producao_etapas e ON e.id = l.etapa_atual_id
                WHERE l.ordem_producao_id = %s AND l.etapa_atual_id IS NOT NULL
                """,
                (ordem_producao_id,)
            ) or []

            if not itens:
                return

            ordens = [int(i.get('ordem') or 0) for i in itens]
            min_ord = min(ordens)
            max_ord = max(ordens)

            # Se tudo estiver na mesma etapa, manter full
            if min_ord == max_ord:
                for it in itens:
                    db.update(
                        "UPDATE op_lotes SET align_side = 'full', updated_at = NOW() WHERE id = %s",
                        (it.get('id'),)
                    )
                return

            for it in itens:
                o = int(it.get('ordem') or 0)
                if o == min_ord:
                    side = 'right'
                elif o == max_ord:
                    side = 'left'
                else:
                    side = 'full'
                db.update(
                    "UPDATE op_lotes SET align_side = %s, updated_at = NOW() WHERE id = %s",
                    (side, it.get('id'))
                )

        etapa_nova_id = request.form.get('etapa_nova_id')
        qtd_raw = request.form.get('quantidade')
        observacao = (request.form.get('observacao') or '').strip()

        if not etapa_nova_id:
            return jsonify({'erro': 'Etapa não informada'}), 400

        def _normalizar_decimal(valor):
            v = ('' if valor is None else str(valor)).strip()
            if not v:
                raise InvalidOperation('empty')
            # aceita formatos pt-BR (1.234,56) e en-US (1234.56)
            if ',' in v and '.' in v:
                v = v.replace('.', '').replace(',', '.')
            elif ',' in v:
                v = v.replace(',', '.')
            return Decimal(v)

        try:
            qtd_mov = _normalizar_decimal(qtd_raw)
        except Exception:
            return jsonify({'erro': 'Quantidade inválida'}), 400

        if qtd_mov <= 0:
            return jsonify({'erro': 'Quantidade inválida'}), 400

        lote = db.fetch_one("""
            SELECT id, ordem_producao_id, sequencia, quantidade, etapa_atual_id
            FROM op_lotes
            WHERE id = %s
            LIMIT 1
        """, (lote_id,))
        if not lote:
            return jsonify({'erro': 'Lote não encontrado'}), 404

        op = db.fetch_one("SELECT id, quantidade, status FROM ordens_producao WHERE id = %s", (lote.get('ordem_producao_id'),))
        if not op:
            return jsonify({'erro': 'OP não encontrada'}), 404

        etapa_nova = db.fetch_one("SELECT id FROM producao_etapas WHERE id = %s AND ativo = 1", (etapa_nova_id,))
        if not etapa_nova:
            return jsonify({'erro': 'Etapa inválida'}), 400

        qtd_atual = Decimal(str(lote.get('quantidade') or 0))
        if qtd_mov > qtd_atual:
            return jsonify({'erro': 'Quantidade maior que a disponível no lote'}), 400

        etapa_anterior_id = lote.get('etapa_atual_id')

        # Se já existir lote da mesma OP na etapa destino, faz merge (soma) ao invés de criar duplicado
        lote_destino = db.fetch_one(
            """
            SELECT id, quantidade
            FROM op_lotes
            WHERE ordem_producao_id = %s AND etapa_atual_id = %s AND id <> %s
            ORDER BY id
            LIMIT 1
            """,
            (op.get('id'), etapa_nova_id, lote_id)
        )

        # Movimento total
        if qtd_mov == qtd_atual:
            if lote_destino:
                qtd_dest = Decimal(str(lote_destino.get('quantidade') or 0))
                qtd_nova = qtd_dest + qtd_mov
                db.update(
                    "UPDATE op_lotes SET quantidade = %s, align_side = 'full', updated_at = NOW() WHERE id = %s",
                    (str(qtd_nova), lote_destino.get('id'))
                )
                db.update("DELETE FROM op_lotes WHERE id = %s", (lote_id,))
                lote_movido_id = lote_destino.get('id')
            else:
                db.update(
                    "UPDATE op_lotes SET etapa_atual_id = %s, align_side = 'full', updated_at = NOW() WHERE id = %s",
                    (etapa_nova_id, lote_id)
                )
                lote_movido_id = lote_id
        else:
            # Movimento parcial: reduz lote atual e envia quantidade ao destino (merge se possível)
            qtd_restante = qtd_atual - qtd_mov
            db.update(
                "UPDATE op_lotes SET quantidade = %s, align_side = 'right', updated_at = NOW() WHERE id = %s",
                (str(qtd_restante), lote_id)
            )

            if lote_destino:
                qtd_dest = Decimal(str(lote_destino.get('quantidade') or 0))
                qtd_nova = qtd_dest + qtd_mov
                db.update(
                    "UPDATE op_lotes SET quantidade = %s, align_side = 'left', updated_at = NOW() WHERE id = %s",
                    (str(qtd_nova), lote_destino.get('id'))
                )
                lote_movido_id = lote_destino.get('id')
            else:
                prox_seq = db.fetch_one(
                    "SELECT COALESCE(MAX(sequencia), 0) + 1 AS s FROM op_lotes WHERE ordem_producao_id = %s",
                    (op.get('id'),)
                )
                seq = int((prox_seq or {}).get('s') or 1)

                lote_movido_id = db.insert(
                    "INSERT INTO op_lotes (ordem_producao_id, sequencia, quantidade, etapa_atual_id, align_side, status) VALUES (%s, %s, %s, %s, 'left', %s)",
                    (op.get('id'), seq, str(qtd_mov), etapa_nova_id, op.get('status'))
                )

        # Log do lote
        db.insert("""
            INSERT INTO op_lotes_etapas_log (
                lote_id, ordem_producao_id, quantidade_movida,
                etapa_anterior_id, etapa_nova_id,
                observacao, usuario_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            lote_movido_id,
            op.get('id'),
            str(qtd_mov),
            etapa_anterior_id,
            etapa_nova_id,
            observacao if observacao else None,
            session.get('user_id')
        ))

        # Compatibilidade: etapa_atual_id da OP = etapa com maior soma de quantidade
        dominante = db.fetch_one("""
            SELECT etapa_atual_id, SUM(quantidade) AS qtd
            FROM op_lotes
            WHERE ordem_producao_id = %s
            GROUP BY etapa_atual_id
            ORDER BY qtd DESC
            LIMIT 1
        """, (op.get('id'),))
        if dominante and dominante.get('etapa_atual_id'):
            db.update(
                "UPDATE ordens_producao SET etapa_atual_id = %s WHERE id = %s",
                (dominante.get('etapa_atual_id'), op.get('id'))
            )

        # Ajustar alinhamentos para refletir: origem (mais antiga)=direita, intermediárias=full, destino mais avançado=esquerda
        _recalcular_align_sides(op.get('id'))

        return jsonify({'sucesso': True})

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@ordem_producao_bp.route('/<int:id>/template/criar', methods=['POST'])
def criar_template_da_op(id):
    """Cria um template a partir da OP e aplica na OP."""
    db = get_db()

    try:
        template_id = _criar_template_a_partir_op(db, id)
        _aplicar_template_em_op(db, id, template_id)
        flash('Ficha Técnica criada e aplicada na OP com sucesso!', 'success')
        return redirect(url_for('ordem_producao.visualizar_op', id=id))
    except Exception as e:
        flash(f'Erro ao criar Ficha Técnica a partir da OP: {str(e)}', 'danger')
        return redirect(url_for('ordem_producao.visualizar_op', id=id))


@ordem_producao_bp.route('/<int:id>/template/importar', methods=['GET', 'POST'])
def importar_template_para_op(id):
    """Importa um template de outro produto e aplica na OP."""
    db = get_db()

    try:
        op = db.fetch_one("SELECT id, produto_id, numero_op, usou_template FROM ordens_producao WHERE id = %s", (id,))
        if not op:
            flash('OP não encontrada!', 'danger')
            return redirect(url_for('ordem_producao.listar_ops'))

        if request.method == 'GET':
            templates = db.fetch_all("""
                SELECT t.id AS template_id, t.produto_id, t.versao, t.nome_template,
                       p.name AS produto_nome
                FROM produto_templates_producao t
                INNER JOIN products p ON p.id = t.produto_id
                WHERE t.ativo = 1
                ORDER BY p.name, t.versao DESC
            """) or []

            return render_template('industria/ordem_producao_importar_template.html', op=op, templates=templates)

        template_origem_id = request.form.get('template_origem_id')
        if not template_origem_id:
            flash('Selecione uma Ficha Técnica de origem.', 'warning')
            return redirect(url_for('ordem_producao.importar_template_para_op', id=id))

        # Copiar template de origem para o produto final desta OP
        origem = db.fetch_one("""
            SELECT id, produto_id, versao, nome_template, custo_total_base
            FROM produto_templates_producao
            WHERE id = %s
        """, (template_origem_id,))
        if not origem:
            flash('Ficha Técnica de origem não encontrada.', 'danger')
            return redirect(url_for('ordem_producao.importar_template_para_op', id=id))

        # Próxima versão para o produto da OP
        versao_atual = db.fetch_one(
            "SELECT MAX(versao) AS v FROM produto_templates_producao WHERE produto_id = %s",
            (op['produto_id'],)
        )
        prox_versao = int((versao_atual or {}).get('v') or 0) + 1

        # Desativar template ativo anterior do produto
        db.execute_query(
            "UPDATE produto_templates_producao SET ativo = 0 WHERE produto_id = %s AND ativo = 1",
            (op['produto_id'],)
        )

        novo_template_id = db.insert("""
            INSERT INTO produto_templates_producao (
                produto_id, versao, nome_template, custo_total_base, ativo, created_by
            ) VALUES (%s, %s, %s, %s, 1, %s)
        """, (
            op['produto_id'],
            prox_versao,
            f"Importado: {origem.get('nome_template') or 'Template'}",
            str(origem.get('custo_total_base') or 0),
            session.get('user_id')
        ))

        itens_origem = db.fetch_all("""
            SELECT tipo_item, produto_id, descricao, quantidade, unidade_medida, custo_unitario_base, custo_total_base
            FROM produto_template_itens
            WHERE template_id = %s
            ORDER BY tipo_item, id
        """, (template_origem_id,)) or []

        for it in itens_origem:
            db.insert("""
                INSERT INTO produto_template_itens (
                    template_id, tipo_item, produto_id, descricao,
                    quantidade, unidade_medida, custo_unitario_base, custo_total_base
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                novo_template_id,
                it['tipo_item'],
                it['produto_id'],
                it.get('descricao'),
                it.get('quantidade'),
                it.get('unidade_medida'),
                it.get('custo_unitario_base'),
                it.get('custo_total_base')
            ))

        _aplicar_template_em_op(db, id, novo_template_id)
        flash('Ficha Técnica importada e aplicada na OP com sucesso!', 'success')
        return redirect(url_for('ordem_producao.visualizar_op', id=id))

    except Exception as e:
        flash(f'Erro ao importar Ficha Técnica: {str(e)}', 'danger')
        return redirect(url_for('ordem_producao.visualizar_op', id=id))


@ordem_producao_bp.route('/verificar-template/<int:produto_id>', methods=['GET'])
def verificar_template(produto_id):
    """Verifica se existe template ativo para o produto"""
    db = get_db()
    
    try:
        template = db.fetch_one("""
            SELECT 
                t.id,
                t.versao,
                t.nome_template,
                t.custo_total_base,
                t.tempo_producao_horas,
                t.observacoes,
                p.name as produto_nome
            FROM produto_templates_producao t
            INNER JOIN products p ON t.produto_id = p.id
            WHERE t.produto_id = %s AND t.ativo = 1
        """, (produto_id,))
        
        if template:
            # Buscar itens do template
            itens = db.fetch_all("""
                SELECT 
                    ti.id,
                    ti.tipo_item,
                    ti.produto_id,
                    p.name as produto_nome,
                    ti.descricao,
                    ti.quantidade,
                    ti.unidade_medida,
                    ti.custo_unitario_base,
                    ti.custo_total_base,
                    p.cost_price as custo_atual,
                    CASE 
                        WHEN ti.custo_unitario_base > 0 THEN
                            ((p.cost_price - ti.custo_unitario_base) / ti.custo_unitario_base) * 100
                        ELSE 0
                    END as variacao_percentual
                FROM produto_template_itens ti
                INNER JOIN products p ON ti.produto_id = p.id
                WHERE ti.template_id = %s
                ORDER BY ti.tipo_item, p.name
            """, (template['id'],))
            
            # Calcular custo total atual
            custo_total_atual = sum(
                float(item['quantidade']) * float(item['custo_atual'] or 0)
                for item in itens
            )
            
            # Calcular variação total
            variacao_total = 0
            if template['custo_total_base'] and template['custo_total_base'] > 0:
                variacao_total = ((custo_total_atual - float(template['custo_total_base'])) / 
                                float(template['custo_total_base'])) * 100
            
            return jsonify({
                'existe': True,
                'template': {
                    'id': template['id'],
                    'versao': template['versao'],
                    'nome': template['nome_template'],
                    'custo_base': float(template['custo_total_base'] or 0),
                    'custo_atual': custo_total_atual,
                    'variacao_percentual': round(variacao_total, 2),
                    'tempo_horas': float(template['tempo_producao_horas'] or 0),
                    'observacoes': template['observacoes']
                },
                'itens': [
                    {
                        'id': item['id'],
                        'tipo_item': item['tipo_item'],
                        'produto_id': item['produto_id'],
                        'produto_nome': item['produto_nome'],
                        'descricao': item['descricao'],
                        'quantidade': float(item['quantidade']),
                        'unidade_medida': item['unidade_medida'],
                        'custo_unitario_base': float(item['custo_unitario_base'] or 0),
                        'custo_unitario_atual': float(item['custo_atual'] or 0),
                        'custo_total_base': float(item['custo_total_base'] or 0),
                        'custo_total_atual': float(item['quantidade']) * float(item['custo_atual'] or 0),
                        'variacao_percentual': round(float(item['variacao_percentual'] or 0), 2)
                    }
                    for item in itens
                ]
            })
        else:
            return jsonify({'existe': False})
            
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@ordem_producao_bp.route('/buscar-produtos-por-tipo', methods=['GET'])
def buscar_produtos_por_tipo():
    """Busca produtos filtrados por categoria_fiscal"""
    db = get_db()
    tipo = request.args.get('tipo', '')
    
    try:
        # Mapear tipo_item para categoria_fiscal
        mapa_tipos = {
            'servico': 'servico',
            'materia_prima': 'materia_prima',
            'consumo_interno': 'consumo_interno'
        }
        
        categoria_fiscal = mapa_tipos.get(tipo)
        
        if not categoria_fiscal:
            return jsonify([])
        
        produtos = db.fetch_all("""
            SELECT 
                p.id,
                p.name,
                p.cost_price,
                p.unit_measure,
                pc.name as categoria_nome
            FROM products p
            INNER JOIN product_categories pc ON p.category_id = pc.id
            WHERE p.active = TRUE 
              AND pc.categoria_fiscal = %s
            ORDER BY p.name
        """, (categoria_fiscal,))
        
        return jsonify([
            {
                'id': p['id'],
                'name': p['name'],
                'cost_price': float(p['cost_price'] or 0),
                'unit_measure': p['unit_measure'],
                'categoria': p['categoria_nome']
            }
            for p in produtos
        ])
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@ordem_producao_bp.route('/salvar', methods=['POST'])
def salvar_op():
    """Salva nova ordem de produção ou atualiza existente"""
    db = get_db()
    
    try:
        # Verificar se é edição
        op_id = request.form.get('op_id')
        is_edicao = bool(op_id)
        
        # Dados gerais
        empresa_id = request.form.get('empresa_id')
        cliente_id = request.form.get('cliente_id')
        produto_id = request.form.get('produto_id')
        quantidade = request.form.get('quantidade')
        data_solicitacao = request.form.get('data_solicitacao')
        data_prevista = request.form.get('data_prevista')
        observacoes = request.form.get('observacoes', '')
        
        # Template
        usou_template = request.form.get('usou_template', '0')
        template_usado_id = request.form.get('template_usado_id')
        custo_total_template = request.form.get('custo_total_template', '0')
        
        # Validações
        if not all([empresa_id, cliente_id, produto_id, quantidade, data_solicitacao]):
            flash('Preencha todos os campos obrigatórios!', 'danger')
            return redirect(url_for('ordem_producao.nova_op'))
        
        # Se data_prevista não foi informada, calcular automaticamente
        if not data_prevista and not is_edicao:
            try:
                from app.services.previsao_producao_service import PrevisaoProducaoService
                service = PrevisaoProducaoService()
                tempo_produto = service.get_tempo_total_produto(int(produto_id))
                tempo_total = int(tempo_produto * float(quantidade))
                previsao = service.adicionar_minutos_uteis(datetime.now(), tempo_total, int(empresa_id) if empresa_id else None)
                data_prevista = previsao.strftime('%Y-%m-%d') if previsao else None
            except Exception as e:
                print(f"[OP] Erro ao calcular previsão: {e}")
        
        if is_edicao:
            # Atualizar OP existente
            db.execute_query("""
                UPDATE ordens_producao SET
                    empresa_id = %s, cliente_id = %s, produto_id = %s, quantidade = %s,
                    template_usado_id = %s, usou_template = %s, custo_total_template = %s,
                    data_solicitacao = %s, data_prevista = %s, observacoes = %s
                WHERE id = %s
            """, (
                empresa_id, cliente_id, produto_id, quantidade,
                template_usado_id if usou_template == '1' else None,
                usou_template, custo_total_template,
                data_solicitacao, data_prevista, observacoes, op_id
            ))
            
            # Excluir itens antigos
            db.execute_query("DELETE FROM ordem_producao_itens WHERE ordem_producao_id = %s", (op_id,))
        else:
            etapa_inicial = db.fetch_one("""
                SELECT id
                FROM producao_etapas
                WHERE ativo = 1
                ORDER BY ordem, id
                LIMIT 1
            """)
            etapa_inicial_id = etapa_inicial.get('id') if etapa_inicial else None

            # Inserir nova OP (número gerado automaticamente por trigger)
            op_id = db.insert("""
                INSERT INTO ordens_producao (
                    empresa_id, cliente_id, produto_id, quantidade,
                    template_usado_id, usou_template, custo_total_template,
                    data_solicitacao, data_prevista, observacoes,
                    etapa_atual_id,
                    status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pendente')
            """, (
                empresa_id, cliente_id, produto_id, quantidade,
                template_usado_id if usou_template == '1' else None,
                usou_template, custo_total_template,
                data_solicitacao, data_prevista, observacoes,
                etapa_inicial_id
            ))

            # Criar lote inicial (100%)
            try:
                db.insert(
                    "INSERT INTO op_lotes (ordem_producao_id, sequencia, quantidade, etapa_atual_id, align_side, status) VALUES (%s, 1, %s, %s, 'full', 'pendente')",
                    (op_id, quantidade, etapa_inicial_id)
                )
            except Exception:
                pass
        
        # Inserir itens
        custo_total_atual = Decimal('0')
        
        # Processar itens de serviço
        servico_ids = request.form.getlist('servico_produto_id[]')
        for i, prod_id in enumerate(servico_ids):
            if prod_id:
                qtd = request.form.getlist('servico_quantidade[]')[i]
                custo_unit = request.form.getlist('servico_custo_unitario[]')[i]
                custo_template = request.form.getlist('servico_custo_template[]')[i] or None
                veio_template = request.form.getlist('servico_veio_template[]')[i] or '0'
                
                custo_total_item = Decimal(qtd) * Decimal(custo_unit)
                custo_total_atual += custo_total_item
                
                # Buscar dados do produto
                prod = db.fetch_one("SELECT name, unit_measure FROM products WHERE id = %s", (prod_id,))
                
                db.insert("""
                    INSERT INTO ordem_producao_itens (
                        ordem_producao_id, tipo_item, produto_id, descricao,
                        quantidade, unidade_medida, custo_unitario_template,
                        custo_unitario_atual, custo_total, veio_template
                    ) VALUES (%s, 'servico', %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    op_id, prod_id, prod['name'], qtd, prod['unit_measure'],
                    custo_template, custo_unit, custo_total_item, veio_template
                ))
        
        # Processar itens de matéria prima
        materia_ids = request.form.getlist('materia_produto_id[]')
        for i, prod_id in enumerate(materia_ids):
            if prod_id:
                qtd = request.form.getlist('materia_quantidade[]')[i]
                custo_unit = request.form.getlist('materia_custo_unitario[]')[i]
                custo_template = request.form.getlist('materia_custo_template[]')[i] or None
                veio_template = request.form.getlist('materia_veio_template[]')[i] or '0'
                
                custo_total_item = Decimal(qtd) * Decimal(custo_unit)
                custo_total_atual += custo_total_item
                
                prod = db.fetch_one("SELECT name, unit_measure FROM products WHERE id = %s", (prod_id,))
                
                db.insert("""
                    INSERT INTO ordem_producao_itens (
                        ordem_producao_id, tipo_item, produto_id, descricao,
                        quantidade, unidade_medida, custo_unitario_template,
                        custo_unitario_atual, custo_total, veio_template
                    ) VALUES (%s, 'materia_prima', %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    op_id, prod_id, prod['name'], qtd, prod['unit_measure'],
                    custo_template, custo_unit, custo_total_item, veio_template
                ))
        
        # Processar itens de consumo interno
        consumo_ids = request.form.getlist('consumo_produto_id[]')
        for i, prod_id in enumerate(consumo_ids):
            if prod_id:
                qtd = request.form.getlist('consumo_quantidade[]')[i]
                custo_unit = request.form.getlist('consumo_custo_unitario[]')[i]
                custo_template = request.form.getlist('consumo_custo_template[]')[i] or None
                veio_template = request.form.getlist('consumo_veio_template[]')[i] or '0'
                
                custo_total_item = Decimal(qtd) * Decimal(custo_unit)
                custo_total_atual += custo_total_item
                
                prod = db.fetch_one("SELECT name, unit_measure FROM products WHERE id = %s", (prod_id,))
                
                db.insert("""
                    INSERT INTO ordem_producao_itens (
                        ordem_producao_id, tipo_item, produto_id, descricao,
                        quantidade, unidade_medida, custo_unitario_template,
                        custo_unitario_atual, custo_total, veio_template
                    ) VALUES (%s, 'consumo_interno', %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    op_id, prod_id, prod['name'], qtd, prod['unit_measure'],
                    custo_template, custo_unit, custo_total_item, veio_template
                ))
        
        # Atualizar custo total da OP
        db.execute_query("""
            UPDATE ordens_producao 
            SET custo_total_atual = %s
            WHERE id = %s
        """, (custo_total_atual, op_id))
        
        # Buscar número da OP
        op = db.fetch_one("SELECT numero_op FROM ordens_producao WHERE id = %s", (op_id,))
        
        if is_edicao:
            flash(f'Ordem de Produção {op["numero_op"]} atualizada com sucesso!', 'success')
        else:
            flash(f'Ordem de Produção {op["numero_op"]} criada com sucesso!', 'success')
        
        return redirect(url_for('ordem_producao.visualizar_op', id=op_id))
        
    except Exception as e:
        flash(f'Erro ao salvar ordem de produção: {str(e)}', 'danger')
        return redirect(url_for('ordem_producao.nova_op'))


@ordem_producao_bp.route('/editar/<int:id>', methods=['GET'])
@industria_ops_editar_required
def editar_op(id):
    """Formulário para editar ordem de produção"""
    db = get_db()
    
    try:
        # Buscar OP
        op = db.fetch_one("SELECT * FROM ordens_producao WHERE id = %s", (id,))
        
        if not op:
            flash('Ordem de produção não encontrada!', 'danger')
            return redirect(url_for('ordem_producao.listar_ops'))
        
        if op['status'] != 'pendente':
            flash('Apenas OPs pendentes podem ser editadas!', 'warning')
            return redirect(url_for('ordem_producao.visualizar_op', id=id))
        
        # Buscar dados para formulário
        empresas = db.fetch_all("SELECT id, nome_fantasia FROM empresas WHERE ativo = TRUE ORDER BY nome_fantasia")
        clientes = db.fetch_all("SELECT id, name FROM customers WHERE active = TRUE ORDER BY name")

        produto_selecionado = None
        if op.get('produto_id'):
            produto_selecionado = db.fetch_one(
                "SELECT id, internal_code AS codigo, name AS nome FROM products WHERE id = %s",
                (op['produto_id'],)
            )
        
        # Buscar itens da OP
        itens = db.fetch_all("""
            SELECT * FROM ordem_producao_itens 
            WHERE ordem_producao_id = %s
            ORDER BY tipo_item, id
        """, (id,))
        
        return render_template('industria/ordem_producao_form.html',
                             empresas=empresas,
                             clientes=clientes,
                             produto_selecionado=produto_selecionado,
                             op=op,
                             itens=itens)
        
    except Exception as e:
        flash(f'Erro ao carregar formulário: {str(e)}', 'danger')
        return redirect(url_for('ordem_producao.listar_ops'))


@ordem_producao_bp.route('/visualizar/<int:id>')
def visualizar_op(id):
    """Visualiza detalhes de uma ordem de produção"""
    db = get_db()
    
    try:
        # Buscar OP
        op = db.fetch_one("SELECT * FROM vw_ordens_producao_resumo WHERE id = %s", (id,))
        
        if not op:
            flash('Ordem de produção não encontrada!', 'danger')
            return redirect(url_for('ordem_producao.listar_ops'))

        # Etapas de chão de fábrica
        etapa_atual = db.fetch_one("""
            SELECT e.id, e.nome, e.ordem
            FROM ordens_producao op
            LEFT JOIN producao_etapas e ON e.id = op.etapa_atual_id
            WHERE op.id = %s
            LIMIT 1
        """, (id,))

        etapas = db.fetch_all("""
            SELECT id, nome, ordem
            FROM producao_etapas
            WHERE ativo = 1
            ORDER BY ordem, id
        """) or []

        # Unificar histórico: log antigo (op_etapas_log) + log de lotes (op_lotes_etapas_log)
        # Inclui líder, operador, etapa, data, status
        etapas_log = db.fetch_all("""
            SELECT
                x.id,
                x.created_at,
                x.observacao,
                x.etapa_anterior,
                x.etapa_nova,
                x.usuario_nome,
                x.lote_info,
                x.quantidade_movida,
                x.lider_nome,
                x.operador_nome,
                x.status_anterior,
                x.status_novo,
                x.arara
            FROM (
                SELECT
                    CONCAT('op_', l.id) AS id,
                    l.created_at,
                    l.observacao,
                    ea.nome AS etapa_anterior,
                    en.nome AS etapa_nova,
                    u.name AS usuario_nome,
                    NULL AS lote_info,
                    NULL AS quantidade_movida,
                    NULL AS lider_nome,
                    NULL AS operador_nome,
                    NULL AS status_anterior,
                    NULL AS status_novo,
                    NULL AS arara
                FROM op_etapas_log l
                LEFT JOIN producao_etapas ea ON ea.id = l.etapa_anterior_id
                INNER JOIN producao_etapas en ON en.id = l.etapa_nova_id
                LEFT JOIN users u ON u.id = l.usuario_id
                WHERE l.ordem_producao_id = %s

                UNION ALL

                SELECT
                    CONCAT('lote_', ll.id) AS id,
                    ll.created_at,
                    ll.observacao,
                    ea2.nome AS etapa_anterior,
                    en2.nome AS etapa_nova,
                    u2.name AS usuario_nome,
                    CONCAT('Lote ', COALESCE(lo.sequencia, '-')) AS lote_info,
                    ll.quantidade_movida AS quantidade_movida,
                    ulider.name AS lider_nome,
                    uop.name AS operador_nome,
                    ll.status_anterior,
                    ll.status_novo,
                    ll.arara
                FROM op_lotes_etapas_log ll
                LEFT JOIN op_lotes lo ON lo.id = ll.lote_id
                LEFT JOIN producao_etapas ea2 ON ea2.id = ll.etapa_anterior_id
                LEFT JOIN producao_etapas en2 ON en2.id = ll.etapa_nova_id
                LEFT JOIN users u2 ON u2.id = ll.usuario_id
                LEFT JOIN users ulider ON ulider.id = ll.lider_id
                LEFT JOIN users uop ON uop.id = ll.operador_origem_id
                WHERE ll.ordem_producao_id = %s
            ) x
            ORDER BY x.created_at DESC
            LIMIT 200
        """, (id, id)) or []
        
        # Buscar itens
        itens = db.fetch_all("""
            SELECT * FROM vw_ordem_producao_itens_detalhado 
            WHERE ordem_producao_id = %s
            ORDER BY tipo_item, produto_nome
        """, (id,))
        
        # Agrupar itens por tipo
        itens_por_tipo = {
            'servico': [],
            'materia_prima': [],
            'consumo_interno': []
        }
        
        for item in itens:
            itens_por_tipo[item['tipo_item']].append(item)
        
        # Calcular totais por tipo
        totais = {
            'servico': sum(float(i['custo_total']) for i in itens_por_tipo['servico']),
            'materia_prima': sum(float(i['custo_total']) for i in itens_por_tipo['materia_prima']),
            'consumo_interno': sum(float(i['custo_total']) for i in itens_por_tipo['consumo_interno'])
        }
        
        return render_template('industria/ordem_producao_visualizar.html',
                             op=op,
                             etapa_atual=etapa_atual,
                             etapas=etapas,
                             etapas_log=etapas_log,
                             itens_por_tipo=itens_por_tipo,
                             totais=totais)
        
    except Exception as e:
        flash(f'Erro ao carregar ordem de produção: {str(e)}', 'danger')
        return redirect(url_for('ordem_producao.listar_ops'))


@ordem_producao_bp.route('/<int:id>/mudar-etapa', methods=['POST'])
@login_required
def mudar_etapa(id):
    """Altera etapa atual da OP e registra log (data/hora + usuário)."""
    db = get_db()

    try:
        etapa_nova_id = request.form.get('etapa_nova_id')
        observacao = (request.form.get('observacao') or '').strip()

        if not etapa_nova_id:
            return jsonify({'erro': 'Etapa não informada'}), 400

        op = db.fetch_one("SELECT id, etapa_atual_id FROM ordens_producao WHERE id = %s", (id,))
        if not op:
            return jsonify({'erro': 'OP não encontrada'}), 404

        etapa_nova = db.fetch_one(
            "SELECT id FROM producao_etapas WHERE id = %s AND ativo = 1",
            (etapa_nova_id,)
        )
        if not etapa_nova:
            return jsonify({'erro': 'Etapa inválida'}), 400

        etapa_anterior_id = op.get('etapa_atual_id')

        # Atualizar etapa atual (persistência garantida)
        db.update(
            "UPDATE ordens_producao SET etapa_atual_id = %s WHERE id = %s",
            (etapa_nova_id, id)
        )

        # Regras mínimas: ao sair de "pendente" via etapa, marcar como "em_producao" e preencher data de início
        op_status = db.fetch_one("SELECT status, data_inicio_producao FROM ordens_producao WHERE id = %s", (id,))
        if op_status and op_status.get('status') == 'pendente':
            if op_status.get('data_inicio_producao') is None:
                db.update(
                    "UPDATE ordens_producao SET status = 'em_producao', data_inicio_producao = CURDATE() WHERE id = %s",
                    (id,)
                )
            else:
                db.update(
                    "UPDATE ordens_producao SET status = 'em_producao' WHERE id = %s",
                    (id,)
                )

        db.insert("""
            INSERT INTO op_etapas_log (
                ordem_producao_id, etapa_anterior_id, etapa_nova_id,
                observacao, usuario_id
            ) VALUES (%s, %s, %s, %s, %s)
        """, (
            id,
            etapa_anterior_id,
            etapa_nova_id,
            observacao if observacao else None,
            session.get('user_id')
        ))

        return jsonify({'sucesso': True})

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@ordem_producao_bp.route('/alterar-status/<int:id>', methods=['POST'])
def alterar_status(id):
    """Altera o status de uma ordem de produção"""
    db = get_db()
    
    try:
        novo_status = request.form.get('status')
        motivo_cancelamento = request.form.get('motivo_cancelamento', '')
        
        if novo_status not in ['pendente', 'em_producao', 'concluida', 'cancelada']:
            return jsonify({'erro': 'Status inválido'}), 400
        
        # Buscar dados da OP antes de atualizar
        op = db.fetch_one("""
            SELECT op.id, op.produto_id, op.quantidade, op.status, op.tipo_op
            FROM ordens_producao op
            WHERE op.id = %s
        """, (id,))
        
        if not op:
            return jsonify({'erro': 'OP não encontrada'}), 404
        
        # Atualizar datas conforme status
        updates = []
        params = [novo_status]
        
        if novo_status == 'em_producao':
            updates.append("data_inicio_producao = CURDATE()")
        elif novo_status == 'concluida':
            updates.append("data_conclusao = CURDATE()")
            
            # Se OP de PRODUÇÃO está sendo concluída, ADICIONAR ao estoque
            if op['tipo_op'] in ('producao', 'mista') and op['status'] != 'concluida':
                produto_id = op['produto_id']
                quantidade = float(op['quantidade'] or 0)
                
                if produto_id and quantidade > 0:
                    if registrar_movimentacao:
                        # Usar helper Kardex
                        resultado = registrar_movimentacao(
                            produto_id=produto_id,
                            tipo='entrada_producao',
                            quantidade=quantidade,
                            origem_tela='Ordem de Produção',
                            referencia_tipo='op',
                            referencia_id=id,
                            referencia_codigo=f'OP-{id}',
                            observacao=f'Entrada de produção - OP #{id}'
                        )
                        if resultado.get('success'):
                            print(f"[OP CONCLUÍDA] [KARDEX] Estoque: {resultado.get('estoque_anterior')} -> {resultado.get('estoque_posterior')}")
                        else:
                            print(f"[OP CONCLUÍDA] [KARDEX] Erro: {resultado.get('error')}")
                    else:
                        # Fallback: atualização direta
                        db.execute("""
                            UPDATE products 
                            SET stock_quantity = COALESCE(stock_quantity, 0) + %s
                            WHERE id = %s
                        """, (quantidade, produto_id))
                        
                        db.execute("""
                            INSERT INTO current_stock (product_id, location_id, quantity)
                            VALUES (%s, 1, %s)
                            ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
                        """, (produto_id, quantidade))
                    
                    print(f"[OP CONCLUÍDA] Estoque atualizado: Produto {produto_id} +{quantidade}")
                    
        elif novo_status == 'cancelada':
            updates.append("motivo_cancelamento = %s")
            params.append(motivo_cancelamento)
        
        query = f"UPDATE ordens_producao SET status = %s"
        if updates:
            query += ", " + ", ".join(updates)
        query += " WHERE id = %s"
        params.append(id)
        
        db.execute_query(query, tuple(params))
        
        flash('Status alterado com sucesso!', 'success')
        return jsonify({'sucesso': True})
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@ordem_producao_bp.route('/excluir/<int:id>', methods=['POST'])
@industria_ops_excluir_required
def excluir_op(id):
    """Exclui uma ordem de produção"""
    db = get_db()
    
    try:
        # Verificar se pode excluir
        op = db.fetch_one("SELECT status FROM ordens_producao WHERE id = %s", (id,))
        
        if not op:
            flash('Ordem de produção não encontrada!', 'danger')
            return redirect(url_for('ordem_producao.listar_ops'))
        
        if op['status'] in ['em_producao', 'concluida']:
            flash('Não é possível excluir OP em produção ou concluída!', 'warning')
            return redirect(url_for('ordem_producao.listar_ops'))
        
        # Excluir (CASCADE vai excluir itens automaticamente)
        db.execute_query("DELETE FROM ordens_producao WHERE id = %s", (id,))
        
        flash('Ordem de produção excluída com sucesso!', 'success')
        return redirect(url_for('ordem_producao.listar_ops'))
        
    except Exception as e:
        flash(f'Erro ao excluir ordem de produção: {str(e)}', 'danger')
        return redirect(url_for('ordem_producao.listar_ops'))


# =====================================================
# GANTT DO OPERADOR - Tela exclusiva para operadores
# =====================================================

@ordem_producao_bp.route('/meu-gantt')
@login_required
def meu_gantt():
    """Gantt exclusivo para operadores de chão de fábrica.
    Mostra apenas lotes vinculados ao operador logado.
    Status: Em Espera -> Em Produção -> Despachado
    """
    db = get_db()
    user_id = session.get('user_id')
    
    # Verificar se usuário tem permissão para esta tela
    from utils.permissoes_helper import tem_permissao
    if not tem_permissao('industria.minha_producao', 'visualizar'):
        flash('Você não tem permissão para acessar esta funcionalidade.', 'warning')
        return redirect(url_for('bem_vindo'))
    
    status_filtro = (request.args.get('status') or '').strip()
    
    # Buscar o líder do operador
    lider_info = db.fetch_one("""
        SELECT lo.lider_id, u.name AS lider_nome
        FROM lider_operadores lo
        INNER JOIN users u ON u.id = lo.lider_id
        WHERE lo.operador_id = %s
        LIMIT 1
    """, (user_id,))
    
    lider_id = lider_info.get('lider_id') if lider_info else None
    
    # Buscar etapas do líder do operador (apenas as que ele pode trabalhar)
    etapas_lider = []
    if lider_id:
        etapas_lider = db.fetch_all("""
            SELECT e.id, e.nome, e.ordem, e.cor_hex, e.icone, e.descricao,
                   e.grupo_etapas_id, e.operador_padrao_id,
                   g.nome AS grupo_etapas_nome
            FROM lider_etapas le
            INNER JOIN producao_etapas e ON e.id = le.etapa_id
            LEFT JOIN producao_etapas_grupos g ON g.id = e.grupo_etapas_id
            WHERE le.lider_id = %s AND e.ativo = 1
            ORDER BY e.ordem, e.id
        """, (lider_id,)) or []
    
    # Buscar todas etapas (para despacho externo)
    etapas = db.fetch_all("""
        SELECT e.id, e.nome, e.ordem, e.cor_hex, e.icone, e.descricao,
               e.grupo_etapas_id, e.operador_padrao_id,
               g.nome AS grupo_etapas_nome
        FROM producao_etapas e
        LEFT JOIN producao_etapas_grupos g ON g.id = e.grupo_etapas_id
        WHERE e.ativo = 1
        ORDER BY e.ordem, e.id
    """) or []
    
    try:
        # Buscar lotes do operador (atribuídos pelo líder OU vinculados à etapa)
        # Prioriza operador_designado_id (atribuição do líder)
        query = """
            SELECT
                l.id AS lote_id,
                l.sequencia AS lote_sequencia,
                l.quantidade AS lote_quantidade,
                l.etapa_atual_id,
                l.operador_id,
                l.operador_designado_id,
                l.prioridade,
                l.status_operador,
                l.arara,
                l.data_atribuicao,
                l.data_inicio_operador,
                l.data_fim_operador,
                op.data_inicio_producao,
                (SELECT MAX(log.created_at) 
                 FROM op_lotes_etapas_log log 
                 WHERE log.lote_id = l.id 
                   AND log.etapa_nova_id = l.etapa_atual_id) AS data_chegada_etapa,
                pp.id AS pausa_id,
                pp.inicio AS pausa_inicio,
                ppm.nome AS pausa_motivo,
                v.id AS op_id,
                v.numero_op,
                v.cliente_nome,
                v.produto_nome,
                v.status AS op_status,
                v.data_solicitacao,
                v.data_prevista,
                op.quantidade AS op_quantidade_total,
                e.nome AS etapa_nome,
                e.cor_hex AS etapa_cor_hex,
                e.icone AS etapa_icone,
                og.id AS grupo_id,
                o.numero AS orcamento_numero
            FROM op_lotes l
            INNER JOIN ordens_producao op ON op.id = l.ordem_producao_id
            INNER JOIN vw_ordens_producao_resumo v ON v.id = op.id
            LEFT JOIN producao_etapas e ON e.id = l.etapa_atual_id
            LEFT JOIN orcamento_op_itens oi ON oi.ordem_producao_id = v.id
            LEFT JOIN orcamento_op_grupos og ON og.id = oi.grupo_id
            LEFT JOIN orcamentos o ON o.id = og.orcamento_id
            LEFT JOIN producao_pausas pp ON pp.lote_id = l.id AND pp.fim IS NULL
            LEFT JOIN producao_pausas_motivos ppm ON ppm.id = pp.motivo_id
            WHERE v.status NOT IN ('concluida', 'cancelada')
              AND (l.operador_designado_id = %s OR l.operador_id = %s OR e.operador_padrao_id = %s)
        """
        params = [user_id, user_id, user_id]
        
        if status_filtro:
            query += " AND l.status_operador = %s"
            params.append(status_filtro)
        
        query += " AND l.status_operador IN ('em_espera', 'em_producao')"
        query += " ORDER BY l.prioridade, l.status_operador, v.data_prevista, v.id"
        
        lotes = db.fetch_all(query, tuple(params)) or []
        
        # Buscar lotes despachados HOJE pelo operador (com etapa destino e arara)
        lotes_despachados = db.fetch_all("""
            SELECT
                l.id AS lote_id,
                l.sequencia AS lote_sequencia,
                l.quantidade AS lote_quantidade,
                log.etapa_anterior_id AS etapa_atual_id,
                l.operador_id,
                l.operador_designado_id,
                l.prioridade,
                'despachado' AS status_operador,
                log.arara,
                l.data_inicio_operador,
                log.created_at AS data_fim_operador,
                v.id AS op_id,
                v.numero_op,
                v.cliente_nome,
                v.produto_nome,
                v.status AS op_status,
                v.data_solicitacao,
                v.data_prevista,
                op.quantidade AS op_quantidade_total,
                e_ant.nome AS etapa_nome,
                e_ant.cor_hex AS etapa_cor_hex,
                e_ant.icone AS etapa_icone,
                e_dest.nome AS etapa_destino_nome,
                e_dest.cor_hex AS etapa_destino_cor
            FROM op_lotes_etapas_log log
            INNER JOIN op_lotes l ON l.id = log.lote_id
            INNER JOIN ordens_producao op ON op.id = l.ordem_producao_id
            INNER JOIN vw_ordens_producao_resumo v ON v.id = op.id
            LEFT JOIN producao_etapas e_ant ON e_ant.id = log.etapa_anterior_id
            LEFT JOIN producao_etapas e_dest ON e_dest.id = log.etapa_nova_id
            WHERE log.status_novo = 'despachado'
              AND log.usuario_id = %s
              AND DATE(log.created_at) = CURDATE()
            ORDER BY log.created_at DESC
        """, (user_id,)) or []
        
        # Agrupar por status do operador
        lotes_por_status = {
            'em_espera': [],
            'em_producao': [],
            'despachado': lotes_despachados
        }
        
        for lote in lotes:
            status = lote.get('status_operador') or 'em_espera'
            if status in lotes_por_status:
                lotes_por_status[status].append(lote)
        
        return render_template(
            'industria/meu_gantt.html',
            lotes=lotes,
            lotes_por_status=lotes_por_status,
            etapas=etapas,
            etapas_lider=etapas_lider,
            lider_info=lider_info,
            status_filtro=status_filtro,
            full_width=True,
            menu_collapsed=True,
        )
        
    except Exception as e:
        flash(f'Erro ao carregar meu gantt: {str(e)}', 'danger')
        return render_template(
            'industria/meu_gantt.html',
            lotes=[],
            lotes_por_status={'em_espera': [], 'em_producao': [], 'despachado': []},
            etapas=etapas,
            etapas_lider=[],
            lider_info=None,
            status_filtro=status_filtro,
            full_width=True,
            menu_collapsed=True,
        )


@ordem_producao_bp.route('/meu-gantt/iniciar-producao', methods=['POST'])
@login_required
def meu_gantt_iniciar_producao():
    """Operador inicia produção de um lote, informando quantidade e etapa.
    Se quantidade parcial, divide o lote (parte em_producao, parte em_espera).
    Se já existe lote em_producao na mesma etapa, faz merge."""
    if not session.get('eh_operador'):
        return jsonify({'success': False, 'error': 'Acesso restrito a operadores.'}), 403
    
    db = get_db()
    user_id = session.get('user_id')
    lote_id = request.form.get('lote_id')
    etapa_id = request.form.get('etapa_id')
    quantidade = request.form.get('quantidade')
    
    if not lote_id:
        return jsonify({'success': False, 'error': 'Lote não informado.'}), 400
    
    try:
        # Buscar lote atual
        lote = db.fetch_one("""
            SELECT id, ordem_producao_id, quantidade, etapa_atual_id, status 
            FROM op_lotes WHERE id = %s
        """, (lote_id,))
        if not lote:
            return jsonify({'success': False, 'error': 'Lote não encontrado.'}), 404
        
        etapa_anterior = lote.get('etapa_atual_id')
        ordem_producao_id = lote.get('ordem_producao_id')
        qtd_lote = Decimal(str(lote.get('quantidade') or 0))
        lote_status = lote.get('status')
        nova_etapa = etapa_id or etapa_anterior
        
        # Quantidade a iniciar
        qtd_iniciar = Decimal(str(quantidade)) if quantidade else qtd_lote
        
        # Buscar líder do operador
        lider_info = db.fetch_one("""
            SELECT lo.lider_id
            FROM lider_operadores lo
            WHERE lo.operador_id = %s
            LIMIT 1
        """, (user_id,))
        lider_id = lider_info.get('lider_id') if lider_info else None
        
        # Verificar se já existe lote em_producao na mesma etapa (para merge)
        lote_producao_existente = db.fetch_one("""
            SELECT id, quantidade 
            FROM op_lotes 
            WHERE ordem_producao_id = %s 
              AND etapa_atual_id = %s 
              AND id != %s
              AND status_operador = 'em_producao'
              AND operador_id = %s
            LIMIT 1
        """, (ordem_producao_id, nova_etapa, lote_id, user_id))
        
        if qtd_iniciar >= qtd_lote:
            # Quantidade total - iniciar lote inteiro
            if lote_producao_existente:
                # MERGE: Somar ao lote já em produção
                nova_qtd = Decimal(str(lote_producao_existente.get('quantidade') or 0)) + qtd_lote
                db.update("""
                    UPDATE op_lotes 
                    SET quantidade = %s, updated_at = NOW()
                    WHERE id = %s
                """, (str(nova_qtd), lote_producao_existente.get('id')))
                
                # Deletar lote atual (foi mergeado)
                db.update("DELETE FROM op_lotes WHERE id = %s", (lote_id,))
                
                # Log
                db.insert("""
                    INSERT INTO op_lotes_etapas_log 
                    (lote_id, ordem_producao_id, lider_id, quantidade_movida, etapa_anterior_id, etapa_nova_id,
                     operador_origem_id, status_anterior, status_novo, usuario_id, observacao, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'em_espera', 'em_producao', %s, 'Iniciou e mergeou com lote existente', NOW())
                """, (lote_producao_existente.get('id'), ordem_producao_id, lider_id, str(qtd_lote), 
                      etapa_anterior, nova_etapa, user_id, user_id))
                
                return jsonify({'success': True, 'message': f'Produção iniciada e combinada! Total: {nova_qtd}'})
            else:
                # Iniciar normalmente
                db.update("""
                    UPDATE op_lotes 
                    SET status_operador = 'em_producao',
                        operador_id = %s,
                        etapa_atual_id = %s,
                        data_inicio_operador = NOW(),
                        updated_at = NOW()
                    WHERE id = %s
                """, (user_id, nova_etapa, lote_id))
                
                # Log
                db.insert("""
                    INSERT INTO op_lotes_etapas_log 
                    (lote_id, ordem_producao_id, lider_id, quantidade_movida, etapa_anterior_id, etapa_nova_id,
                     operador_origem_id, status_anterior, status_novo, usuario_id, observacao, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'em_espera', 'em_producao', %s, 'Operador iniciou produção', NOW())
                """, (lote_id, ordem_producao_id, lider_id, str(qtd_lote), 
                      etapa_anterior, nova_etapa, user_id, user_id))
                
                return jsonify({'success': True, 'message': 'Produção iniciada!'})
        else:
            # Quantidade parcial - DIVIDIR LOTE
            qtd_restante = qtd_lote - qtd_iniciar
            
            # Atualizar lote original com quantidade restante (permanece em_espera)
            db.update("""
                UPDATE op_lotes 
                SET quantidade = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (str(qtd_restante), lote_id))
            
            if lote_producao_existente:
                # MERGE: Somar quantidade ao lote já em produção
                nova_qtd = Decimal(str(lote_producao_existente.get('quantidade') or 0)) + qtd_iniciar
                db.update("""
                    UPDATE op_lotes 
                    SET quantidade = %s, updated_at = NOW()
                    WHERE id = %s
                """, (str(nova_qtd), lote_producao_existente.get('id')))
                
                # Log para lote original (quantidade reduzida)
                db.insert("""
                    INSERT INTO op_lotes_etapas_log 
                    (lote_id, ordem_producao_id, lider_id, quantidade_movida, etapa_anterior_id, etapa_nova_id,
                     operador_origem_id, status_anterior, status_novo, usuario_id, observacao, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'em_espera', 'em_espera', %s, 'Lote dividido - restante em espera', NOW())
                """, (lote_id, ordem_producao_id, lider_id, str(qtd_restante), 
                      etapa_anterior, etapa_anterior, user_id, user_id))
                
                # Log para lote em produção (mergeado)
                db.insert("""
                    INSERT INTO op_lotes_etapas_log 
                    (lote_id, ordem_producao_id, lider_id, quantidade_movida, etapa_anterior_id, etapa_nova_id,
                     operador_origem_id, status_anterior, status_novo, usuario_id, observacao, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'em_espera', 'em_producao', %s, 'Quantidade adicionada (merge)', NOW())
                """, (lote_producao_existente.get('id'), ordem_producao_id, lider_id, str(qtd_iniciar), 
                      etapa_anterior, nova_etapa, user_id, user_id))
                
                return jsonify({'success': True, 'message': f'Lote dividido e combinado! {qtd_iniciar} somado ao em produção (total: {nova_qtd}), {qtd_restante} permanece em espera.'})
            else:
                # Criar novo lote em produção
                prox_seq = db.fetch_one("""
                    SELECT COALESCE(MAX(sequencia), 0) + 1 AS s 
                    FROM op_lotes WHERE ordem_producao_id = %s
                """, (ordem_producao_id,))
                seq = int((prox_seq or {}).get('s') or 1)
                
                novo_lote_id = db.insert("""
                    INSERT INTO op_lotes 
                    (ordem_producao_id, sequencia, quantidade, etapa_atual_id, 
                     operador_id, operador_designado_id, status_operador, 
                     data_inicio_operador, align_side, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, 'em_producao', NOW(), 'full', %s, NOW())
                """, (ordem_producao_id, seq, str(qtd_iniciar), 
                      nova_etapa, user_id, user_id, lote_status))
                
                # Log para lote original (quantidade reduzida, permanece em_espera)
                db.insert("""
                    INSERT INTO op_lotes_etapas_log 
                    (lote_id, ordem_producao_id, lider_id, quantidade_movida, etapa_anterior_id, etapa_nova_id,
                     operador_origem_id, status_anterior, status_novo, usuario_id, observacao, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'em_espera', 'em_espera', %s, 'Lote dividido - restante em espera', NOW())
                """, (lote_id, ordem_producao_id, lider_id, str(qtd_restante), 
                      etapa_anterior, etapa_anterior, user_id, user_id))
                
                # Log para novo lote (em produção)
                db.insert("""
                    INSERT INTO op_lotes_etapas_log 
                    (lote_id, ordem_producao_id, lider_id, quantidade_movida, etapa_anterior_id, etapa_nova_id,
                     operador_origem_id, status_anterior, status_novo, usuario_id, observacao, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'em_espera', 'em_producao', %s, 'Lote dividido - iniciou produção', NOW())
                """, (novo_lote_id, ordem_producao_id, lider_id, str(qtd_iniciar), 
                      etapa_anterior, nova_etapa, user_id, user_id))
                
                return jsonify({'success': True, 'message': f'Lote dividido! {qtd_iniciar} em produção, {qtd_restante} permanece em espera.'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ordem_producao_bp.route('/meu-gantt/alterar-etapa', methods=['POST'])
@login_required
def meu_gantt_alterar_etapa():
    """Operador altera a etapa do lote em produção. Se quantidade parcial, divide o lote."""
    if not session.get('eh_operador'):
        return jsonify({'success': False, 'error': 'Acesso restrito a operadores.'}), 403
    
    db = get_db()
    user_id = session.get('user_id')
    lote_id = request.form.get('lote_id')
    nova_etapa_id = request.form.get('etapa_id')
    quantidade = request.form.get('quantidade')
    
    if not lote_id or not nova_etapa_id:
        return jsonify({'success': False, 'error': 'Lote e etapa são obrigatórios.'}), 400
    
    try:
        # Buscar lote
        lote = db.fetch_one("""
            SELECT id, ordem_producao_id, quantidade, etapa_atual_id, status 
            FROM op_lotes WHERE id = %s
        """, (lote_id,))
        if not lote:
            return jsonify({'success': False, 'error': 'Lote não encontrado.'}), 404
        
        etapa_anterior = lote.get('etapa_atual_id')
        ordem_producao_id = lote.get('ordem_producao_id')
        lote_status = lote.get('status')
        qtd_atual = Decimal(str(lote.get('quantidade') or 0))
        qtd_movida = Decimal(str(quantidade)) if quantidade else qtd_atual
        
        # Buscar líder do operador para registrar no log
        lider_info = db.fetch_one("""
            SELECT lo.lider_id
            FROM lider_operadores lo
            WHERE lo.operador_id = %s
            LIMIT 1
        """, (user_id,))
        lider_id = lider_info.get('lider_id') if lider_info else None
        
        # Verificar se já existe lote da mesma OP na etapa destino (para merge)
        lote_destino = db.fetch_one("""
            SELECT id, quantidade 
            FROM op_lotes 
            WHERE ordem_producao_id = %s 
              AND etapa_atual_id = %s 
              AND id != %s
              AND status_operador = 'em_producao'
            LIMIT 1
        """, (ordem_producao_id, nova_etapa_id, lote_id))
        
        if qtd_movida >= qtd_atual:
            # Quantidade total - mover lote inteiro para nova etapa
            if lote_destino:
                # MERGE: Somar quantidade ao lote existente na etapa destino
                nova_qtd = Decimal(str(lote_destino.get('quantidade') or 0)) + qtd_atual
                db.update("""
                    UPDATE op_lotes 
                    SET quantidade = %s, updated_at = NOW()
                    WHERE id = %s
                """, (str(nova_qtd), lote_destino.get('id')))
                
                # Deletar lote atual (foi mergeado)
                db.update("DELETE FROM op_lotes WHERE id = %s", (lote_id,))
                
                # Log
                db.insert("""
                    INSERT INTO op_lotes_etapas_log 
                    (lote_id, ordem_producao_id, quantidade_movida, etapa_anterior_id, etapa_nova_id,
                     lider_id, operador_origem_id, status_anterior, status_novo, usuario_id, 
                     observacao, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'em_producao', 'em_producao', %s, 
                            'Lote mergeado com existente', NOW())
                """, (lote_destino.get('id'), ordem_producao_id, str(qtd_atual), 
                      etapa_anterior, nova_etapa_id, lider_id, user_id, user_id))
                
                return jsonify({'success': True, 'message': f'Lote combinado! Total na etapa: {nova_qtd}'})
            else:
                # Mover normalmente
                db.update("""
                    UPDATE op_lotes 
                    SET etapa_atual_id = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (nova_etapa_id, lote_id))
                
                # Log
                db.insert("""
                    INSERT INTO op_lotes_etapas_log 
                    (lote_id, ordem_producao_id, quantidade_movida, etapa_anterior_id, etapa_nova_id,
                     lider_id, operador_origem_id, status_anterior, status_novo, usuario_id, 
                     observacao, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'em_producao', 'em_producao', %s, 
                            'Alterou etapa (total)', NOW())
                """, (lote_id, ordem_producao_id, str(qtd_movida), 
                      etapa_anterior, nova_etapa_id, lider_id, user_id, user_id))
                
                return jsonify({'success': True, 'message': 'Etapa alterada!'})
        else:
            # Quantidade parcial - DIVIDIR LOTE
            qtd_restante = qtd_atual - qtd_movida
            
            # Atualizar lote original com quantidade restante (permanece na etapa atual)
            db.update("""
                UPDATE op_lotes 
                SET quantidade = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (str(qtd_restante), lote_id))
            
            if lote_destino:
                # MERGE: Somar quantidade ao lote existente na etapa destino
                nova_qtd = Decimal(str(lote_destino.get('quantidade') or 0)) + qtd_movida
                db.update("""
                    UPDATE op_lotes 
                    SET quantidade = %s, updated_at = NOW()
                    WHERE id = %s
                """, (str(nova_qtd), lote_destino.get('id')))
                
                # Log para lote original (quantidade reduzida)
                db.insert("""
                    INSERT INTO op_lotes_etapas_log 
                    (lote_id, ordem_producao_id, quantidade_movida, etapa_anterior_id, etapa_nova_id,
                     lider_id, operador_origem_id, status_anterior, status_novo, usuario_id, 
                     observacao, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'em_producao', 'em_producao', %s, 
                            'Lote dividido - restante', NOW())
                """, (lote_id, ordem_producao_id, str(qtd_restante), 
                      etapa_anterior, etapa_anterior, lider_id, user_id, user_id))
                
                # Log para lote destino (mergeado)
                db.insert("""
                    INSERT INTO op_lotes_etapas_log 
                    (lote_id, ordem_producao_id, quantidade_movida, etapa_anterior_id, etapa_nova_id,
                     lider_id, operador_origem_id, status_anterior, status_novo, usuario_id, 
                     observacao, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'em_producao', 'em_producao', %s, 
                            'Quantidade adicionada (merge)', NOW())
                """, (lote_destino.get('id'), ordem_producao_id, str(qtd_movida), 
                      etapa_anterior, nova_etapa_id, lider_id, user_id, user_id))
                
                return jsonify({'success': True, 'message': f'Lote dividido e combinado! {qtd_movida} somado ao existente (total: {nova_qtd}), {qtd_restante} permanece.'})
            else:
                # Criar novo lote com quantidade movida na nova etapa
                prox_seq = db.fetch_one("""
                    SELECT COALESCE(MAX(sequencia), 0) + 1 AS s 
                    FROM op_lotes WHERE ordem_producao_id = %s
                """, (ordem_producao_id,))
                seq = int((prox_seq or {}).get('s') or 1)
                
                novo_lote_id = db.insert("""
                    INSERT INTO op_lotes 
                    (ordem_producao_id, sequencia, quantidade, etapa_atual_id, 
                     operador_id, operador_designado_id, status_operador, 
                     data_inicio_operador, align_side, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, 'em_producao', NOW(), 'full', %s, NOW())
                """, (ordem_producao_id, seq, str(qtd_movida), 
                      nova_etapa_id, user_id, user_id, lote_status))
                
                # Log para lote original (quantidade reduzida)
                db.insert("""
                    INSERT INTO op_lotes_etapas_log 
                    (lote_id, ordem_producao_id, quantidade_movida, etapa_anterior_id, etapa_nova_id,
                     lider_id, operador_origem_id, status_anterior, status_novo, usuario_id, 
                     observacao, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'em_producao', 'em_producao', %s, 
                            'Lote dividido - restante', NOW())
                """, (lote_id, ordem_producao_id, str(qtd_restante), 
                      etapa_anterior, etapa_anterior, lider_id, user_id, user_id))
                
                # Log para novo lote (movido para nova etapa)
                db.insert("""
                    INSERT INTO op_lotes_etapas_log 
                    (lote_id, ordem_producao_id, quantidade_movida, etapa_anterior_id, etapa_nova_id,
                     lider_id, operador_origem_id, status_anterior, status_novo, usuario_id, 
                     observacao, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'em_producao', 'em_producao', %s, 
                            'Lote dividido - movido para nova etapa', NOW())
                """, (novo_lote_id, ordem_producao_id, str(qtd_movida), 
                      etapa_anterior, nova_etapa_id, lider_id, user_id, user_id))
                
                return jsonify({'success': True, 'message': f'Lote dividido! {qtd_movida} para nova etapa, {qtd_restante} permanece.'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ordem_producao_bp.route('/meu-gantt/despachar', methods=['POST'])
@login_required
def meu_gantt_despachar():
    """Operador despacha lote para próxima etapa."""
    if not session.get('eh_operador'):
        return jsonify({'success': False, 'error': 'Acesso restrito a operadores.'}), 403
    
    db = get_db()
    user_id = session.get('user_id')
    lote_id = request.form.get('lote_id')
    quantidade_enviada = request.form.get('quantidade')
    arara = request.form.get('arara', '').strip()
    proxima_etapa_id = request.form.get('proxima_etapa_id')
    observacao = request.form.get('observacao', '').strip()
    
    if not lote_id:
        return jsonify({'success': False, 'error': 'Lote não informado.'}), 400
    
    try:
        # Buscar lote atual
        lote = db.fetch_one("""
            SELECT l.id, l.ordem_producao_id, l.quantidade, l.etapa_atual_id, l.status, 
                   e.ordem AS etapa_ordem
            FROM op_lotes l
            LEFT JOIN producao_etapas e ON e.id = l.etapa_atual_id
            WHERE l.id = %s
        """, (lote_id,))
        
        if not lote:
            return jsonify({'success': False, 'error': 'Lote não encontrado.'}), 404
        
        etapa_atual_id = lote.get('etapa_atual_id')
        qtd_atual = Decimal(str(lote.get('quantidade') or 0))
        qtd_enviada = Decimal(str(quantidade_enviada or qtd_atual))
        
        # Se não informou próxima etapa, buscar a seguinte
        if not proxima_etapa_id:
            proxima = db.fetch_one("""
                SELECT id FROM producao_etapas 
                WHERE ativo = 1 AND ordem > %s
                ORDER BY ordem LIMIT 1
            """, (lote.get('etapa_ordem') or 0,))
            proxima_etapa_id = proxima.get('id') if proxima else None
        
        # Se NÃO há próxima etapa, é FINALIZAÇÃO - adicionar ao estoque
        if not proxima_etapa_id:
            # Buscar dados da OP para saber o produto
            op_data = db.fetch_one("""
                SELECT op.id, op.produto_id, op.tipo_op, p.name as produto_nome
                FROM ordens_producao op
                LEFT JOIN products p ON p.id = op.produto_id
                WHERE op.id = %s
            """, (lote.get('ordem_producao_id'),))
            
            if op_data and op_data.get('produto_id') and op_data.get('tipo_op') in ('producao', 'mista'):
                produto_id = op_data['produto_id']
                quantidade_finalizada = float(qtd_enviada)
                op_id = lote.get('ordem_producao_id')
                
                if registrar_movimentacao:
                    # Usar helper Kardex
                    resultado = registrar_movimentacao(
                        produto_id=produto_id,
                        tipo='entrada_producao',
                        quantidade=quantidade_finalizada,
                        origem_tela='Lote Produção',
                        referencia_tipo='op_lote',
                        referencia_id=lote_id,
                        referencia_codigo=f'OP-{op_id}/L-{lote_id}',
                        observacao=f'Produção finalizada - Lote #{lote_id} da OP #{op_id}'
                    )
                    if resultado.get('success'):
                        print(f"[LOTE FINALIZADO] [KARDEX] Estoque: {resultado.get('estoque_anterior')} -> {resultado.get('estoque_posterior')}")
                    else:
                        print(f"[LOTE FINALIZADO] [KARDEX] Erro: {resultado.get('error')}")
                else:
                    # Fallback: atualização direta
                    db.execute("""
                        UPDATE products 
                        SET stock_quantity = COALESCE(stock_quantity, 0) + %s
                        WHERE id = %s
                    """, (quantidade_finalizada, produto_id))
                    
                    db.execute("""
                        INSERT INTO current_stock (product_id, location_id, quantity)
                        VALUES (%s, 1, %s)
                        ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
                    """, (produto_id, quantidade_finalizada))
                
                print(f"[LOTE FINALIZADO] Estoque atualizado: Produto {produto_id} +{quantidade_finalizada}")
            
            # Marcar lote como concluído
            db.update("""
                UPDATE op_lotes 
                SET status = 'concluido',
                    data_fim_operador = NOW(),
                    updated_at = NOW()
                WHERE id = %s
            """, (lote_id,))
            
            # Log
            db.insert("""
                INSERT INTO op_lotes_etapas_log 
                (lote_id, ordem_producao_id, quantidade_movida, etapa_anterior_id, etapa_nova_id,
                 usuario_id, observacao, created_at)
                VALUES (%s, %s, %s, %s, NULL, %s, %s, NOW())
            """, (lote_id, lote.get('ordem_producao_id'), str(qtd_enviada), 
                  etapa_atual_id, user_id, 'Lote finalizado - entrada no estoque'))
            
            return jsonify({'success': True, 'message': 'Lote finalizado! Produto adicionado ao estoque.'})
        
        # Ao despachar para outra etapa, o lote NÃO vai para operador nenhum
        # Vai SOMENTE para o líder responsável pela etapa destino
        # O líder depois atribui a um operador
        
        if qtd_enviada >= qtd_atual:
            # Despacho total - mover lote para próxima etapa (sem operador)
            db.update("""
                UPDATE op_lotes 
                SET etapa_atual_id = %s,
                    operador_id = NULL,
                    operador_designado_id = NULL,
                    status_operador = NULL,
                    arara = %s,
                    data_fim_operador = NOW(),
                    updated_at = NOW()
                WHERE id = %s
            """, (proxima_etapa_id, arara, lote_id))
        else:
            # Despacho parcial - lote atual continua em produção com restante
            # Cria novo lote na próxima etapa (vai para líder)
            qtd_restante = qtd_atual - qtd_enviada
            ordem_producao_id = lote.get('ordem_producao_id')
            
            # Lote atual continua EM PRODUÇÃO com quantidade restante
            db.update("""
                UPDATE op_lotes 
                SET quantidade = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (str(qtd_restante), lote_id))
            
            # Criar novo lote na próxima etapa (sem operador - vai para líder)
            prox_seq = db.fetch_one("""
                SELECT COALESCE(MAX(sequencia), 0) + 1 AS s 
                FROM op_lotes WHERE ordem_producao_id = %s
            """, (ordem_producao_id,))
            seq = int((prox_seq or {}).get('s') or 1)
            
            db.insert("""
                INSERT INTO op_lotes 
                (ordem_producao_id, sequencia, quantidade, etapa_atual_id, 
                 operador_id, operador_designado_id, status_operador, align_side, status, arara, created_at)
                VALUES (%s, %s, %s, %s, NULL, NULL, NULL, 'full', %s, %s, NOW())
            """, (ordem_producao_id, seq, str(qtd_enviada), 
                  proxima_etapa_id, lote.get('status'), arara))
        
        # Log
        db.insert("""
            INSERT INTO op_lotes_etapas_log 
            (lote_id, ordem_producao_id, quantidade_movida, etapa_anterior_id, etapa_nova_id,
             operador_origem_id, operador_destino_id, arara, status_anterior, status_novo,
             usuario_id, observacao, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NULL, %s, 'em_producao', 'despachado', %s, %s, NOW())
        """, (lote_id, lote.get('ordem_producao_id'), str(qtd_enviada), 
              etapa_atual_id, proxima_etapa_id, user_id,
              arara, user_id, observacao or 'Lote despachado para líder'))
        
        return jsonify({'success': True, 'message': 'Lote despachado com sucesso!'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ordem_producao_bp.route('/meu-gantt/corrigir-despacho', methods=['POST'])
@login_required
def meu_gantt_corrigir_despacho():
    """Operador corrige um despacho errado - altera etapa destino e/ou arara."""
    if not session.get('eh_operador'):
        return jsonify({'success': False, 'error': 'Acesso restrito a operadores.'}), 403
    
    db = get_db()
    user_id = session.get('user_id')
    
    try:
        lote_id = request.form.get('lote_id')
        etapa_destino_id = request.form.get('etapa_destino_id')
        arara = (request.form.get('arara') or '').strip()
        observacao = (request.form.get('observacao') or '').strip()
        
        if not lote_id or not etapa_destino_id:
            return jsonify({'success': False, 'error': 'Lote e etapa destino são obrigatórios.'}), 400
        
        if not observacao:
            return jsonify({'success': False, 'error': 'Motivo da correção é obrigatório.'}), 400
        
        # Buscar último log de despacho deste lote feito pelo operador hoje
        log_despacho = db.fetch_one("""
            SELECT log.id, log.lote_id, log.etapa_anterior_id, log.etapa_nova_id, 
                   log.arara AS arara_anterior, l.etapa_atual_id
            FROM op_lotes_etapas_log log
            INNER JOIN op_lotes l ON l.id = log.lote_id
            WHERE log.lote_id = %s 
              AND log.status_novo = 'despachado'
              AND log.usuario_id = %s
              AND DATE(log.created_at) = CURDATE()
            ORDER BY log.created_at DESC
            LIMIT 1
        """, (lote_id, user_id))
        
        if not log_despacho:
            return jsonify({'success': False, 'error': 'Despacho não encontrado ou não foi feito por você hoje.'}), 404
        
        etapa_anterior_log = log_despacho.get('etapa_nova_id')
        etapa_atual_lote = log_despacho.get('etapa_atual_id')
        
        # Atualizar a etapa atual do lote para a nova etapa destino
        db.update("""
            UPDATE op_lotes 
            SET etapa_atual_id = %s,
                arara = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (etapa_destino_id, arara or None, lote_id))
        
        # Atualizar o log de despacho original com a correção
        db.update("""
            UPDATE op_lotes_etapas_log 
            SET etapa_nova_id = %s,
                arara = %s,
                observacao = CONCAT(COALESCE(observacao, ''), ' | CORREÇÃO: ', %s)
            WHERE id = %s
        """, (etapa_destino_id, arara or None, observacao, log_despacho.get('id')))
        
        # Registrar log de correção
        db.insert("""
            INSERT INTO op_lotes_etapas_log 
            (lote_id, ordem_producao_id, quantidade_movida, etapa_anterior_id, etapa_nova_id,
             operador_origem_id, arara, status_anterior, status_novo,
             usuario_id, observacao, created_at)
            SELECT %s, ordem_producao_id, quantidade, %s, %s,
                   %s, %s, 'despachado', 'correcao_despacho',
                   %s, %s, NOW()
            FROM op_lotes WHERE id = %s
        """, (lote_id, etapa_anterior_log, etapa_destino_id,
              user_id, arara or None, user_id, 
              f'CORREÇÃO DE DESPACHO: {observacao}', lote_id))
        
        return jsonify({'success': True, 'message': 'Despacho corrigido com sucesso!'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =====================================================
# PAINEL DO LÍDER DE EQUIPE
# =====================================================

@ordem_producao_bp.route('/lider/painel')
@login_required
def lider_painel():
    """Painel do líder de equipe - visualiza lotes das etapas que controla."""
    db = get_db()
    user_id = session.get('user_id')
    
    # Verificar se é líder
    if not session.get('eh_lider_equipe'):
        flash('Acesso restrito a líderes de equipe.', 'warning')
        return redirect(url_for('ordem_producao.producao_gantt'))
    
    try:
        # Buscar etapas que o líder controla
        etapas_lider = db.fetch_all("""
            SELECT e.id, e.nome, e.ordem, e.cor_hex, e.icone
            FROM lider_etapas le
            INNER JOIN producao_etapas e ON e.id = le.etapa_id
            WHERE le.lider_id = %s AND e.ativo = 1
            ORDER BY e.ordem
        """, (user_id,)) or []
        
        etapa_ids = [e['id'] for e in etapas_lider]
        
        # Buscar operadores da equipe
        operadores = db.fetch_all("""
            SELECT u.id, u.name, u.username
            FROM lider_operadores lo
            INNER JOIN users u ON u.id = lo.operador_id
            WHERE lo.lider_id = %s AND u.status = 'active'
            ORDER BY u.name
        """, (user_id,)) or []
        
        # Buscar lotes das etapas do líder (sem_atribuicao, em_espera, em_producao)
        # status_operador NULL = sem atribuição (lote disponível para líder atribuir)
        lotes = []
        if etapa_ids:
            placeholders = ','.join(['%s'] * len(etapa_ids))
            lotes = db.fetch_all(f"""
                SELECT
                    l.id AS lote_id,
                    l.sequencia,
                    l.quantidade,
                    l.prioridade,
                    COALESCE(l.status_operador, 'sem_atribuicao') AS status_operador,
                    l.operador_id,
                    l.operador_designado_id,
                    l.arara,
                    u_op.name AS operador_nome,
                    u_design.name AS operador_designado_nome,
                    l.etapa_atual_id,
                    e.nome AS etapa_nome,
                    e.cor_hex AS etapa_cor,
                    op.id AS op_id,
                    op.numero_op,
                    v.cliente_nome,
                    v.produto_nome,
                    v.data_prevista,
                    op.data_inicio_producao,
                    l.data_atribuicao,
                    l.data_inicio_operador,
                    (SELECT MAX(log.created_at) 
                     FROM op_lotes_etapas_log log 
                     WHERE log.lote_id = l.id 
                       AND log.etapa_nova_id = l.etapa_atual_id) AS data_chegada_etapa,
                    pp.id AS pausa_id,
                    pp.inicio AS pausa_inicio,
                    ppm.nome AS pausa_motivo,
                    ppm.tipo AS pausa_tipo
                FROM op_lotes l
                INNER JOIN ordens_producao op ON op.id = l.ordem_producao_id
                INNER JOIN vw_ordens_producao_resumo v ON v.id = op.id
                INNER JOIN producao_etapas e ON e.id = l.etapa_atual_id
                LEFT JOIN users u_op ON u_op.id = l.operador_id
                LEFT JOIN users u_design ON u_design.id = l.operador_designado_id
                LEFT JOIN producao_pausas pp ON pp.lote_id = l.id AND pp.fim IS NULL
                LEFT JOIN producao_pausas_motivos ppm ON ppm.id = pp.motivo_id
                WHERE v.status NOT IN ('concluida', 'cancelada')
                  AND l.etapa_atual_id IN ({placeholders})
                  AND (l.status_operador IS NULL 
                       OR l.status_operador IN ('em_espera', 'em_producao'))
                ORDER BY l.prioridade, v.data_prevista, l.id
            """, tuple(etapa_ids)) or []
            
            # REMOVIDO: Query de lotes despachados do log
            # Causava duplicidade - agora despachados são tratados apenas pelo operador
        
        # Estatísticas por operador
        stats_operadores = {}
        for op in operadores:
            stats = db.fetch_one("""
                SELECT 
                    COUNT(CASE WHEN status_operador = 'em_espera' THEN 1 END) AS em_espera,
                    COUNT(CASE WHEN status_operador = 'em_producao' THEN 1 END) AS em_producao,
                    COUNT(CASE WHEN status_operador = 'despachado' AND DATE(data_fim_operador) = CURDATE() THEN 1 END) AS despachados_hoje
                FROM op_lotes
                WHERE operador_designado_id = %s
            """, (op['id'],)) or {}
            stats_operadores[op['id']] = stats
        
        return render_template(
            'industria/lider_painel.html',
            etapas_lider=etapas_lider,
            operadores=operadores,
            lotes=lotes,
            stats_operadores=stats_operadores,
            full_width=True
        )
        
    except Exception as e:
        flash(f'Erro ao carregar painel: {str(e)}', 'danger')
        return render_template(
            'industria/lider_painel.html',
            etapas_lider=[],
            operadores=[],
            lotes=[],
            stats_operadores={},
            full_width=True
        )


@ordem_producao_bp.route('/lider/atribuir-lote', methods=['POST'])
@login_required
def lider_atribuir_lote():
    """Líder atribui lote (ou parte dele) a um operador com prioridade.
    Se quantidade < total do lote, divide o lote em dois.
    """
    if not session.get('eh_lider_equipe'):
        return jsonify({'success': False, 'error': 'Acesso restrito a líderes.'}), 403
    
    db = get_db()
    user_id = session.get('user_id')
    lote_id = request.form.get('lote_id')
    operador_id = request.form.get('operador_id') or None
    prioridade = request.form.get('prioridade') or 3
    quantidade_atribuir = request.form.get('quantidade')
    arara = request.form.get('arara') or None
    
    if not lote_id:
        return jsonify({'success': False, 'error': 'Lote não informado.'}), 400
    
    try:
        # Buscar lote atual
        lote = db.fetch_one("""
            SELECT id, ordem_producao_id, quantidade, etapa_atual_id, status 
            FROM op_lotes WHERE id = %s
        """, (lote_id,))
        if not lote:
            return jsonify({'success': False, 'error': 'Lote não encontrado.'}), 404
        
        quantidade_total = float(lote.get('quantidade', 0))
        quantidade_atribuir = float(quantidade_atribuir) if quantidade_atribuir else quantidade_total
        
        if quantidade_atribuir <= 0:
            return jsonify({'success': False, 'error': 'Quantidade inválida.'}), 400
        
        if quantidade_atribuir > quantidade_total:
            return jsonify({'success': False, 'error': f'Quantidade maior que disponível ({quantidade_total}).'}), 400
        
        ordem_producao_id = lote.get('ordem_producao_id')
        etapa_atual_id = lote.get('etapa_atual_id')
        lote_status = lote.get('status')
        
        if quantidade_atribuir < quantidade_total:
            # DIVIDIR O LOTE: criar novo lote com o restante
            quantidade_restante = quantidade_total - quantidade_atribuir
            
            # Buscar próxima sequência
            max_seq = db.fetch_one("""
                SELECT MAX(sequencia) as max_seq FROM op_lotes 
                WHERE ordem_producao_id = %s
            """, (ordem_producao_id,))
            nova_sequencia = (max_seq.get('max_seq') or 0) + 1 if max_seq else 1
            
            # Criar lote com o restante (fica SEM ATRIBUIÇÃO - NULL)
            db.insert("""
                INSERT INTO op_lotes (
                    ordem_producao_id, sequencia, quantidade, etapa_atual_id,
                    status_operador, prioridade, status, created_at
                ) VALUES (%s, %s, %s, %s, NULL, 3, %s, NOW())
            """, (
                ordem_producao_id,
                nova_sequencia,
                quantidade_restante,
                etapa_atual_id,
                lote_status
            ))
            
            # Atualizar lote original com a quantidade atribuída
            db.update("""
                UPDATE op_lotes 
                SET quantidade = %s,
                    operador_designado_id = %s,
                    operador_id = %s,
                    status_operador = 'em_espera',
                    arara = %s,
                    prioridade = %s,
                    data_atribuicao = NOW(),
                    atribuido_por_id = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (quantidade_atribuir, operador_id, operador_id, arara, prioridade, user_id, lote_id))
            
            # Log da atribuição (lote dividido)
            db.insert("""
                INSERT INTO op_lotes_etapas_log 
                (lote_id, ordem_producao_id, lider_id, quantidade_movida, etapa_anterior_id, etapa_nova_id,
                 operador_destino_id, arara, status_anterior, status_novo, usuario_id, observacao, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'sem_atribuicao', 'em_espera', %s, 
                        'Líder atribuiu lote parcial ao operador', NOW())
            """, (lote_id, ordem_producao_id, user_id, quantidade_atribuir, etapa_atual_id, etapa_atual_id,
                  operador_id, arara, user_id))
            
            return jsonify({
                'success': True, 
                'message': f'Lote dividido! {quantidade_atribuir} atribuído ao operador, {quantidade_restante} disponível para atribuição.'
            })
        else:
            # Atribuir lote inteiro
            db.update("""
                UPDATE op_lotes 
                SET operador_designado_id = %s,
                    operador_id = %s,
                    status_operador = 'em_espera',
                    arara = %s,
                    prioridade = %s,
                    data_atribuicao = NOW(),
                    atribuido_por_id = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (operador_id, operador_id, arara, prioridade, user_id, lote_id))
            
            # Log da atribuição (lote inteiro)
            db.insert("""
                INSERT INTO op_lotes_etapas_log 
                (lote_id, ordem_producao_id, lider_id, quantidade_movida, etapa_anterior_id, etapa_nova_id,
                 operador_destino_id, arara, status_anterior, status_novo, usuario_id, observacao, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'sem_atribuicao', 'em_espera', %s, 
                        'Líder atribuiu lote ao operador', NOW())
            """, (lote_id, ordem_producao_id, user_id, quantidade_atribuir, etapa_atual_id, etapa_atual_id,
                  operador_id, arara, user_id))
            
            return jsonify({'success': True, 'message': 'Lote atribuído com sucesso!'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ordem_producao_bp.route('/lider/gerenciar-equipe')
@login_required
def lider_gerenciar_equipe():
    """Líder gerencia sua equipe e etapas."""
    db = get_db()
    user_id = session.get('user_id')
    
    if not session.get('eh_lider_equipe'):
        flash('Acesso restrito a líderes de equipe.', 'warning')
        return redirect(url_for('ordem_producao.producao_gantt'))
    
    try:
        # Operadores da equipe
        operadores_equipe = db.fetch_all("""
            SELECT u.id, u.name, u.username
            FROM lider_operadores lo
            INNER JOIN users u ON u.id = lo.operador_id
            WHERE lo.lider_id = %s
            ORDER BY u.name
        """, (user_id,)) or []
        
        # Etapas do líder
        etapas_lider = db.fetch_all("""
            SELECT e.id, e.nome, e.ordem
            FROM lider_etapas le
            INNER JOIN producao_etapas e ON e.id = le.etapa_id
            WHERE le.lider_id = %s
            ORDER BY e.ordem
        """, (user_id,)) or []
        
        # Todos operadores disponíveis (para adicionar)
        todos_operadores = db.fetch_all("""
            SELECT id, name, username FROM users 
            WHERE eh_operador = 1 AND status = 'active'
            ORDER BY name
        """) or []
        
        # Todas etapas disponíveis (para adicionar)
        todas_etapas = db.fetch_all("""
            SELECT id, nome, ordem FROM producao_etapas 
            WHERE ativo = 1
            ORDER BY ordem
        """) or []
        
        return render_template(
            'industria/lider_gerenciar_equipe.html',
            operadores_equipe=operadores_equipe,
            etapas_lider=etapas_lider,
            todos_operadores=todos_operadores,
            todas_etapas=todas_etapas
        )
        
    except Exception as e:
        flash(f'Erro ao carregar configuração: {str(e)}', 'danger')
        return redirect(url_for('ordem_producao.lider_painel'))


@ordem_producao_bp.route('/lider/vincular-operador', methods=['POST'])
@login_required
def lider_vincular_operador():
    """Vincula operador à equipe do líder."""
    if not session.get('eh_lider_equipe'):
        return jsonify({'success': False, 'error': 'Acesso restrito a líderes.'}), 403
    
    db = get_db()
    user_id = session.get('user_id')
    operador_id = request.form.get('operador_id')
    
    if not operador_id:
        return jsonify({'success': False, 'error': 'Operador não informado.'}), 400
    
    try:
        db.insert("""
            INSERT IGNORE INTO lider_operadores (lider_id, operador_id)
            VALUES (%s, %s)
        """, (user_id, operador_id))
        
        return jsonify({'success': True, 'message': 'Operador vinculado!'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ordem_producao_bp.route('/lider/desvincular-operador', methods=['POST'])
@login_required
def lider_desvincular_operador():
    """Remove operador da equipe do líder."""
    if not session.get('eh_lider_equipe'):
        return jsonify({'success': False, 'error': 'Acesso restrito a líderes.'}), 403
    
    db = get_db()
    user_id = session.get('user_id')
    operador_id = request.form.get('operador_id')
    
    try:
        db.execute_query("""
            DELETE FROM lider_operadores 
            WHERE lider_id = %s AND operador_id = %s
        """, (user_id, operador_id))
        
        return jsonify({'success': True, 'message': 'Operador removido da equipe!'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ordem_producao_bp.route('/lider/vincular-etapa', methods=['POST'])
@login_required
def lider_vincular_etapa():
    """Vincula etapa ao controle do líder."""
    if not session.get('eh_lider_equipe'):
        return jsonify({'success': False, 'error': 'Acesso restrito a líderes.'}), 403
    
    db = get_db()
    user_id = session.get('user_id')
    etapa_id = request.form.get('etapa_id')
    
    if not etapa_id:
        return jsonify({'success': False, 'error': 'Etapa não informada.'}), 400
    
    try:
        db.insert("""
            INSERT IGNORE INTO lider_etapas (lider_id, etapa_id)
            VALUES (%s, %s)
        """, (user_id, etapa_id))
        
        return jsonify({'success': True, 'message': 'Etapa vinculada!'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ordem_producao_bp.route('/lider/desvincular-etapa', methods=['POST'])
@login_required
def lider_desvincular_etapa():
    """Remove etapa do controle do líder."""
    if not session.get('eh_lider_equipe'):
        return jsonify({'success': False, 'error': 'Acesso restrito a líderes.'}), 403
    
    db = get_db()
    user_id = session.get('user_id')
    etapa_id = request.form.get('etapa_id')
    
    try:
        db.execute_query("""
            DELETE FROM lider_etapas 
            WHERE lider_id = %s AND etapa_id = %s
        """, (user_id, etapa_id))
        
        return jsonify({'success': True, 'message': 'Etapa removida do controle!'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
