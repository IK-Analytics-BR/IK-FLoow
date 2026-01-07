from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.produto import Produto
from app.models.insumo import Insumo
from app.forms.product import ProductForm

products = Blueprint('products', __name__)

@products.route('/produtos')
@login_required
def index():
    """Lista todos os produtos."""
    produtos = Produto.query.all()
    return render_template('products/index.html', title='Produtos', produtos=produtos)

@products.route('/produtos/novo', methods=['GET', 'POST'])
@login_required
def novo():
    """Adiciona um novo produto."""
    form = ProductForm()
    if form.validate_on_submit():
        produto = Produto(
            nome=form.nome.data,
            codigo=form.codigo.data,
            descricao=form.descricao.data,
            fabricante=form.fabricante.data,
            modelo=form.modelo.data,
            categoria=form.categoria.data
        )
        db.session.add(produto)
        db.session.commit()
        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('products.index'))
    
    return render_template('products/form.html', title='Novo Produto', form=form)

@products.route('/produtos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Edita um produto existente."""
    produto = Produto.query.get_or_404(id)
    form = ProductForm(obj=produto)
    
    if form.validate_on_submit():
        form.populate_obj(produto)
        db.session.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('products.index'))
    
    return render_template('products/form.html', title='Editar Produto', form=form)

@products.route('/produtos/visualizar/<int:id>')
@login_required
def visualizar(id):
    """Visualiza detalhes de um produto."""
    produto = Produto.query.get_or_404(id)
    insumos = Insumo.query.filter_by(produto_id=id).all()
    
    return render_template('products/view.html', 
                           title='Detalhes do Produto',
                           produto=produto,
                           insumos=insumos)

@products.route('/produtos/excluir/<int:id>')
@login_required
def excluir(id):
    """Exclui um produto (marcando como inativo)."""
    produto = Produto.query.get_or_404(id)
    produto.ativo = False
    db.session.commit()
    flash('Produto excluído com sucesso!', 'success')
    return redirect(url_for('products.index'))
