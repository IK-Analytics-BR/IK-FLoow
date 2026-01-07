"""
Módulo de validadores para os modelos SQLAlchemy.
"""

import re
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.orm import validates

# Validadores de CNPJ
def is_valid_cnpj(cnpj):
    """Verifica se um CNPJ é válido."""
    # Remover caracteres não numéricos
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    # Verificar se tem 14 dígitos
    if len(cnpj) != 14:
        return False
    
    # Verificar se todos os dígitos são iguais
    if cnpj == cnpj[0] * 14:
        return False
    
    # Calcular primeiro dígito verificador
    soma = 0
    peso = 5
    for i in range(12):
        soma += int(cnpj[i]) * peso
        peso = 9 if peso == 2 else peso - 1
    
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    # Calcular segundo dígito verificador
    soma = 0
    peso = 6
    for i in range(13):
        soma += int(cnpj[i]) * peso
        peso = 9 if peso == 2 else peso - 1
    
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    # Verificar dígitos verificadores
    return int(cnpj[12]) == digito1 and int(cnpj[13]) == digito2

# Validadores de e-mail
def is_valid_email(email):
    """Verifica se um e-mail é válido."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

# Validadores de telefone
def is_valid_phone(phone):
    """Verifica se um telefone é válido."""
    # Remover caracteres não numéricos
    phone = re.sub(r'[^0-9]', '', phone)
    
    # Verificar se tem entre 10 e 11 dígitos (com DDD)
    return 10 <= len(phone) <= 11

# Validadores de CEP
def is_valid_cep(cep):
    """Verifica se um CEP é válido."""
    # Remover caracteres não numéricos
    cep = re.sub(r'[^0-9]', '', cep)
    
    # Verificar se tem 8 dígitos
    return len(cep) == 8

# Validadores de data
def is_valid_date(date_str):
    """Verifica se uma data é válida."""
    try:
        if isinstance(date_str, str):
            datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

# Validadores de preço
def is_valid_price(price):
    """Verifica se um preço é válido."""
    try:
        price = float(price)
        return price >= 0
    except (ValueError, TypeError):
        return False

# Validadores de quantidade
def is_valid_quantity(quantity):
    """Verifica se uma quantidade é válida."""
    try:
        quantity = int(quantity)
        return quantity >= 0
    except (ValueError, TypeError):
        return False

# Função para aplicar validadores a um modelo
def apply_validators(cls):
    """Aplica validadores a um modelo SQLAlchemy."""
    
    # Validador de CNPJ
    if hasattr(cls, 'cnpj'):
        @validates('cnpj')
        def validate_cnpj(self, key, cnpj):
            if cnpj and not is_valid_cnpj(cnpj):
                raise ValueError(f'CNPJ inválido: {cnpj}')
            return cnpj
        
        setattr(cls, 'validate_cnpj', validate_cnpj)
    
    # Validador de e-mail
    if hasattr(cls, 'email'):
        @validates('email')
        def validate_email(self, key, email):
            if email and not is_valid_email(email):
                raise ValueError(f'E-mail inválido: {email}')
            return email
        
        setattr(cls, 'validate_email', validate_email)
    
    # Validador de telefone
    if hasattr(cls, 'telefone'):
        @validates('telefone')
        def validate_phone(self, key, phone):
            if phone and not is_valid_phone(phone):
                raise ValueError(f'Telefone inválido: {phone}')
            return phone
        
        setattr(cls, 'validate_phone', validate_phone)
    
    # Validador de CEP
    if hasattr(cls, 'cep'):
        @validates('cep')
        def validate_cep(self, key, cep):
            if cep and not is_valid_cep(cep):
                raise ValueError(f'CEP inválido: {cep}')
            return cep
        
        setattr(cls, 'validate_cep', validate_cep)
    
    # Validador de preço
    for attr in ['preco', 'preco_unitario', 'price']:
        if hasattr(cls, attr):
            @validates(attr)
            def validate_price(self, key, price):
                if price is not None and not is_valid_price(price):
                    raise ValueError(f'Preço inválido: {price}')
                return price
            
            setattr(cls, f'validate_{attr}', validate_price)
    
    # Validador de quantidade
    for attr in ['estoque_atual', 'estoque_minimo', 'stock', 'min_stock']:
        if hasattr(cls, attr):
            @validates(attr)
            def validate_quantity(self, key, quantity):
                if quantity is not None and not is_valid_quantity(quantity):
                    raise ValueError(f'Quantidade inválida: {quantity}')
                return quantity
            
            setattr(cls, f'validate_{attr}', validate_quantity)
    
    return cls
