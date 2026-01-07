"""
Rotas para gerenciamento de Fichas Técnicas (Templates de Produção)
Permite listar, visualizar, editar e criar fichas técnicas para produtos
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.database import get_db
from datetime import datetime

ficha_tecnica_bp = Blueprint('ficha_tecnica', __name__, url_prefix='/produtos/fichas-tecnicas')


@ficha_tecnica_bp.route('/')
def listar():
    """Lista todas as fichas técnicas cadastradas"""
    db = get_db()
    
    # Filtros
    busca = request.args.get('busca', '').strip()
    tipo_produto = request.args.get('tipo', '')
    apenas_ativos = request.args.get('ativos', '1') == '1'
    
    # Query base
    query = """
        SELECT 
            t.id,
            t.produto_id,
            t.versao,
            t.nome_template,
            t.custo_total_base,
            t.tempo_producao_horas,
            t.ativo,
            t.created_at,
            t.updated_at,
            p.name as produto_nome,
            p.internal_code as produto_codigo,
            (SELECT COUNT(*) FROM produto_template_itens WHERE template_id = t.id) as qtd_itens
        FROM produto_templates_producao t
        INNER JOIN products p ON t.produto_id = p.id
        WHERE 1=1
    """
    params = []
    
    if busca:
        query += " AND (p.name LIKE %s OR p.internal_code LIKE %s OR t.nome_template LIKE %s)"
        params.extend([f'%{busca}%', f'%{busca}%', f'%{busca}%'])
    
    if tipo_produto:
        if tipo_produto == 'CS':
            query += " AND p.name LIKE 'CS %'"
        elif tipo_produto == 'PV':
            query += " AND p.name LIKE 'PV %'"
        elif tipo_produto == 'CP':
            query += " AND (p.name LIKE 'CP %' OR p.name LIKE 'CORREIA PLANA%')"
        elif tipo_produto == 'CT':
            query += " AND (p.name LIKE 'CT %' OR p.name LIKE 'CORREIA TRANSP%')"
        elif tipo_produto == 'HTD':
            query += " AND p.name LIKE '%HTD%'"
    
    if apenas_ativos:
        query += " AND t.ativo = 1"
    
    query += " ORDER BY p.name, t.versao DESC LIMIT 100"
    
    fichas = db.fetch_all(query, params) or []
    
    # Estatísticas
    stats = db.fetch_one("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN ativo = 1 THEN 1 ELSE 0 END) as ativos,
            SUM(CASE WHEN ativo = 0 THEN 1 ELSE 0 END) as inativos
        FROM produto_templates_producao
    """)
    
    return render_template('produtos/ficha_tecnica_lista.html',
        fichas=fichas,
        stats=stats or {'total': 0, 'ativos': 0, 'inativos': 0},
        filtros={
            'busca': busca,
            'tipo': tipo_produto,
            'ativos': apenas_ativos
        }
    )


