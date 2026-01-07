from datetime import datetime
from app import db
from app.models.validators import apply_validators

@apply_validators
class Produto(db.Model):
    """Modelo para produtos do sistema."""
    __tablename__ = 'produtos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(50), unique=True, index=True)
    descricao = db.Column(db.Text)
    fabricante = db.Column(db.String(100))
    modelo = db.Column(db.String(100))
    categoria = db.Column(db.String(50))
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    insumos = db.relationship('Insumo', backref='produto', lazy='dynamic')
    equipamentos = db.relationship('Equipamento', backref='tipo_produto', lazy='dynamic')
    
    def __repr__(self):
        return f'<Produto {self.nome}>'
