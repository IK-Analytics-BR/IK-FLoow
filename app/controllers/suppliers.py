from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.fornecedor import Fornecedor, InsumoFornecedor
from app.models.insumo import Insumo, TipoDesgaste
from app.models.equipamento import Equipamento, InstalacaoInsumo
from app.models.cliente import Cliente
from app.forms.supplier import SupplierForm, SupplySupplierForm

suppliers = Blueprint('suppliers', __name__)

@suppliers.route('/fornecedores')
@login_required
def index():
    """Lista todos os fornecedores."""
    fornecedores = Fornecedor.query.all()
    return render_template('suppliers/index.html', title='Fornecedores', fornecedores=fornecedores)

@suppliers.route('/fornecedores/novo', methods=['GET', 'POST'])
@login_required
def novo():
    """Adiciona um novo fornecedor."""
    form = SupplierForm()
    if form.validate_on_submit():
        fornecedor = Fornecedor(
            nome=form.nome.data,
            cnpj=form.cnpj.data,
            email=form.email.data,
            telefone=form.telefone.data,
            endereco=form.endereco.data,
            cidade=form.cidade.data,
            estado=form.estado.data,
            cep=form.cep.data,
            contato_nome=form.contato_nome.data,
            contato_cargo=form.contato_cargo.data,
            usuario_id=current_user.id if current_user.is_supplier() else None
        )
        db.session.add(fornecedor)
        db.session.commit()
        flash('Fornecedor adicionado com sucesso!', 'success')
        return redirect(url_for('suppliers.index'))
    
    return render_template('suppliers/form.html', title='Novo Fornecedor', form=form)

