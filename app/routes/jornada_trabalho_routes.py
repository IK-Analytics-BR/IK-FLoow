"""
Blueprint para Gestão de Jornadas de Trabalho
Módulo Indústria
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import get_db
from datetime import datetime, time

# Criar blueprint
jornada_trabalho_bp = Blueprint('jornada_trabalho', __name__, url_prefix='/industria/jornada-trabalho')


@jornada_trabalho_bp.route('/')
def listar_jornadas():
    """Lista todas as jornadas de trabalho cadastradas"""
    db = get_db()
    
    try:
        jornadas = db.fetch_all("""
            SELECT 
                jt.id,
                jt.nome,
                jt.descricao,
                e.nome_fantasia as empresa_nome,
                jt.ativo,
                jt.created_at,
                COUNT(DISTINCT jth.id) as total_horarios
            FROM jornadas_trabalho jt
            LEFT JOIN empresas e ON jt.empresa_id = e.id
            LEFT JOIN jornada_horarios jth ON jt.id = jth.jornada_id
            GROUP BY jt.id
            ORDER BY e.nome_fantasia, jt.nome
        """)
        
        return render_template('industria/jornada_trabalho_lista.html', jornadas=jornadas)
    
    except Exception as e:
        flash(f'Erro ao listar jornadas: {str(e)}', 'danger')
        return render_template('industria/jornada_trabalho_lista.html', jornadas=[])


@jornada_trabalho_bp.route('/nova')
def nova_jornada():
    """Formulário para criar nova jornada"""
    db = get_db()
    
    # Buscar empresas ativas
    empresas = db.fetch_all("""
        SELECT id, nome_fantasia, razao_social
        FROM empresas
        WHERE ativo = 1
        ORDER BY nome_fantasia
    """)
    
    return render_template('industria/jornada_trabalho_form.html', 
                         empresas=empresas, 
                         jornada=None,
                         horarios=[])


@jornada_trabalho_bp.route('/editar/<int:id>')
def editar_jornada(id):
    """Formulário para editar jornada existente"""
    db = get_db()
    
    # Buscar jornada
    jornada = db.fetch_one("""
        SELECT * FROM jornadas_trabalho WHERE id = %s
    """, (id,))
    
    if not jornada:
        flash('Jornada não encontrada!', 'danger')
        return redirect(url_for('jornada_trabalho.listar_jornadas'))
    
    # Buscar empresas
    empresas = db.fetch_all("""
        SELECT id, nome_fantasia, razao_social
        FROM empresas
        WHERE ativo = 1
        ORDER BY nome_fantasia
    """)
    
    # Buscar horários da jornada
    horarios = db.fetch_all("""
        SELECT * FROM jornada_horarios
        WHERE jornada_id = %s
        ORDER BY 
            FIELD(dia_semana, 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'),
            turno
    """, (id,))
    
    return render_template('industria/jornada_trabalho_form.html',
                         empresas=empresas,
                         jornada=jornada,
                         horarios=horarios)


@jornada_trabalho_bp.route('/salvar', methods=['POST'])
def salvar_jornada():
    """Salva nova jornada ou atualiza existente"""
    db = get_db()
    
    jornada_id = request.form.get('jornada_id')
    nome = request.form.get('nome')
    descricao = request.form.get('descricao')
    empresa_id = request.form.get('empresa_id')
    ativo = 1 if request.form.get('ativo') else 0
    
    # Validações
    if not nome or not empresa_id:
        flash('Nome e Empresa são obrigatórios!', 'danger')
        return redirect(url_for('jornada_trabalho.nova_jornada'))
    
    try:
        if jornada_id:
            # Atualizar jornada existente
            db.execute_query("""
                UPDATE jornadas_trabalho
                SET nome = %s,
                    descricao = %s,
                    empresa_id = %s,
                    ativo = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (nome, descricao, empresa_id, ativo, jornada_id))
            
            # Deletar horários antigos
            db.execute_query("DELETE FROM jornada_horarios WHERE jornada_id = %s", (jornada_id,))
            
            flash('Jornada atualizada com sucesso!', 'success')
            jornada_id_final = jornada_id
        else:
            # Criar nova jornada
            db.execute_query("""
                INSERT INTO jornadas_trabalho (nome, descricao, empresa_id, ativo, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (nome, descricao, empresa_id, ativo))
            
            jornada_id_final = db.fetch_one("SELECT LAST_INSERT_ID() as id")['id']
            flash('Jornada criada com sucesso!', 'success')
        
        # Salvar horários
        dias_semana = request.form.getlist('dia_semana[]')
        turnos = request.form.getlist('turno[]')
        horas_inicio = request.form.getlist('hora_inicio[]')
        horas_fim = request.form.getlist('hora_fim[]')
        
        for i in range(len(dias_semana)):
            if dias_semana[i] and turnos[i] and horas_inicio[i] and horas_fim[i]:
                db.execute_query("""
                    INSERT INTO jornada_horarios 
                    (jornada_id, dia_semana, turno, hora_inicio, hora_fim, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """, (jornada_id_final, dias_semana[i], turnos[i], horas_inicio[i], horas_fim[i]))
        
        return redirect(url_for('jornada_trabalho.editar_jornada', id=jornada_id_final))
    
    except Exception as e:
        flash(f'Erro ao salvar jornada: {str(e)}', 'danger')
        return redirect(url_for('jornada_trabalho.nova_jornada'))


@jornada_trabalho_bp.route('/excluir/<int:id>', methods=['POST'])
def excluir_jornada(id):
    """Exclui uma jornada (soft delete)"""
    db = get_db()
    
    try:
        # Verificar se jornada existe
        jornada = db.fetch_one("SELECT * FROM jornadas_trabalho WHERE id = %s", (id,))
        
        if not jornada:
            flash('Jornada não encontrada!', 'danger')
            return redirect(url_for('jornada_trabalho.listar_jornadas'))
        
        # Soft delete
        db.execute_query("""
            UPDATE jornadas_trabalho
            SET ativo = 0, updated_at = NOW()
            WHERE id = %s
        """, (id,))
        
        flash('Jornada excluída com sucesso!', 'success')
    
    except Exception as e:
        flash(f'Erro ao excluir jornada: {str(e)}', 'danger')
    
    return redirect(url_for('jornada_trabalho.listar_jornadas'))


@jornada_trabalho_bp.route('/visualizar/<int:id>')
def visualizar_jornada(id):
    """Visualiza detalhes de uma jornada"""
    db = get_db()
    
    # Buscar jornada
    jornada = db.fetch_one("""
        SELECT jt.*, e.nome_fantasia as empresa_nome
        FROM jornadas_trabalho jt
        LEFT JOIN empresas e ON jt.empresa_id = e.id
        WHERE jt.id = %s
    """, (id,))
    
    if not jornada:
        flash('Jornada não encontrada!', 'danger')
        return redirect(url_for('jornada_trabalho.listar_jornadas'))
    
    # Buscar horários
    horarios = db.fetch_all("""
        SELECT * FROM jornada_horarios
        WHERE jornada_id = %s
        ORDER BY 
            FIELD(dia_semana, 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'),
            turno
    """, (id,))
    
    return render_template('industria/jornada_trabalho_visualizar.html',
                         jornada=jornada,
                         horarios=horarios)
