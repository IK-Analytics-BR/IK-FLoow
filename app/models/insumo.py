from datetime import datetime
from app import db
from app.models.validators import apply_validators

@apply_validators
class TipoDesgaste(db.Model):
    """Modelo para tipos de desgaste de insumos."""
    __tablename__ = 'tipos_desgaste'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    
    # Relacionamentos
    insumos = db.relationship('Insumo', backref='tipo_desgaste', lazy='dynamic')
    
    def __repr__(self):
        return f'<TipoDesgaste {self.nome}>'

@apply_validators
class Insumo(db.Model):
    """Modelo para insumos/peças do sistema."""
    __tablename__ = 'insumos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(50), unique=True, index=True)
    descricao = db.Column(db.Text)
    fabricante = db.Column(db.String(100))
    modelo = db.Column(db.String(100))
    vida_util = db.Column(db.Integer)  # Vida útil em dias
    tipo_desgaste_id = db.Column(db.Integer, db.ForeignKey('tipos_desgaste.id'))
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'))
    estoque_atual = db.Column(db.Integer, default=0)
    estoque_minimo = db.Column(db.Integer, default=5)
    preco_unitario = db.Column(db.Float)
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    instalacoes = db.relationship('InstalacaoInsumo', backref='insumo', lazy='dynamic')
    
    def __repr__(self):
        return f'<Insumo {self.nome}>'
        
    def precisa_reposicao(self):
        """Verifica se o insumo precisa de reposição."""
        return self.estoque_atual <= self.estoque_minimo
