"""
Rotas para Especificações Técnicas de Produtos (DNA do Produto)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from database import get_db

produto_especificacoes_bp = Blueprint('produto_especificacoes', __name__, url_prefix='/produtos/especificacoes')


@produto_especificacoes_bp.route('/<int:produto_id>', methods=['GET'])
def visualizar(produto_id):
    """Visualiza especificações técnicas de um produto."""
    db = get_db()
    
    produto = db.fetch_one("SELECT * FROM products WHERE id = %s", (produto_id,))
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('produtos.listar'))
    
    especificacao = db.fetch_one("""
        SELECT e.*, 
               tc.codigo as tipo_codigo, tc.nome as tipo_nome,
               mc.codigo as material_codigo, mc.nome as material_nome,
               pc.codigo as perfil_codigo, pc.nome as perfil_nome
        FROM produto_especificacoes_tecnicas e
        LEFT JOIN tipos_correia tc ON tc.id = e.tipo_correia_id
        LEFT JOIN materiais_correia mc ON mc.id = e.material_base_id
        LEFT JOIN perfis_correia pc ON pc.id = e.perfil_id
        WHERE e.produto_id = %s
    """, (produto_id,))
    
    return render_template('produtos/especificacoes_view.html',
                         produto=produto,
                         especificacao=especificacao)


@produto_especificacoes_bp.route('/<int:produto_id>/editar', methods=['GET', 'POST'])
def editar(produto_id):
    """Edita ou cria especificações técnicas de um produto."""
    db = get_db()
    
    produto = db.fetch_one("SELECT * FROM products WHERE id = %s", (produto_id,))
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('produtos.listar'))
    
    # Buscar lookups
    tipos_correia = db.fetch_all("SELECT * FROM tipos_correia WHERE ativo = 1 ORDER BY nome")
    materiais = db.fetch_all("SELECT * FROM materiais_correia WHERE ativo = 1 ORDER BY nome")
    perfis = db.fetch_all("SELECT * FROM perfis_correia WHERE ativo = 1 ORDER BY codigo")
    
    # Buscar especificação existente
    especificacao = db.fetch_one("""
        SELECT * FROM produto_especificacoes_tecnicas WHERE produto_id = %s
    """, (produto_id,))
    
    if request.method == 'POST':
        try:
            # Coletar dados do formulário
            dados = {
                'largura_mm': request.form.get('largura_mm') or None,
                'comprimento_mm': request.form.get('comprimento_mm') or None,
                'espessura_mm': request.form.get('espessura_mm') or None,
                'tipo_correia_id': request.form.get('tipo_correia_id') or None,
                'material_base_id': request.form.get('material_base_id') or None,
                'perfil_id': request.form.get('perfil_id') or None,
                'material_revestimento': request.form.get('material_revestimento') or None,
                'cor': request.form.get('cor') or None,
                'dureza_shore': request.form.get('dureza_shore') or None,
                'passo_mm': request.form.get('passo_mm') or None,
                'numero_dentes': request.form.get('numero_dentes') or None,
                'largura_dente_mm': request.form.get('largura_dente_mm') or None,
                'numero_lonas': request.form.get('numero_lonas') or None,
                'tipo_lona': request.form.get('tipo_lona') or None,
                'reforco': request.form.get('reforco') or None,
                'tipo_emenda': request.form.get('tipo_emenda') or None,
                'acabamento_borda': request.form.get('acabamento_borda') or None,
                'temperatura_min': request.form.get('temperatura_min') or None,
                'temperatura_max': request.form.get('temperatura_max') or None,
                'velocidade_max': request.form.get('velocidade_max') or None,
                'carga_max_kg': request.form.get('carga_max_kg') or None,
                'aplicacao': request.form.get('aplicacao') or None,
                'ambiente': request.form.get('ambiente') or None,
                'norma_tecnica': request.form.get('norma_tecnica') or None,
                'certificacoes': request.form.get('certificacoes') or None,
                'observacoes_tecnicas': request.form.get('observacoes_tecnicas') or None,
            }
            
            if especificacao:
                # Atualizar
                db.execute_query("""
                    UPDATE produto_especificacoes_tecnicas SET
                        largura_mm = %s, comprimento_mm = %s, espessura_mm = %s,
                        tipo_correia_id = %s, material_base_id = %s, perfil_id = %s,
                        material_revestimento = %s, cor = %s, dureza_shore = %s,
                        passo_mm = %s, numero_dentes = %s, largura_dente_mm = %s,
                        numero_lonas = %s, tipo_lona = %s, reforco = %s,
                        tipo_emenda = %s, acabamento_borda = %s,
                        temperatura_min = %s, temperatura_max = %s,
                        velocidade_max = %s, carga_max_kg = %s,
                        aplicacao = %s, ambiente = %s,
                        norma_tecnica = %s, certificacoes = %s,
                        observacoes_tecnicas = %s,
                        updated_by = %s
                    WHERE produto_id = %s
                """, (
                    dados['largura_mm'], dados['comprimento_mm'], dados['espessura_mm'],
                    dados['tipo_correia_id'], dados['material_base_id'], dados['perfil_id'],
                    dados['material_revestimento'], dados['cor'], dados['dureza_shore'],
                    dados['passo_mm'], dados['numero_dentes'], dados['largura_dente_mm'],
                    dados['numero_lonas'], dados['tipo_lona'], dados['reforco'],
                    dados['tipo_emenda'], dados['acabamento_borda'],
                    dados['temperatura_min'], dados['temperatura_max'],
                    dados['velocidade_max'], dados['carga_max_kg'],
                    dados['aplicacao'], dados['ambiente'],
                    dados['norma_tecnica'], dados['certificacoes'],
                    dados['observacoes_tecnicas'],
                    session.get('user_id'),
                    produto_id
                ))
                flash('Especificações técnicas atualizadas com sucesso!', 'success')
            else:
                # Inserir
                db.insert("""
                    INSERT INTO produto_especificacoes_tecnicas (
                        produto_id, largura_mm, comprimento_mm, espessura_mm,
                        tipo_correia_id, material_base_id, perfil_id,
                        material_revestimento, cor, dureza_shore,
                        passo_mm, numero_dentes, largura_dente_mm,
                        numero_lonas, tipo_lona, reforco,
                        tipo_emenda, acabamento_borda,
                        temperatura_min, temperatura_max,
                        velocidade_max, carga_max_kg,
                        aplicacao, ambiente,
                        norma_tecnica, certificacoes,
                        observacoes_tecnicas,
                        created_by
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    produto_id,
                    dados['largura_mm'], dados['comprimento_mm'], dados['espessura_mm'],
                    dados['tipo_correia_id'], dados['material_base_id'], dados['perfil_id'],
                    dados['material_revestimento'], dados['cor'], dados['dureza_shore'],
                    dados['passo_mm'], dados['numero_dentes'], dados['largura_dente_mm'],
                    dados['numero_lonas'], dados['tipo_lona'], dados['reforco'],
                    dados['tipo_emenda'], dados['acabamento_borda'],
                    dados['temperatura_min'], dados['temperatura_max'],
                    dados['velocidade_max'], dados['carga_max_kg'],
                    dados['aplicacao'], dados['ambiente'],
                    dados['norma_tecnica'], dados['certificacoes'],
                    dados['observacoes_tecnicas'],
                    session.get('user_id')
                ))
                
                # Atualizar tipo industrial do produto
                db.execute_query(
                    "UPDATE products SET tipo_produto_industrial = 'correia' WHERE id = %s",
                    (produto_id,)
                )
                flash('Especificações técnicas cadastradas com sucesso!', 'success')
            
            return redirect(url_for('produto_especificacoes.visualizar', produto_id=produto_id))
            
        except Exception as e:
            flash(f'Erro ao salvar especificações: {str(e)}', 'danger')
    
    return render_template('produtos/especificacoes_form.html',
                         produto=produto,
                         especificacao=especificacao,
                         tipos_correia=tipos_correia,
                         materiais=materiais,
                         perfis=perfis)