@ficha_tecnica_bp.route('/<int:id>')
def visualizar(id):
    """Visualiza uma ficha técnica"""
    db = get_db()
    
    ficha = db.fetch_one("""
        SELECT 
            t.*,
            p.name as produto_nome,
            p.internal_code as produto_codigo,
            p.unit_measure as produto_unidade,
            p.cost_price as produto_custo_atual
        FROM produto_templates_producao t
        INNER JOIN products p ON t.produto_id = p.id
        WHERE t.id = %s
    """, [id])
    
    if not ficha:
        flash('Ficha técnica não encontrada.', 'danger')
        return redirect(url_for('ficha_tecnica.listar'))
    
    # Buscar itens agrupados por tipo
    itens = db.fetch_all("""
        SELECT 
            i.*,
            p.name as produto_nome,
            p.internal_code as produto_codigo,
            p.cost_price as custo_atual,
            p.unit_measure as unidade_produto
        FROM produto_template_itens i
        LEFT JOIN products p ON i.produto_id = p.id
        WHERE i.template_id = %s
        ORDER BY i.tipo_item, i.id
    """, [id])
    
    # Separar por tipo
    servicos = [i for i in (itens or []) if i['tipo_item'] == 'servico']
    materias_primas = [i for i in (itens or []) if i['tipo_item'] == 'materia_prima']
    consumo_interno = [i for i in (itens or []) if i['tipo_item'] == 'consumo_interno']
    
    # Calcular totais
    total_servicos = sum(float(i['custo_total_base'] or 0) for i in servicos)
    total_materias = sum(float(i['custo_total_base'] or 0) for i in materias_primas)
    total_consumo = sum(float(i['custo_total_base'] or 0) for i in consumo_interno)
    
    # =====================================================
    # HISTÓRICO DE PRODUÇÃO - Últimas 10 OPs concluídas
    # =====================================================
    produto_id = ficha['produto_id']
    
    # Buscar últimas 10 OPs concluídas deste produto
    ultimas_ops = db.fetch_all("""
        SELECT 
            op.id,
            op.numero_op,
            op.quantidade,
            op.data_inicio_producao,
            op.data_conclusao,
            TIMESTAMPDIFF(MINUTE, op.data_inicio_producao, op.data_conclusao) as tempo_total_minutos,
            (SELECT COUNT(*) FROM op_lotes l WHERE l.ordem_producao_id = op.id) as qtd_lotes
        FROM ordens_producao op
        WHERE op.produto_id = %s 
          AND op.status = 'concluida'
          AND op.data_inicio_producao IS NOT NULL
          AND op.data_conclusao IS NOT NULL
        ORDER BY op.data_conclusao DESC
        LIMIT 10
    """, [produto_id]) or []
    
    # Calcular resumo das últimas OPs
    total_quantidade_produzida = sum(int(op.get('quantidade') or 0) for op in ultimas_ops)
    total_tempo_minutos = sum(int(op.get('tempo_total_minutos') or 0) for op in ultimas_ops)
    
    # Tempo por unidade (em minutos)
    tempo_por_unidade_min = 0
    if total_quantidade_produzida > 0 and total_tempo_minutos > 0:
        tempo_por_unidade_min = total_tempo_minutos / total_quantidade_produzida
    
    # Converter para horas e minutos
    tempo_por_unidade_horas = tempo_por_unidade_min / 60 if tempo_por_unidade_min > 0 else 0
    
    # Buscar tempo médio por etapa das últimas OPs
    tempos_etapas = db.fetch_all("""
        SELECT 
            e.id as etapa_id,
            e.nome as etapa_nome,
            e.ordem,
            COUNT(DISTINCT log.id) as qtd_registros,
            AVG(TIMESTAMPDIFF(MINUTE, log.created_at, 
                COALESCE(
                    (SELECT MIN(log2.created_at) 
                     FROM op_lotes_etapas_log log2 
                     WHERE log2.lote_id = log.lote_id 
                       AND log2.created_at > log.created_at),
                    l.data_fim_operador
                )
            )) as tempo_medio_minutos,
            MIN(TIMESTAMPDIFF(MINUTE, log.created_at, 
                COALESCE(
                    (SELECT MIN(log2.created_at) 
                     FROM op_lotes_etapas_log log2 
                     WHERE log2.lote_id = log.lote_id 
                       AND log2.created_at > log.created_at),
                    l.data_fim_operador
                )
            )) as tempo_min_minutos,
            MAX(TIMESTAMPDIFF(MINUTE, log.created_at, 
                COALESCE(
                    (SELECT MIN(log2.created_at) 
                     FROM op_lotes_etapas_log log2 
                     WHERE log2.lote_id = log.lote_id 
                       AND log2.created_at > log.created_at),
                    l.data_fim_operador
                )
            )) as tempo_max_minutos
        FROM op_lotes_etapas_log log
        INNER JOIN op_lotes l ON log.lote_id = l.id
        INNER JOIN ordens_producao op ON l.ordem_producao_id = op.id
        INNER JOIN producao_etapas e ON log.etapa_nova_id = e.id
        WHERE op.produto_id = %s
          AND op.status = 'concluida'
          AND op.data_conclusao >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY e.id, e.nome, e.ordem
        HAVING tempo_medio_minutos > 0 AND tempo_medio_minutos < 1440
        ORDER BY e.ordem
    """, [produto_id]) or []
    
    # Resumo do histórico
    historico_producao = {
        'ultimas_ops': ultimas_ops,
        'total_ops': len(ultimas_ops),
        'total_quantidade': total_quantidade_produzida,
        'total_tempo_minutos': total_tempo_minutos,
        'total_tempo_horas': round(total_tempo_minutos / 60, 2) if total_tempo_minutos > 0 else 0,
        'tempo_por_unidade_minutos': round(tempo_por_unidade_min, 2),
        'tempo_por_unidade_horas': round(tempo_por_unidade_horas, 4),
        'tempos_etapas': tempos_etapas
    }
    
    return render_template('produtos/ficha_tecnica_view.html',
        ficha=ficha,
        servicos=servicos,
        materias_primas=materias_primas,
        consumo_interno=consumo_interno,
        totais={
            'servicos': total_servicos,
            'materias_primas': total_materias,
            'consumo_interno': total_consumo,
            'total': total_servicos + total_materias + total_consumo
        },
        historico_producao=historico_producao
    )


