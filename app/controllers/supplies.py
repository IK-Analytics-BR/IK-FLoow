from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.insumo import Insumo, TipoDesgaste
from app.models.produto import Produto
from app.forms.supply import SupplyForm, WearTypeForm

supplies = Blueprint('supplies', __name__)

@supplies.route('/insumos')
@login_required
def index():
    """Lista todos os insumos."""
    insumos = Insumo.query.all()
    return render_template('supplies/index.html', title='Insumos', insumos=insumos)

@supplies.route('/insumos/novo', methods=['GET', 'POST'])
@login_required
def novo():
    """Adiciona um novo insumo."""
    form = SupplyForm()
    # Carrega as opções para o select de produtos
    form.produto_id.choices = [(p.id, f"{p.codigo} - {p.nome}") for p in Produto.query.filter_by(ativo=True).all()]
    # Carrega as opções para o select de tipos de desgaste
    form.tipo_desgaste_id.choices = [(t.id, t.nome) for t in TipoDesgaste.query.all()]
    
    if form.validate_on_submit():
        insumo = Insumo(
            nome=form.nome.data,
            codigo=form.codigo.data,
            descricao=form.descricao.data,
            fabricante=form.fabricante.data,
            modelo=form.modelo.data,
            vida_util=form.vida_util.data,
            tipo_desgaste_id=form.tipo_desgaste_id.data,
            produto_id=form.produto_id.data,
            estoque_atual=form.estoque_atual.data,
            estoque_minimo=form.estoque_minimo.data,
            preco_unitario=form.preco_unitario.data
        )
        db.session.add(insumo)
        db.session.commit()
        flash('Insumo adicionado com sucesso!', 'success')
        return redirect(url_for('supplies.index'))
    
    return render_template('supplies/form.html', title='Novo Insumo', form=form)

@supplies.route('/insumos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Edita um insumo existente."""
    insumo = Insumo.query.get_or_404(id)
    form = SupplyForm(obj=insumo)
    # Carrega as opções para o select de produtos
    form.produto_id.choices = [(p.id, f"{p.codigo} - {p.nome}") for p in Produto.query.filter_by(ativo=True).all()]
    # Carrega as opções para o select de tipos de desgaste
    form.tipo_desgaste_id.choices = [(t.id, t.nome) for t in TipoDesgaste.query.all()]
    
    if form.validate_on_submit():
        form.populate_obj(insumo)
        db.session.commit()
        flash('Insumo atualizado com sucesso!', 'success')
        return redirect(url_for('supplies.index'))
    
    return render_template('supplies/form.html', title='Editar Insumo', form=form)

@supplies.route('/insumos/visualizar/<int:id>')
@login_required
def visualizar(id):
    """Visualiza detalhes de um insumo."""
    insumo = Insumo.query.get_or_404(id)
    return render_template('supplies/view.html', title='Detalhes do Insumo', insumo=insumo)

@supplies.route('/insumos/excluir/<int:id>')
@login_required
def excluir(id):
    """Exclui um insumo (marcando como inativo)."""
    insumo = Insumo.query.get_or_404(id)
    insumo.ativo = False
    db.session.commit()
    flash('Insumo excluído com sucesso!', 'success')
    return redirect(url_for('supplies.index'))

# Rotas para gerenciamento de tipos de desgaste
@supplies.route('/tipos-desgaste')
@login_required
def tipos_desgaste():
    """Lista todos os tipos de desgaste."""
    tipos = TipoDesgaste.query.all()
    return render_template('supplies/wear_types.html', title='Tipos de Desgaste', tipos=tipos)

@supplies.route('/tipos-desgaste/novo', methods=['GET', 'POST'])
@login_required
def novo_tipo_desgaste():
    """Adiciona um novo tipo de desgaste."""
    form = WearTypeForm()
    if form.validate_on_submit():
        tipo = TipoDesgaste(
            nome=form.nome.data,
            descricao=form.descricao.data
        )
        db.session.add(tipo)
        db.session.commit()
        flash('Tipo de desgaste adicionado com sucesso!', 'success')
        return redirect(url_for('supplies.tipos_desgaste'))
    
    return render_template('supplies/wear_type_form.html', title='Novo Tipo de Desgaste', form=form)

@supplies.route('/tipos-desgaste/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_tipo_desgaste(id):
    """Edita um tipo de desgaste existente."""
    tipo = TipoDesgaste.query.get_or_404(id)
    form = WearTypeForm(obj=tipo)
    
    if form.validate_on_submit():
        form.populate_obj(tipo)
        db.session.commit()
        flash('Tipo de desgaste atualizado com sucesso!', 'success')
        return redirect(url_for('supplies.tipos_desgaste'))
    
    return render_template('supplies/wear_type_form.html', title='Editar Tipo de Desgaste', form=form)
