from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.cliente import Cliente
from app.models.equipamento import Equipamento
from app.forms.customer import CustomerForm

customers = Blueprint('customers', __name__)

@customers.route('/clientes')
@login_required
def index():
    """Lista todos os clientes."""
    clientes = Cliente.query.all()
    return render_template('customers/index.html', title='Clientes', clientes=clientes)

@customers.route('/clientes/novo', methods=['GET', 'POST'])
@login_required
def novo():
    """Adiciona um novo cliente."""
    form = CustomerForm()
    if form.validate_on_submit():
        cliente = Cliente(
            nome=form.nome.data,
            cnpj=form.cnpj.data,
            email=form.email.data,
            telefone=form.telefone.data,
            endereco=form.endereco.data,
            cidade=form.cidade.data,
            estado=form.estado.data,
            cep=form.cep.data,
            contato_nome=form.contato_nome.data,
            contato_cargo=form.contato_cargo.data
        )
        db.session.add(cliente)
        db.session.commit()
        flash('Cliente adicionado com sucesso!', 'success')
        return redirect(url_for('customers.index'))
    
    return render_template('customers/form.html', title='Novo Cliente', form=form)

@customers.route('/clientes/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Edita um cliente existente."""
    cliente = Cliente.query.get_or_404(id)
    form = CustomerForm(obj=cliente)
    
    if form.validate_on_submit():
        form.populate_obj(cliente)
        db.session.commit()
        flash('Cliente atualizado com sucesso!', 'success')
        return redirect(url_for('customers.index'))
    
    return render_template('customers/form.html', title='Editar Cliente', form=form)

@customers.route('/clientes/visualizar/<int:id>')
@login_required
def visualizar(id):
    """Visualiza detalhes de um cliente."""
    cliente = Cliente.query.get_or_404(id)
    equipamentos = Equipamento.query.filter_by(cliente_id=id).all()
    
    return render_template('customers/view.html', 
                           title='Detalhes do Cliente',
                           cliente=cliente,
                           equipamentos=equipamentos)

@customers.route('/clientes/excluir/<int:id>')
@login_required
def excluir(id):
    """Exclui um cliente (marcando como inativo)."""
    cliente = Cliente.query.get_or_404(id)
    cliente.ativo = False
    db.session.commit()
    flash('Cliente excluído com sucesso!', 'success')
    return redirect(url_for('customers.index'))