@ficha_tecnica_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    """Edita uma ficha técnica"""
    db = get_db()
    
    ficha = db.fetch_one("""
        SELECT 
            t.*,
            p.name as produto_nome,
            p.internal_code as produto_codigo
        FROM produto_templates_producao t
        INNER JOIN products p ON t.produto_id = p.id
        WHERE t.id = %s
    """, [id])
    
    if not ficha:
        flash('Ficha técnica não encontrada.', 'danger')
        return redirect(url_for('ficha_tecnica.listar'))
    
    if request.method == 'POST':
        try:
            nome_template = request.form.get('nome_template', '').strip()
            tempo_horas = float(request.form.get('tempo_producao_horas') or 0)
            observacoes = request.form.get('observacoes', '').strip()
            ativo = request.form.get('ativo') == '1'
            
            # Processar itens
            itens_json = request.form.get('itens_json', '[]')
            import json
            itens = json.loads(itens_json)
            
            # Calcular custo total
            custo_total = sum(float(item.get('custo_total', 0)) for item in itens)
            
            # Atualizar ficha
            db.execute_query("""
                UPDATE produto_templates_producao 
                SET nome_template = %s,
                    custo_total_base = %s,
                    tempo_producao_horas = %s,
                    observacoes = %s,
                    ativo = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, [nome_template, custo_total, tempo_horas, observacoes, 1 if ativo else 0, id])
            
            # Remover itens antigos e inserir novos
            db.execute_query("DELETE FROM produto_template_itens WHERE template_id = %s", [id])
            
            for item in itens:
                db.execute_query("""
                    INSERT INTO produto_template_itens 
                    (template_id, tipo_item, produto_id, descricao, quantidade, 
                     unidade_medida, custo_unitario_base, custo_total_base)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    id,
                    item.get('tipo_item'),
                    item.get('produto_id') or None,
                    item.get('descricao', ''),
                    float(item.get('quantidade', 0)),
                    item.get('unidade_medida', 'UN'),
                    float(item.get('custo_unitario', 0)),
                    float(item.get('custo_total', 0))
                ])
            
            flash('Ficha técnica atualizada com sucesso!', 'success')
            return redirect(url_for('ficha_tecnica.visualizar', id=id))
            
        except Exception as e:
            print(f"[FICHA TECNICA] Erro ao salvar: {e}")
            import traceback
            traceback.print_exc()
            flash(f'Erro ao salvar ficha técnica: {str(e)}', 'danger')
    
    # GET - Carregar dados para edição
    itens = db.fetch_all("""
        SELECT 
            i.*,
            p.name as produto_nome,
            p.internal_code as produto_codigo,
            p.cost_price as custo_atual
        FROM produto_template_itens i
        LEFT JOIN products p ON i.produto_id = p.id
        WHERE i.template_id = %s
        ORDER BY i.tipo_item, i.id
    """, [id])
    
    # Buscar produtos para autocomplete (serviços e matérias-primas)
    servicos_disponiveis = db.fetch_all("""
        SELECT id, internal_code as codigo, name as nome, cost_price as custo, unit_measure as unidade
        FROM products WHERE category_id = 2 ORDER BY name LIMIT 100
    """) or []
    
    materias_disponiveis = db.fetch_all("""
        SELECT id, internal_code as codigo, name as nome, cost_price as custo, unit_measure as unidade
        FROM products WHERE category_id = 3 ORDER BY name LIMIT 100
    """) or []
    
    # =====================================================
    # HISTÓRICO DE PRODUÇÃO - Últimas 10 OPs concluídas
    # =====================================================
    produto_id = ficha['produto_id']
    
    # Buscar últimas 10 OPs concluídas deste produto
    ultimas_ops = db.fetch_all("""
        SELECT 
            op.id,
            op.numero_op,
            op.quantidade,
            op.data_inicio_producao,
            op.data_conclusao,
            TIMESTAMPDIFF(MINUTE, op.data_inicio_producao, op.data_conclusao) as tempo_total_minutos,
            (SELECT COUNT(*) FROM op_lotes l WHERE l.ordem_producao_id = op.id) as qtd_lotes
        FROM ordens_producao op
        WHERE op.produto_id = %s 
          AND op.status = 'concluida'
          AND op.data_inicio_producao IS NOT NULL
          AND op.data_conclusao IS NOT NULL
        ORDER BY op.data_conclusao DESC
        LIMIT 10
    """, [produto_id]) or []
    
    # Calcular resumo das últimas OPs
    total_quantidade_produzida = sum(int(op.get('quantidade') or 0) for op in ultimas_ops)
    total_tempo_minutos = sum(int(op.get('tempo_total_minutos') or 0) for op in ultimas_ops)
    
    # Tempo por unidade (em minutos)
    tempo_por_unidade_min = 0
    if total_quantidade_produzida > 0 and total_tempo_minutos > 0:
        tempo_por_unidade_min = total_tempo_minutos / total_quantidade_produzida
    
    # Converter para horas
    tempo_por_unidade_horas = tempo_por_unidade_min / 60 if tempo_por_unidade_min > 0 else 0
    
    # Buscar tempo médio por etapa das últimas OPs
    tempos_etapas = db.fetch_all("""
        SELECT 
            e.id as etapa_id,
            e.nome as etapa_nome,
            e.ordem,
            COUNT(DISTINCT log.id) as qtd_registros,
            AVG(TIMESTAMPDIFF(MINUTE, log.created_at, 
                COALESCE(
                    (SELECT MIN(log2.created_at) 
                     FROM op_lotes_etapas_log log2 
                     WHERE log2.lote_id = log.lote_id 
                       AND log2.created_at > log.created_at),
                    l.data_fim_operador
                )
            )) as tempo_medio_minutos,
            MIN(TIMESTAMPDIFF(MINUTE, log.created_at, 
                COALESCE(
                    (SELECT MIN(log2.created_at) 
                     FROM op_lotes_etapas_log log2 
                     WHERE log2.lote_id = log.lote_id 
                       AND log2.created_at > log.created_at),
                    l.data_fim_operador
                )
            )) as tempo_min_minutos,
            MAX(TIMESTAMPDIFF(MINUTE, log.created_at, 
                COALESCE(
                    (SELECT MIN(log2.created_at) 
                     FROM op_lotes_etapas_log log2 
                     WHERE log2.lote_id = log.lote_id 
                       AND log2.created_at > log.created_at),
                    l.data_fim_operador
                )
            )) as tempo_max_minutos
        FROM op_lotes_etapas_log log
        INNER JOIN op_lotes l ON log.lote_id = l.id
        INNER JOIN ordens_producao op ON l.ordem_producao_id = op.id
        INNER JOIN producao_etapas e ON log.etapa_nova_id = e.id
        WHERE op.produto_id = %s
          AND op.status = 'concluida'
          AND op.data_conclusao >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY e.id, e.nome, e.ordem
        HAVING tempo_medio_minutos > 0 AND tempo_medio_minutos < 1440
        ORDER BY e.ordem
    """, [produto_id]) or []
    
    # Resumo do histórico
    historico_producao = {
        'ultimas_ops': ultimas_ops,
        'total_ops': len(ultimas_ops),
        'total_quantidade': total_quantidade_produzida,
        'total_tempo_minutos': total_tempo_minutos,
        'total_tempo_horas': round(total_tempo_minutos / 60, 2) if total_tempo_minutos > 0 else 0,
        'tempo_por_unidade_minutos': round(tempo_por_unidade_min, 2),
        'tempo_por_unidade_horas': round(tempo_por_unidade_horas, 4),
        'tempos_etapas': tempos_etapas
    }
    
    return render_template('produtos/ficha_tecnica_form.html',
        ficha=ficha,
        itens=itens or [],
        servicos_disponiveis=servicos_disponiveis,
        materias_disponiveis=materias_disponiveis,
        historico_producao=historico_producao
    )