@suppliers.route('/fornecedores/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Edita um fornecedor existente."""
    fornecedor = Fornecedor.query.get_or_404(id)
    form = SupplierForm(obj=fornecedor)
    
    if form.validate_on_submit():
        form.populate_obj(fornecedor)
        db.session.commit()
        flash('Fornecedor atualizado com sucesso!', 'success')
        return redirect(url_for('suppliers.index'))
    
    return render_template('suppliers/form.html', title='Editar Fornecedor', form=form)

@suppliers.route('/fornecedores/visualizar/<int:id>')
@login_required
def visualizar(id):
    """Visualiza detalhes de um fornecedor."""
    fornecedor = Fornecedor.query.get_or_404(id)
    insumos_fornecidos = InsumoFornecedor.query.filter_by(fornecedor_id=id).all()
    
    return render_template('suppliers/view.html', 
                           title='Detalhes do Fornecedor',
                           fornecedor=fornecedor,
                           insumos_fornecidos=insumos_fornecidos)

@suppliers.route('/fornecedores/excluir/<int:id>')
@login_required
def excluir(id):
    """Exclui um fornecedor (marcando como inativo)."""
    fornecedor = Fornecedor.query.get_or_404(id)
    fornecedor.ativo = False
    db.session.commit()
    flash('Fornecedor excluído com sucesso!', 'success')
    return redirect(url_for('suppliers.index'))

@suppliers.route('/fornecedores/insumos/<int:id>', methods=['GET', 'POST'])
@login_required
def adicionar_insumo(id):
    """Adiciona um insumo ao catálogo do fornecedor."""
    fornecedor = Fornecedor.query.get_or_404(id)
    form = SupplySupplierForm()
    # Carrega as opções para o select de insumos
    form.insumo_id.choices = [(i.id, f"{i.codigo} - {i.nome}") for i in Insumo.query.filter_by(ativo=True).all()]
    
    if form.validate_on_submit():
        # Verifica se o insumo já está cadastrado para este fornecedor
        existente = InsumoFornecedor.query.filter_by(
            fornecedor_id=id,
            insumo_id=form.insumo_id.data
        ).first()
        
        if existente:
            existente.preco = form.preco.data
            existente.prazo_entrega = form.prazo_entrega.data
            existente.observacoes = form.observacoes.data
            existente.ativo = True
            flash('Insumo atualizado no catálogo do fornecedor!', 'success')
        else:
            insumo_fornecedor = InsumoFornecedor(
                fornecedor_id=id,
                insumo_id=form.insumo_id.data,
                preco=form.preco.data,
                prazo_entrega=form.prazo_entrega.data,
                observacoes=form.observacoes.data
            )
            db.session.add(insumo_fornecedor)
            flash('Insumo adicionado ao catálogo do fornecedor!', 'success')
        
        db.session.commit()
        return redirect(url_for('suppliers.visualizar', id=id))
    
    return render_template('suppliers/add_supply.html', 
                           title='Adicionar Insumo ao Catálogo',
                           fornecedor=fornecedor,
                           form=form)

@suppliers.route('/fornecedores/insumos/remover/<int:id>')
@login_required
def remover_insumo(id):
    """Remove um insumo do catálogo do fornecedor."""
    insumo_fornecedor = InsumoFornecedor.query.get_or_404(id)
    fornecedor_id = insumo_fornecedor.fornecedor_id
    
    insumo_fornecedor.ativo = False
    db.session.commit()
    flash('Insumo removido do catálogo do fornecedor!', 'success')
    return redirect(url_for('suppliers.visualizar', id=fornecedor_id))

@suppliers.route('/oportunidades')
@login_required
def oportunidades():
    """Lista oportunidades de negócio para fornecedores."""
    # Se o usuário for um fornecedor, mostra apenas suas oportunidades
    if current_user.is_supplier():
        fornecedor = Fornecedor.query.filter_by(usuario_id=current_user.id).first()
        if not fornecedor:
            flash('Você precisa cadastrar sua empresa como fornecedor primeiro!', 'warning')
            return redirect(url_for('suppliers.novo'))
        
        # Busca os insumos que o fornecedor oferece
        insumos_fornecidos = InsumoFornecedor.query.filter_by(fornecedor_id=fornecedor.id, ativo=True).all()
        insumos_ids = [item.insumo_id for item in insumos_fornecidos]
        
        # Busca os tipos de desgaste dos insumos fornecidos
        insumos = Insumo.query.filter(Insumo.id.in_(insumos_ids)).all()
        tipos_desgaste_ids = [insumo.tipo_desgaste_id for insumo in insumos]
        
        # Busca outros insumos com os mesmos tipos de desgaste
        insumos_relacionados = Insumo.query.filter(
            Insumo.tipo_desgaste_id.in_(tipos_desgaste_ids),
            ~Insumo.id.in_(insumos_ids)
        ).all()
        
        # Busca instalações de insumos que precisam ser substituídos
        instalacoes = InstalacaoInsumo.query.join(Insumo).filter(
            InstalacaoInsumo.status == 'Instalado',
            Insumo.tipo_desgaste_id.in_(tipos_desgaste_ids)
        ).all()
        
        # Filtra as instalações que estão próximas da data de substituição (30 dias ou menos)
        hoje = db.func.current_date()
        oportunidades = []
        for instalacao in instalacoes:
            dias_restantes = instalacao.dias_ate_substituicao()
            if dias_restantes <= 30:
                oportunidades.append({
                    'instalacao': instalacao,
                    'dias_restantes': dias_restantes,
                    'cliente': instalacao.equipamento.cliente,
                    'equipamento': instalacao.equipamento,
                    'insumo': instalacao.insumo
                })
        
        return render_template('suppliers/opportunities.html', 
                               title='Oportunidades de Negócio',
                               oportunidades=oportunidades,
                               insumos_relacionados=insumos_relacionados)
    else:
        # Para administradores, mostra todas as oportunidades
        instalacoes = InstalacaoInsumo.query.filter_by(status='Instalado').all()
        hoje = db.func.current_date()
        oportunidades = []
        for instalacao in instalacoes:
            dias_restantes = instalacao.dias_ate_substituicao()
            if dias_restantes <= 30:
                oportunidades.append({
                    'instalacao': instalacao,
                    'dias_restantes': dias_restantes,
                    'cliente': instalacao.equipamento.cliente,
                    'equipamento': instalacao.equipamento,
                    'insumo': instalacao.insumo
                })
        
        return render_template('suppliers/opportunities.html', 
                               title='Oportunidades de Negócio',
                               oportunidades=oportunidades)
