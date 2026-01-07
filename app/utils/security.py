"""
Utilitários de segurança para o sistema.
"""

import hashlib
import os
import binascii
import re

def hash_password(password):
    """
    Cria um hash seguro para a senha usando PBKDF2.
    
    Args:
        password (str): A senha em texto plano
        
    Returns:
        str: O hash da senha no formato "algoritmo:iterações:salt:hash"
    """
    # Gerar um salt aleatório
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    
    # Criar o hash da senha usando PBKDF2
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), 
                                salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    
    # Retornar o hash no formato "algoritmo:iterações:salt:hash"
    return (salt + pwdhash).decode('ascii')

def verify_password(stored_password, provided_password):
    """
    Verifica se a senha fornecida corresponde ao hash armazenado.
    
    Args:
        stored_password (str): O hash da senha armazenado
        provided_password (str): A senha fornecida pelo usuário
        
    Returns:
        bool: True se a senha estiver correta, False caso contrário
    """
    # Extrair o salt do hash armazenado
    salt = stored_password[:64]
    
    # Extrair o hash armazenado
    stored_hash = stored_password[64:]
    
    # Calcular o hash da senha fornecida usando o mesmo salt
    pwdhash = hashlib.pbkdf2_hmac('sha512', 
                                provided_password.encode('utf-8'), 
                                salt.encode('ascii'), 
                                100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    
    # Comparar os hashes
    return pwdhash == stored_hash

def validate_password_strength(password):
    """
    Verifica se a senha atende aos requisitos mínimos de segurança.
    
    Args:
        password (str): A senha a ser verificada
        
    Returns:
        tuple: (bool, str) - (True, None) se a senha for válida, (False, mensagem) caso contrário
    """
    if len(password) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres."
    
    if not re.search(r'[A-Z]', password):
        return False, "A senha deve conter pelo menos uma letra maiúscula."
    
    if not re.search(r'[a-z]', password):
        return False, "A senha deve conter pelo menos uma letra minúscula."
    
    if not re.search(r'[0-9]', password):
        return False, "A senha deve conter pelo menos um número."
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "A senha deve conter pelo menos um caractere especial."
    
    return True, None

def sanitize_input(input_string):
    """
    Sanitiza uma string de entrada para prevenir injeção de SQL e XSS.
    
    Args:
        input_string (str): A string a ser sanitizada
        
    Returns:
        str: A string sanitizada
    """
    if input_string is None:
        return None
    
    # Remover caracteres potencialmente perigosos
    sanitized = re.sub(r'[\'";\\]', '', input_string)
    
    # Escapar tags HTML
    sanitized = sanitized.replace('<', '&lt;').replace('>', '&gt;')
    
    return sanitized