@ficha_tecnica_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    """Cria uma nova ficha técnica"""
    db = get_db()
    
    if request.method == 'POST':
        try:
            produto_id = int(request.form.get('produto_id'))
            nome_template = request.form.get('nome_template', '').strip()
            tempo_horas = float(request.form.get('tempo_producao_horas') or 0)
            observacoes = request.form.get('observacoes', '').strip()
            
            # Verificar se produto existe
            produto = db.fetch_one("SELECT id, name FROM products WHERE id = %s", [produto_id])
            if not produto:
                flash('Produto não encontrado.', 'danger')
                return redirect(url_for('ficha_tecnica.novo'))
            
            # Próxima versão
            versao_atual = db.fetch_one(
                "SELECT MAX(versao) as v FROM produto_templates_producao WHERE produto_id = %s",
                [produto_id]
            )
            prox_versao = int((versao_atual or {}).get('v') or 0) + 1
            
            # Desativar templates anteriores
            db.execute_query(
                "UPDATE produto_templates_producao SET ativo = 0 WHERE produto_id = %s AND ativo = 1",
                [produto_id]
            )
            
            # Criar nova ficha
            ficha_id = db.insert("""
                INSERT INTO produto_templates_producao 
                (produto_id, versao, nome_template, custo_total_base, tempo_producao_horas, ativo, observacoes)
                VALUES (%s, %s, %s, 0, %s, 1, %s)
            """, [produto_id, prox_versao, nome_template or f'Ficha Técnica - {produto["name"]}', tempo_horas, observacoes])
            
            flash('Ficha técnica criada com sucesso! Adicione os itens.', 'success')
            return redirect(url_for('ficha_tecnica.editar', id=ficha_id))
            
        except Exception as e:
            print(f"[FICHA TECNICA] Erro ao criar: {e}")
            flash(f'Erro ao criar ficha técnica: {str(e)}', 'danger')
    
    # GET - Formulário de criação
    # Buscar produtos que podem ter ficha técnica (categoria 6 = Produto Produzido)
    produtos = db.fetch_all("""
        SELECT p.id, p.internal_code as codigo, p.name as nome,
               (SELECT COUNT(*) FROM produto_templates_producao t WHERE t.produto_id = p.id AND t.ativo = 1) as tem_ficha
        FROM products p
        WHERE p.category_id = 6
        ORDER BY p.name
        LIMIT 500
    """) or []
    
    return render_template('produtos/ficha_tecnica_novo.html',
        produtos=produtos
    )


