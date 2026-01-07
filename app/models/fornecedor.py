from datetime import datetime
from app import db
from app.models.validators import apply_validators

@apply_validators
class Fornecedor(db.Model):
    """Modelo para fornecedores de insumos."""
    __tablename__ = 'fornecedores'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)  # Nome Fantasia
    razao_social = db.Column(db.String(200))  # Razão Social
    cnpj = db.Column(db.String(18), unique=True, index=True)  # CPF ou CNPJ
    ie = db.Column(db.String(20))  # Inscrição Estadual
    email = db.Column(db.String(120), unique=True)
    telefone = db.Column(db.String(20))
    
    # Campos de endereço
    cep = db.Column(db.String(10))
    endereco = db.Column(db.String(200))  # Logradouro
    numero = db.Column(db.String(10))
    complemento = db.Column(db.String(100))
    neighborhood = db.Column(db.String(100))  # Bairro
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    reference = db.Column(db.String(200))  # Ponto de referência
    
    # Campos de contato
    contato_nome = db.Column(db.String(100))
    contato_cargo = db.Column(db.String(100))
    
    # Campos adicionais
    website = db.Column(db.String(200))
    notes = db.Column(db.Text)
    
    # Campos de controle
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relacionamentos
    insumos_fornecidos = db.relationship('InsumoFornecedor', backref='fornecedor', lazy='dynamic')
    
    def __repr__(self):
        return f'<Fornecedor {self.nome}>'

@apply_validators
class InsumoFornecedor(db.Model):
    """Modelo para relacionamento entre insumos e fornecedores."""
    __tablename__ = 'insumos_fornecedores'
    
    id = db.Column(db.Integer, primary_key=True)
    insumo_id = db.Column(db.Integer, db.ForeignKey('insumos.id'))
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'))
    preco = db.Column(db.Float)
    prazo_entrega = db.Column(db.Integer)  # Prazo em dias
    observacoes = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    insumo = db.relationship('Insumo', backref='fornecedores')
    
    def __repr__(self):
        return f'<InsumoFornecedor {self.id}>'
