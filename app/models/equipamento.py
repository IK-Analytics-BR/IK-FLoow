from datetime import datetime, timedelta
from app import db
from app.models.validators import apply_validators

@apply_validators
class Equipamento(db.Model):
    """Modelo para equipamentos instalados nos clientes."""
    __tablename__ = 'equipamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_serie = db.Column(db.String(100), unique=True, index=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'))
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'))
    data_instalacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_ultima_manutencao = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Ativo')  # Ativo, Inativo, Em Manutenção
    observacoes = db.Column(db.Text)
    
    # Relacionamentos
    insumos_instalados = db.relationship('InstalacaoInsumo', backref='equipamento', lazy='dynamic')
    
    def __repr__(self):
        return f'<Equipamento {self.numero_serie}>'
    
    def insumos_para_substituir(self):
        """Retorna lista de insumos que precisam ser substituídos."""
        hoje = datetime.utcnow()
        return [i for i in self.insumos_instalados if i.data_prevista_substituicao <= hoje]

@apply_validators
class InstalacaoInsumo(db.Model):
    """Modelo para rastreamento de insumos instalados em equipamentos."""
    __tablename__ = 'instalacoes_insumos'
    
    id = db.Column(db.Integer, primary_key=True)
    equipamento_id = db.Column(db.Integer, db.ForeignKey('equipamentos.id'))
    insumo_id = db.Column(db.Integer, db.ForeignKey('insumos.id'))
    data_instalacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_prevista_substituicao = db.Column(db.DateTime)
    data_substituicao = db.Column(db.DateTime)
    status = db.Column(db.String(50), default='Instalado')  # Instalado, Substituído, Defeituoso
    observacoes = db.Column(db.Text)
    
    def __init__(self, **kwargs):
        super(InstalacaoInsumo, self).__init__(**kwargs)
        # Calcula automaticamente a data prevista de substituição com base na vida útil do insumo
        if self.insumo and not self.data_prevista_substituicao:
            self.data_prevista_substituicao = self.data_instalacao + timedelta(days=self.insumo.vida_util)
    
    def __repr__(self):
        return f'<InstalacaoInsumo {self.id}>'
    
    def dias_ate_substituicao(self):
        """Calcula quantos dias faltam para a substituição prevista."""
        if self.data_substituicao:
            return 0
        hoje = datetime.utcnow()
        if self.data_prevista_substituicao <= hoje:
            return 0
        return (self.data_prevista_substituicao - hoje).days
