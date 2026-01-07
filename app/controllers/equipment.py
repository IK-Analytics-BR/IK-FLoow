from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models.equipamento import Equipamento, InstalacaoInsumo
from app.models.cliente import Cliente
from app.models.produto import Produto
from app.models.insumo import Insumo
from app.forms.equipment import EquipmentForm, SupplyInstallationForm

equipment = Blueprint('equipment', __name__)

@equipment.route('/equipamentos')
@login_required
def index():
    """Lista todos os equipamentos."""
    equipamentos = Equipamento.query.all()
    return render_template('equipment/index.html', title='Equipamentos', equipamentos=equipamentos)

@equipment.route('/equipamentos/novo', methods=['GET', 'POST'])
@login_required
def novo():
    """Adiciona um novo equipamento."""
    form = EquipmentForm()
    # Carrega as opções para o select de clientes
    form.cliente_id.choices = [(c.id, c.nome) for c in Cliente.query.filter_by(ativo=True).all()]
    # Carrega as opções para o select de produtos
    form.produto_id.choices = [(p.id, f"{p.codigo} - {p.nome}") for p in Produto.query.filter_by(ativo=True).all()]
    
    if form.validate_on_submit():
        equipamento = Equipamento(
            numero_serie=form.numero_serie.data,
            produto_id=form.produto_id.data,
            cliente_id=form.cliente_id.data,
            data_instalacao=form.data_instalacao.data,
            data_ultima_manutencao=form.data_ultima_manutencao.data,
            status=form.status.data,
            observacoes=form.observacoes.data
        )
        db.session.add(equipamento)
        db.session.commit()
        flash('Equipamento adicionado com sucesso!', 'success')
        return redirect(url_for('equipment.index'))
    
    return render_template('equipment/form.html', title='Novo Equipamento', form=form)

@equipment.route('/equipamentos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Edita um equipamento existente."""
    equipamento = Equipamento.query.get_or_404(id)
    form = EquipmentForm(obj=equipamento)
    # Carrega as opções para o select de clientes
    form.cliente_id.choices = [(c.id, c.nome) for c in Cliente.query.filter_by(ativo=True).all()]
    # Carrega as opções para o select de produtos
    form.produto_id.choices = [(p.id, f"{p.codigo} - {p.nome}") for p in Produto.query.filter_by(ativo=True).all()]
    
    if form.validate_on_submit():
        form.populate_obj(equipamento)
        db.session.commit()
        flash('Equipamento atualizado com sucesso!', 'success')
        return redirect(url_for('equipment.index'))
    
    return render_template('equipment/form.html', title='Editar Equipamento', form=form)

@equipment.route('/equipamentos/visualizar/<int:id>')
@login_required
def visualizar(id):
    """Visualiza detalhes de um equipamento."""
    equipamento = Equipamento.query.get_or_404(id)
    insumos_instalados = InstalacaoInsumo.query.filter_by(equipamento_id=id).all()
    
    # Calcula os dias restantes para cada insumo
    hoje = datetime.utcnow()
    for insumo in insumos_instalados:
        if insumo.data_substituicao:
            insumo.dias_restantes = 0
        elif insumo.data_prevista_substituicao <= hoje:
            insumo.dias_restantes = 0
        else:
            insumo.dias_restantes = (insumo.data_prevista_substituicao - hoje).days
    
    return render_template('equipment/view.html', 
                           title='Detalhes do Equipamento',
                           equipamento=equipamento,
                           insumos_instalados=insumos_instalados)

@equipment.route('/equipamentos/insumos/<int:id>', methods=['GET', 'POST'])
@login_required
def instalar_insumo(id):
    """Instala um novo insumo no equipamento."""
    equipamento = Equipamento.query.get_or_404(id)
    form = SupplyInstallationForm()
    # Carrega as opções para o select de insumos
    form.insumo_id.choices = [(i.id, f"{i.codigo} - {i.nome}") for i in Insumo.query.filter_by(ativo=True).all()]
    
    if form.validate_on_submit():
        # Verifica se há estoque suficiente
        insumo = Insumo.query.get(form.insumo_id.data)
        if insumo.estoque_atual <= 0:
            flash('Não há estoque disponível para este insumo!', 'danger')
            return redirect(url_for('equipment.instalar_insumo', id=id))
        
        # Cria a instalação do insumo
        instalacao = InstalacaoInsumo(
            equipamento_id=id,
            insumo_id=form.insumo_id.data,
            data_instalacao=form.data_instalacao.data,
            observacoes=form.observacoes.data
        )
        
        # Atualiza o estoque
        insumo.estoque_atual -= 1
        
        # Calcula a data prevista de substituição
        instalacao.data_prevista_substituicao = instalacao.data_instalacao + timedelta(days=insumo.vida_util)
        
        db.session.add(instalacao)
        db.session.commit()
        
        flash('Insumo instalado com sucesso!', 'success')
        return redirect(url_for('equipment.visualizar', id=id))
    
    return render_template('equipment/install_supply.html', 
                           title='Instalar Insumo',
                           equipamento=equipamento,
                           form=form)

@equipment.route('/equipamentos/insumos/substituir/<int:id>')
@login_required
def substituir_insumo(id):
    """Marca um insumo como substituído."""
    instalacao = InstalacaoInsumo.query.get_or_404(id)
    instalacao.data_substituicao = datetime.utcnow()
    instalacao.status = 'Substituído'
    
    # Atualiza a data da última manutenção do equipamento
    equipamento = Equipamento.query.get(instalacao.equipamento_id)
    equipamento.data_ultima_manutencao = datetime.utcnow()
    
    db.session.commit()
    flash('Insumo marcado como substituído!', 'success')
    return redirect(url_for('equipment.visualizar', id=instalacao.equipamento_id))

@equipment.route('/manutencoes')
@login_required
def manutencoes():
    """Lista equipamentos que precisam de manutenção."""
    hoje = datetime.utcnow()
    
    # Busca instalações com data prevista de substituição vencida
    instalacoes_vencidas = InstalacaoInsumo.query.filter(
        InstalacaoInsumo.data_prevista_substituicao <= hoje,
        InstalacaoInsumo.data_substituicao == None,
        InstalacaoInsumo.status == 'Instalado'
    ).all()
    
    # Agrupa por equipamento
    equipamentos_manutencao = {}
    for instalacao in instalacoes_vencidas:
        if instalacao.equipamento_id not in equipamentos_manutencao:
            equipamentos_manutencao[instalacao.equipamento_id] = {
                'equipamento': instalacao.equipamento,
                'insumos': []
            }
        equipamentos_manutencao[instalacao.equipamento_id]['insumos'].append(instalacao)
    
    return render_template('equipment/maintenance.html', 
                           title='Manutenções Necessárias',
                           equipamentos_manutencao=equipamentos_manutencao)