@produto_especificacoes_bp.route('/api/perfis/<tipo_correia_codigo>', methods=['GET'])
def api_perfis_por_tipo(tipo_correia_codigo):
    """Retorna perfis compatíveis com um tipo de correia."""
    db = get_db()
    
    perfis = db.fetch_all("""
        SELECT id, codigo, nome, passo_padrao_mm
        FROM perfis_correia 
        WHERE (tipo_correia_codigo = %s OR tipo_correia_codigo IS NULL)
          AND ativo = 1
        ORDER BY codigo
    """, (tipo_correia_codigo,))
    
    return jsonify(perfis or [])


@produto_especificacoes_bp.route('/api/gerar-dna', methods=['POST'])
def api_gerar_dna():
    """Gera código DNA baseado nos parâmetros."""
    db = get_db()
    
    tipo_id = request.json.get('tipo_correia_id')
    material_id = request.json.get('material_base_id')
    perfil_id = request.json.get('perfil_id')
    dureza = request.json.get('dureza_shore') or 0
    lonas = request.json.get('numero_lonas') or 0
    emenda = request.json.get('tipo_emenda') or ''
    
    # Buscar códigos
    tipo_cod = ''
    if tipo_id:
        t = db.fetch_one("SELECT codigo FROM tipos_correia WHERE id = %s", (tipo_id,))
        tipo_cod = t['codigo'] if t else 'XXX'
    
    mat_cod = ''
    if material_id:
        m = db.fetch_one("SELECT codigo FROM materiais_correia WHERE id = %s", (material_id,))
        mat_cod = m['codigo'] if m else 'XXX'
    
    perfil_cod = ''
    if perfil_id:
        p = db.fetch_one("SELECT codigo FROM perfis_correia WHERE id = %s", (perfil_id,))
        perfil_cod = p['codigo'] if p else 'XXX'
    
    # Código emenda
    emenda_cod = 'SEM'
    if 'Vulcan' in emenda:
        emenda_cod = 'VUL'
    elif 'Mec' in emenda:
        emenda_cod = 'MEC'
    elif 'Sold' in emenda:
        emenda_cod = 'SOL'
    
    # Montar DNA
    dna = f"{tipo_cod or 'XXX'}-{mat_cod or 'XXX'}-{perfil_cod or 'XXX'}-{int(dureza)}-{lonas}L-{emenda_cod}"
    
    return jsonify({'codigo_dna': dna})


