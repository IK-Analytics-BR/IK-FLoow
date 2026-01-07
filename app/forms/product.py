from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from app.models.produto import Produto

class ProductForm(FlaskForm):
    """Formulário para cadastro e edição de produtos."""
    nome = StringField('Nome do Produto', validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])
    codigo = StringField('Código do Produto', validators=[
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
    categoria = SelectField('Categoria', choices=[
        ('Esteira', 'Esteira'),
        ('Motor', 'Motor'),
        ('Bomba', 'Bomba'),
        ('Compressor', 'Compressor'),
        ('Válvula', 'Válvula'),
        ('Sensor', 'Sensor'),
        ('Outro', 'Outro')
    ], validators=[DataRequired()])
    submit = SubmitField('Salvar')
    
    def __init__(self, obj=None, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.original_obj = obj
    
    def validate_codigo(self, codigo):
        """Valida se o código já existe."""
        produto = Produto.query.filter_by(codigo=codigo.data).first()
        if produto and (not self.original_obj or produto.id != self.original_obj.id):
            raise ValidationError('Este código de produto já está cadastrado.')
