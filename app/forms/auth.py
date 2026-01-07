from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models.user import User

class LoginForm(FlaskForm):
    """Formulário para login de usuários."""
    username = StringField('Nome de Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')

class RegistrationForm(FlaskForm):
    """Formulário para registro de novos usuários."""
    username = StringField('Nome de Usuário', validators=[
        DataRequired(),
        Length(min=3, max=64)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email()
    ])
    name = StringField('Nome Completo', validators=[
        DataRequired(),
        Length(min=3, max=64)
    ])
    password = PasswordField('Senha', validators=[
        DataRequired(),
        Length(min=8, message='A senha deve ter pelo menos 8 caracteres')
    ])
    password2 = PasswordField('Confirmar Senha', validators=[
        DataRequired(),
        EqualTo('password', message='As senhas devem ser iguais')
    ])
    submit = SubmitField('Registrar')
    
    def validate_username(self, username):
        """Valida se o nome de usuário já existe."""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Este nome de usuário já está em uso. Por favor, escolha outro.')
    
    def validate_email(self, email):
        """Valida se o email já existe."""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Este email já está registrado. Por favor, use outro email.')

class ChangePasswordForm(FlaskForm):
    """Formulário para alteração de senha."""
    old_password = PasswordField('Senha Atual', validators=[DataRequired()])
    new_password = PasswordField('Nova Senha', validators=[
        DataRequired(),
        Length(min=8, message='A senha deve ter pelo menos 8 caracteres')
    ])
    new_password2 = PasswordField('Confirmar Nova Senha', validators=[
        DataRequired(),
        EqualTo('new_password', message='As senhas devem ser iguais')
    ])
    submit = SubmitField('Alterar Senha')
