from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from app.models.equipamento import Equipamento
from datetime import datetime

class EquipmentForm(FlaskForm):
    """Formulário para cadastro e edição de equipamentos."""
    numero_serie = StringField('Número de Série', validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])
    produto_id = SelectField('Produto', coerce=int, validators=[
        DataRequired()
    ])
    cliente_id = SelectField('Cliente', coerce=int, validators=[
        DataRequired()
    ])
    data_instalacao = DateTimeField('Data de Instalação', format='%Y-%m-%d %H:%M', 
                                   default=datetime.utcnow, validators=[DataRequired()])
    data_ultima_manutencao = DateTimeField('Data da Última Manutenção', format='%Y-%m-%d %H:%M', 
                                         default=datetime.utcnow, validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('Ativo', 'Ativo'),
        ('Inativo', 'Inativo'),
        ('Em Manutenção', 'Em Manutenção')
    ], validators=[DataRequired()])
    observacoes = TextAreaField('Observações', validators=[Optional()])
    submit = SubmitField('Salvar')
    
    def __init__(self, obj=None, *args, **kwargs):
        super(EquipmentForm, self).__init__(*args, **kwargs)
        self.original_obj = obj
    
    def validate_numero_serie(self, numero_serie):
        """Valida se o número de série já existe."""
        equipamento = Equipamento.query.filter_by(numero_serie=numero_serie.data).first()
        if equipamento and (not self.original_obj or equipamento.id != self.original_obj.id):
            raise ValidationError('Este número de série já está cadastrado.')

class SupplyInstallationForm(FlaskForm):
    """Formulário para instalação de insumos em equipamentos."""
    insumo_id = SelectField('Insumo', coerce=int, validators=[
        DataRequired()
    ])
    data_instalacao = DateTimeField('Data de Instalação', format='%Y-%m-%d %H:%M', 
                                   default=datetime.utcnow, validators=[DataRequired()])
    observacoes = TextAreaField('Observações', validators=[Optional()])
    submit = SubmitField('Instalar')