@produto_especificacoes_bp.route('/api/buscar-similares/<int:produto_id>', methods=['GET'])
def api_buscar_similares(produto_id):
    """Busca produtos com DNA similar."""
    db = get_db()
    
    # Buscar especificação do produto
    esp = db.fetch_one("""
        SELECT e.*, tc.codigo as tipo_cod, mc.codigo as mat_cod
        FROM produto_especificacoes_tecnicas e
        LEFT JOIN tipos_correia tc ON tc.id = e.tipo_correia_id
        LEFT JOIN materiais_correia mc ON mc.id = e.material_base_id
        WHERE e.produto_id = %s
    """, (produto_id,))
    
    if not esp:
        return jsonify({'similares': [], 'message': 'Produto sem especificação técnica'})
    
    # Buscar similares com mesmo DNA base (ignora dimensões)
    similares = db.fetch_all("""
        SELECT 
            p.id, p.name, p.stock_quantity,
            e.largura_mm, e.comprimento_mm, e.codigo_dna,
            CASE 
                WHEN e.largura_mm = %s AND e.comprimento_mm = %s THEN 'EXATO'
                WHEN e.largura_mm >= %s AND e.comprimento_mm >= %s THEN 'DERIVAVEL'
                ELSE 'PARCIAL'
            END as tipo_match
        FROM products p
        INNER JOIN produto_especificacoes_tecnicas e ON e.produto_id = p.id
        WHERE p.id != %s
          AND e.tipo_correia_id = %s
          AND e.material_base_id = %s
          AND p.stock_quantity > 0
        ORDER BY 
            CASE WHEN e.largura_mm = %s AND e.comprimento_mm = %s THEN 1 ELSE 2 END,
            (e.largura_mm - %s) + (e.comprimento_mm - %s) ASC
        LIMIT 10
    """, (
        esp['largura_mm'], esp['comprimento_mm'],
        esp['largura_mm'], esp['comprimento_mm'],
        produto_id,
        esp['tipo_correia_id'], esp['material_base_id'],
        esp['largura_mm'], esp['comprimento_mm'],
        esp['largura_mm'], esp['comprimento_mm']
    ))
    
    return jsonify({'similares': similares or [], 'produto_dna': esp['codigo_dna']})
