from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange

class ScenarioForm(FlaskForm):
    """Form for creating and editing simulation scenarios."""
    name = StringField('Nome do Cenário', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(max=100, message='Nome deve ter no máximo 100 caracteres')
    ])
    
    description = TextAreaField('Descrição', validators=[
        Length(max=500, message='Descrição deve ter no máximo 500 caracteres')
    ])
    
    equipment_id = SelectField('Equipamento', coerce=int, validators=[
        DataRequired(message='Equipamento é obrigatório')
    ])
    
    simulation_period = IntegerField('Período de Simulação (meses)', validators=[
        DataRequired(message='Período de simulação é obrigatório'),
        NumberRange(min=1, max=60, message='Período deve estar entre 1 e 60 meses')
    ])
    
    usage_pattern = SelectField('Padrão de Uso', choices=[
        ('light', 'Leve (4h/dia em média)'),
        ('moderate', 'Moderado (8h/dia em média)'),
        ('heavy', 'Pesado (16h/dia em média)')
    ], validators=[
        DataRequired(message='Padrão de uso é obrigatório')
    ])
    
    maintenance_strategy = SelectField('Estratégia de Manutenção', choices=[
        ('reactive', 'Reativa (apenas quando falhar)'),
        ('preventive', 'Preventiva (baseada em intervalos)'),
        ('predictive', 'Preditiva (baseada em condição)')
    ], validators=[
        DataRequired(message='Estratégia de manutenção é obrigatória')
    ])
    
    submit = SubmitField('Criar Cenário')
    
class CompareForm(FlaskForm):
    """Form for comparing two scenarios."""
    scenario1_id = SelectField('Cenário 1', coerce=int, validators=[
        DataRequired(message='Cenário 1 é obrigatório')
    ])
    
    scenario2_id = SelectField('Cenário 2', coerce=int, validators=[
        DataRequired(message='Cenário 2 é obrigatório')
    ])
    
    submit = SubmitField('Comparar Cenários')
