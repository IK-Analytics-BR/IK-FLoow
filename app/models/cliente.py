from datetime import datetime
from app import db
from app.models.validators import apply_validators

@apply_validators
class Cliente(db.Model):
    """Modelo para clientes do sistema."""
    __tablename__ = 'clientes'
    
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
    
    # Campos de geocodificação
    latitude = db.Column(db.Numeric(10, 8))
    longitude = db.Column(db.Numeric(11, 8))
    
    # Campos adicionais da Receita Federal
    cnpj_basico = db.Column(db.String(8))
    situacao_cadastral = db.Column(db.Integer)  # 1=Ativa, 2=Suspensa, etc
    data_situacao_cadastral = db.Column(db.Date)
    data_inicio_atividade = db.Column(db.Date)
    cnae_fiscal_principal = db.Column(db.String(10))
    cnae_fiscal_secundaria = db.Column(db.Text)
    matriz_filial = db.Column(db.String(1))  # 1=Matriz, 2=Filial
    ddd1 = db.Column(db.String(4))
    telefone2 = db.Column(db.String(15))
    ddd2 = db.Column(db.String(4))
    fax = db.Column(db.String(15))
    ddd_fax = db.Column(db.String(4))
    tipo_logradouro = db.Column(db.String(50))
    origem_cadastro = db.Column(db.String(20), default='manual')  # manual, receita_federal
    
    # Campos de controle
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    equipamentos = db.relationship('Equipamento', backref='cliente', lazy='dynamic')
    
    def __repr__(self):
        return f'<Cliente {self.nome}>'
