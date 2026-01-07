from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, FloatField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError
from app.models.insumo import Insumo, TipoDesgaste

class SupplyForm(FlaskForm):
    """Formulário para cadastro e edição de insumos."""
    nome = StringField('Nome do Insumo', validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])
    codigo = StringField('Código do Insumo', validators=[
        DataRequired(),
        Length(min=3, max=50)
    ])
    descricao = TextAreaField('Descrição', validators=[
        Optional()
    ])
    fabricante = StringField('Fabricante', validators=[
        DataRequired(),
        Length(max=100)
    ])
    modelo = StringField('Modelo', validators=[
        DataRequired(),
        Length(max=100)
    ])
    vida_util = IntegerField('Vida Útil (dias)', validators=[
        DataRequired(),
        NumberRange(min=1, message='A vida útil deve ser maior que zero')
    ])
    tipo_desgaste_id = SelectField('Tipo de Desgaste', coerce=int, validators=[
        DataRequired()
    ])
    produto_id = SelectField('Produto Relacionado', coerce=int, validators=[
        DataRequired()
    ])
    estoque_atual = IntegerField('Estoque Atual', validators=[
        DataRequired(),
        NumberRange(min=0, message='O estoque não pode ser negativo')
    ])
    estoque_minimo = IntegerField('Estoque Mínimo', validators=[
        DataRequired(),
        NumberRange(min=0, message='O estoque mínimo não pode ser negativo')
    ])
    preco_unitario = FloatField('Preço Unitário (R$)', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='O preço deve ser maior que zero')
    ])
    submit = SubmitField('Salvar')
    
    def __init__(self, obj=None, *args, **kwargs):
        super(SupplyForm, self).__init__(*args, **kwargs)
        self.original_obj = obj
    
    def validate_codigo(self, codigo):
        """Valida se o código já existe."""
        insumo = Insumo.query.filter_by(codigo=codigo.data).first()
        if insumo and (not self.original_obj or insumo.id != self.original_obj.id):
            raise ValidationError('Este código de insumo já está cadastrado.')

class WearTypeForm(FlaskForm):
    """Formulário para cadastro e edição de tipos de desgaste."""
    nome = StringField('Nome do Tipo de Desgaste', validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])
    descricao = TextAreaField('Descrição', validators=[
        Optional()
    ])
    submit = SubmitField('Salvar')
    
    def __init__(self, obj=None, *args, **kwargs):
        super(WearTypeForm, self).__init__(*args, **kwargs)
        self.original_obj = obj
    
    def validate_nome(self, nome):
        """Valida se o nome já existe."""
        tipo = TipoDesgaste.query.filter_by(nome=nome.data).first()
        if tipo and (not self.original_obj or tipo.id != self.original_obj.id):
            raise ValidationError('Este tipo de desgaste já está cadastrado.')
