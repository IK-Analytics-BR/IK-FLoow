"""
Módulo para integrar os modelos SQLAlchemy com as rotas MySQL.
Este módulo fornece funções para converter entre objetos SQLAlchemy e dicionários MySQL.
"""

from app.models.cliente import Cliente
from app.models.produto import Produto
from app.models.insumo import Insumo, TipoDesgaste
from app.models.equipamento import Equipamento, InstalacaoInsumo
from app.models.fornecedor import Fornecedor, InsumoFornecedor
from app.models.user import User
from app import db
from datetime import datetime

def sqlalchemy_to_dict(obj):
    """Converte um objeto SQLAlchemy em um dicionário."""
    result = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        if isinstance(value, datetime):
            value = value.strftime('%Y-%m-%d %H:%M:%S')
        result[column.name] = value
    return result

def dict_to_sqlalchemy(model_class, data):
    """Converte um dicionário em um objeto SQLAlchemy."""
    obj = model_class()
    for key, value in data.items():
        if hasattr(obj, key):
            setattr(obj, key, value)
    return obj

# Funções específicas para cada modelo

def cliente_to_dict(cliente):
    """Converte um objeto Cliente em um dicionário."""
    return {
        'id': cliente.id,
        'name': cliente.nome,
        'cnpj': cliente.cnpj,
        'address': cliente.endereco,
        'city': cliente.cidade,
        'state': cliente.estado,
        'phone': cliente.telefone,
        'email': cliente.email,
        'active': cliente.ativo
    }

def dict_to_cliente(data):
    """Converte um dicionário em um objeto Cliente."""
    cliente = Cliente()
    cliente.nome = data.get('name')
    cliente.cnpj = data.get('cnpj')
    cliente.endereco = data.get('address')
    cliente.cidade = data.get('city')
    cliente.estado = data.get('state')
    cliente.telefone = data.get('phone')
    cliente.email = data.get('email')
    cliente.ativo = data.get('active', True)
    return cliente

def produto_to_dict(produto):
    """Converte um objeto Produto em um dicionário."""
    return {
        'id': produto.id,
        'name': produto.nome,
        'description': produto.descricao,
        'price': produto.preco if hasattr(produto, 'preco') else 0.0,
        'category': produto.categoria,
        'active': produto.ativo
    }

def dict_to_produto(data):
    """Converte um dicionário em um objeto Produto."""
    produto = Produto()
    produto.nome = data.get('name')
    produto.descricao = data.get('description')
    produto.categoria = data.get('category')
    produto.ativo = data.get('active', True)
    return produto

def insumo_to_dict(insumo):
    """Converte um objeto Insumo em um dicionário."""
    return {
        'id': insumo.id,
        'name': insumo.nome,
        'description': insumo.descricao,
        'stock': insumo.estoque_atual,
        'min_stock': insumo.estoque_minimo,
        'price': insumo.preco_unitario,
        'supplier_id': insumo.fornecedor_id if hasattr(insumo, 'fornecedor_id') else None,
        'active': insumo.ativo
    }

def dict_to_insumo(data):
    """Converte um dicionário em um objeto Insumo."""
    insumo = Insumo()
    insumo.nome = data.get('name')
    insumo.descricao = data.get('description')
    insumo.estoque_atual = data.get('stock', 0)
    insumo.estoque_minimo = data.get('min_stock', 0)
    insumo.preco_unitario = data.get('price', 0.0)
    insumo.ativo = data.get('active', True)
    return insumo

def equipamento_to_dict(equipamento):
    """Converte um objeto Equipamento em um dicionário."""
    return {
        'id': equipamento.id,
        'name': equipamento.numero_serie,
        'customer_id': equipamento.cliente_id,
        'installation_date': equipamento.data_instalacao.strftime('%Y-%m-%d') if equipamento.data_instalacao else None,
        'next_maintenance': equipamento.data_ultima_manutencao.strftime('%Y-%m-%d') if equipamento.data_ultima_manutencao else None,
        'notes': equipamento.observacoes,
        'active': equipamento.status == 'Ativo'
    }

def dict_to_equipamento(data):
    """Converte um dicionário em um objeto Equipamento."""
    equipamento = Equipamento()
    equipamento.numero_serie = data.get('name')
    equipamento.cliente_id = data.get('customer_id')
    equipamento.observacoes = data.get('notes')
    equipamento.status = 'Ativo' if data.get('active', True) else 'Inativo'
    
    # Converter datas
    if data.get('installation_date'):
        try:
            equipamento.data_instalacao = datetime.strptime(data.get('installation_date'), '%Y-%m-%d')
        except ValueError:
            pass
    
    if data.get('next_maintenance'):
        try:
            equipamento.data_ultima_manutencao = datetime.strptime(data.get('next_maintenance'), '%Y-%m-%d')
        except ValueError:
            pass
    
    return equipamento

def fornecedor_to_dict(fornecedor):
    """Converte um objeto Fornecedor em um dicionário."""
    return {
        'id': fornecedor.id,
        'name': fornecedor.nome,
        'cnpj': fornecedor.cnpj,
        'address': fornecedor.endereco,
        'city': fornecedor.cidade,
        'state': fornecedor.estado,
        'phone': fornecedor.telefone,
        'email': fornecedor.email,
        'website': fornecedor.website if hasattr(fornecedor, 'website') else '',
        'notes': fornecedor.observacoes if hasattr(fornecedor, 'observacoes') else '',
        'active': fornecedor.ativo
    }

def dict_to_fornecedor(data):
    """Converte um dicionário em um objeto Fornecedor."""
    fornecedor = Fornecedor()
    fornecedor.nome = data.get('name')
    fornecedor.cnpj = data.get('cnpj')
    fornecedor.endereco = data.get('address')
    fornecedor.cidade = data.get('city')
    fornecedor.estado = data.get('state')
    fornecedor.telefone = data.get('phone')
    fornecedor.email = data.get('email')
    fornecedor.ativo = data.get('active', True)
    return fornecedor

def user_to_dict(user):
    """Converte um objeto User em um dicionário."""
    return {
        'id': user.id,
        'name': user.name,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'status': 'active' if user.is_active else 'inactive'
    }

def dict_to_user(data):
    """Converte um dicionário em um objeto User."""
    user = User()
    user.name = data.get('name')
    user.username = data.get('username')
    user.email = data.get('email')
    user.role = data.get('role', 'user')
    user.is_active = data.get('status') == 'active'
    
    # Definir senha se fornecida
    if data.get('password'):
        user.password = data.get('password')
    
    return user

# Funções para salvar objetos no banco de dados

def save_to_db(obj):
    """Salva um objeto no banco de dados."""
    db.session.add(obj)
    db.session.commit()
    return obj

def update_db(obj):
    """Atualiza um objeto no banco de dados."""
    db.session.commit()
    return obj

def delete_from_db(obj):
    """Exclui um objeto do banco de dados."""
    db.session.delete(obj)
    db.session.commit()
    return True