@ficha_tecnica_bp.route('/<int:id>/duplicar', methods=['POST'])
def duplicar(id):
    """Duplica uma ficha técnica para outro produto"""
    db = get_db()
    
    produto_destino_id = request.form.get('produto_destino_id')
    if not produto_destino_id:
        flash('Selecione um produto de destino.', 'danger')
        return redirect(url_for('ficha_tecnica.visualizar', id=id))
    
    try:
        # Buscar ficha origem
        origem = db.fetch_one("""
            SELECT * FROM produto_templates_producao WHERE id = %s
        """, [id])
        
        if not origem:
            flash('Ficha de origem não encontrada.', 'danger')
            return redirect(url_for('ficha_tecnica.listar'))
        
        # Buscar produto destino
        produto_destino = db.fetch_one("SELECT id, name FROM products WHERE id = %s", [produto_destino_id])
        if not produto_destino:
            flash('Produto de destino não encontrado.', 'danger')
            return redirect(url_for('ficha_tecnica.visualizar', id=id))
        
        # Próxima versão
        versao_atual = db.fetch_one(
            "SELECT MAX(versao) as v FROM produto_templates_producao WHERE produto_id = %s",
            [produto_destino_id]
        )
        prox_versao = int((versao_atual or {}).get('v') or 0) + 1
        
        # Desativar templates anteriores do destino
        db.execute_query(
            "UPDATE produto_templates_producao SET ativo = 0 WHERE produto_id = %s AND ativo = 1",
            [produto_destino_id]
        )
        
        # Criar nova ficha
        nova_ficha_id = db.insert("""
            INSERT INTO produto_templates_producao 
            (produto_id, versao, nome_template, custo_total_base, tempo_producao_horas, ativo, observacoes)
            VALUES (%s, %s, %s, %s, %s, 1, %s)
        """, [
            produto_destino_id,
            prox_versao,
            f'Ficha Técnica - {produto_destino["name"]}',
            origem['custo_total_base'],
            origem['tempo_producao_horas'],
            origem['observacoes']
        ])
        
        # Copiar itens
        itens_origem = db.fetch_all(
            "SELECT * FROM produto_template_itens WHERE template_id = %s", [id]
        )
        
        for item in (itens_origem or []):
            db.execute_query("""
                INSERT INTO produto_template_itens 
                (template_id, tipo_item, produto_id, descricao, quantidade, 
                 unidade_medida, custo_unitario_base, custo_total_base)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                nova_ficha_id,
                item['tipo_item'],
                item['produto_id'],
                item['descricao'],
                item['quantidade'],
                item['unidade_medida'],
                item['custo_unitario_base'],
                item['custo_total_base']
            ])
        
        flash(f'Ficha técnica duplicada com sucesso para {produto_destino["name"]}!', 'success')
        return redirect(url_for('ficha_tecnica.editar', id=nova_ficha_id))
        
    except Exception as e:
        print(f"[FICHA TECNICA] Erro ao duplicar: {e}")
        flash(f'Erro ao duplicar ficha técnica: {str(e)}', 'danger')
        return redirect(url_for('ficha_tecnica.visualizar', id=id))


@ficha_tecnica_bp.route('/<int:id>/excluir', methods=['POST'])
def excluir(id):
    """Exclui uma ficha técnica"""
    db = get_db()
    
    try:
        # Verificar se existe
        ficha = db.fetch_one("SELECT id FROM produto_templates_producao WHERE id = %s", [id])
        if not ficha:
            flash('Ficha técnica não encontrada.', 'danger')
            return redirect(url_for('ficha_tecnica.listar'))
        
        # Excluir itens
        db.execute_query("DELETE FROM produto_template_itens WHERE template_id = %s", [id])
        
        # Excluir ficha
        db.execute_query("DELETE FROM produto_templates_producao WHERE id = %s", [id])
        
        flash('Ficha técnica excluída com sucesso!', 'success')
        
    except Exception as e:
        print(f"[FICHA TECNICA] Erro ao excluir: {e}")
        flash(f'Erro ao excluir ficha técnica: {str(e)}', 'danger')
    
    return redirect(url_for('ficha_tecnica.listar'))


# =====================================================
# APIs JSON
# =====================================================

@ficha_tecnica_bp.route('/api/buscar-produtos')
def api_buscar_produtos():
    """API para buscar produtos para autocomplete"""
    db = get_db()
    termo = request.args.get('q', '').strip()
    categoria = request.args.get('categoria', '')
    
    query = """
        SELECT id, internal_code as codigo, name as nome, cost_price as custo, unit_measure as unidade
        FROM products
        WHERE (name LIKE %s OR internal_code LIKE %s)
    """
    params = [f'%{termo}%', f'%{termo}%']
    
    if categoria:
        query += " AND category_id = %s"
        params.append(int(categoria))
    
    query += " ORDER BY name LIMIT 20"
    
    produtos = db.fetch_all(query, params) or []
    
    return jsonify([{
        'id': p['id'],
        'codigo': p['codigo'] or '',
        'nome': p['nome'],
        'custo': float(p['custo'] or 0),
        'unidade': p['unidade'] or 'UN'
    } for p in produtos])


@ficha_tecnica_bp.route('/<int:id>/atualizar-tempo-real', methods=['POST'])
def atualizar_tempo_real(id):
    """Atualiza o tempo de produção da ficha técnica com base no histórico real"""
    db = get_db()
    
    try:
        data = request.get_json() or {}
        tempo_por_unidade_horas = float(data.get('tempo_por_unidade_horas', 0))
        tempo_por_unidade_minutos = float(data.get('tempo_por_unidade_minutos', 0))
        
        if tempo_por_unidade_horas <= 0 and tempo_por_unidade_minutos <= 0:
            return jsonify({'success': False, 'error': 'Tempo inválido ou não calculado'})
        
        # Buscar ficha
        ficha = db.fetch_one("""
            SELECT t.id, t.produto_id, t.tempo_producao_horas
            FROM produto_templates_producao t
            WHERE t.id = %s
        """, [id])
        
        if not ficha:
            return jsonify({'success': False, 'error': 'Ficha técnica não encontrada'})
        
        # Atualizar tempo de produção na ficha
        db.execute_query("""
            UPDATE produto_templates_producao 
            SET tempo_producao_horas = %s,
                observacoes = CONCAT(COALESCE(observacoes, ''), '\n[', NOW(), '] Tempo atualizado automaticamente do histórico: ', %s, 'h/unidade'),
                updated_at = NOW()
            WHERE id = %s
        """, [round(tempo_por_unidade_horas, 4), round(tempo_por_unidade_horas, 4), id])
        
        # Buscar e atualizar item de serviço principal (se existir)
        # Procura por itens de serviço que parecem ser o serviço principal de produção
        servico_principal = db.fetch_one("""
            SELECT id, quantidade, custo_unitario_base
            FROM produto_template_itens
            WHERE template_id = %s 
              AND tipo_item = 'servico'
            ORDER BY custo_total_base DESC
            LIMIT 1
        """, [id])
        
        if servico_principal:
            # Atualizar a quantidade do serviço para refletir o tempo real
            # Se o serviço é por hora, atualiza a quantidade de horas
            db.execute_query("""
                UPDATE produto_template_itens
                SET quantidade = %s,
                    custo_total_base = %s * custo_unitario_base
                WHERE id = %s
            """, [round(tempo_por_unidade_horas, 4), round(tempo_por_unidade_horas, 4), servico_principal['id']])
            
            # Recalcular custo total da ficha
            novo_custo = db.fetch_one("""
                SELECT SUM(custo_total_base) as total
                FROM produto_template_itens
                WHERE template_id = %s
            """, [id])
            
            if novo_custo:
                db.execute_query("""
                    UPDATE produto_templates_producao
                    SET custo_total_base = %s
                    WHERE id = %s
                """, [float(novo_custo['total'] or 0), id])
        
        return jsonify({
            'success': True,
            'message': f'Tempo de produção atualizado para {round(tempo_por_unidade_horas, 4)}h por unidade',
            'tempo_atualizado': round(tempo_por_unidade_horas, 4)
        })
        
    except Exception as e:
        print(f"[FICHA TECNICA] Erro ao atualizar tempo real: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})
