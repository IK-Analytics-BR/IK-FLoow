from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.cliente import Cliente
from app.models.produto import Produto
from app.models.insumo import Insumo
from app.models.equipamento import Equipamento, InstalacaoInsumo

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/index')
@login_required
def index():
    """Página inicial do sistema."""
    # Estatísticas para o dashboard
    stats = {
        'clientes': Cliente.query.filter_by(ativo=True).count(),
        'produtos': Produto.query.filter_by(ativo=True).count(),
        'insumos': Insumo.query.filter_by(ativo=True).count(),
        'equipamentos': Equipamento.query.filter_by(status='Ativo').count()
    }
    
    # Insumos com estoque baixo
    insumos_baixo_estoque = Insumo.query.filter(
        Insumo.estoque_atual <= Insumo.estoque_minimo,
        Insumo.ativo == True
    ).limit(5).all()
    
    # Equipamentos que precisam de manutenção
    equipamentos_manutencao = []
    equipamentos = Equipamento.query.filter_by(status='Ativo').all()
    for equip in equipamentos:
        if equip.insumos_para_substituir():
            equipamentos_manutencao.append(equip)
            if len(equipamentos_manutencao) >= 5:
                break
    
    return render_template('index.html', 
                           title='Dashboard',
                           stats=stats,
                           insumos_baixo_estoque=insumos_baixo_estoque,
                           equipamentos_manutencao=equipamentos_manutencao)

@main.route('/perfil')
@login_required
def perfil():
    """Página de perfil do usuário."""
    return render_template('perfil.html', title='Meu Perfil')
