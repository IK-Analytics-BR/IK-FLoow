from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, ValidationError, Optional
from app.models.cliente import Cliente

class CustomerForm(FlaskForm):
    """Formulário para cadastro e edição de clientes."""
    nome = StringField('Nome da Empresa', validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])
    cnpj = StringField('CNPJ', validators=[
        DataRequired(),
        Length(min=14, max=18)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email()
    ])
    telefone = StringField('Telefone', validators=[
        DataRequired(),
        Length(min=10, max=20)
    ])
    endereco = StringField('Endereço', validators=[
        DataRequired(),
        Length(max=200)
    ])
    cidade = StringField('Cidade', validators=[
        DataRequired(),
        Length(max=100)
    ])
    estado = StringField('Estado (UF)', validators=[
        DataRequired(),
        Length(min=2, max=2)
    ])
    cep = StringField('CEP', validators=[
        DataRequired(),
        Length(min=8, max=10)
    ])
    contato_nome = StringField('Nome do Contato', validators=[
        DataRequired(),
        Length(max=100)
    ])
    contato_cargo = StringField('Cargo do Contato', validators=[
        Optional(),
        Length(max=100)
    ])
    submit = SubmitField('Salvar')
    
    def __init__(self, obj=None, *args, **kwargs):
        super(CustomerForm, self).__init__(*args, **kwargs)
        self.original_obj = obj
    
    def validate_cnpj(self, cnpj):
        """Valida se o CNPJ já existe."""
        cliente = Cliente.query.filter_by(cnpj=cnpj.data).first()
        if cliente and (not self.original_obj or cliente.id != self.original_obj.id):
            raise ValidationError('Este CNPJ já está cadastrado.')
    
    def validate_email(self, email):
        """Valida se o email já existe."""
        cliente = Cliente.query.filter_by(email=email.data).first()
        if cliente and (not self.original_obj or cliente.id != self.original_obj.id):
            raise ValidationError('Este email já está cadastrado.')
