# -*- coding: utf-8 -*-
"""
Serviço de Envio de Email
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formataddr
import os


# Configurações de email (podem ser sobrescritas por variáveis de ambiente ou config)
EMAIL_CONFIG = {
    'smtp_server': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.environ.get('SMTP_PORT', 587)),
    'smtp_user': os.environ.get('SMTP_USER', ''),
    'smtp_password': os.environ.get('SMTP_PASSWORD', ''),
    'sender_name': os.environ.get('SMTP_SENDER_NAME', 'Sistema'),
    'sender_email': os.environ.get('SMTP_SENDER_EMAIL', ''),
    'use_tls': os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'
}


def carregar_config_email(empresa_id=None):
    """
    Carrega configurações de email do banco de dados
    
    Args:
        empresa_id: ID da empresa (opcional). Se informado, busca config específica da empresa.
    
    Returns:
        dict: Configurações de email
    """
    try:
        from app.database import get_db
        db = get_db()
        
        config = None
        
        # Se informou empresa, buscar config específica
        if empresa_id:
            config = db.fetch_one("""
                SELECT 
                    smtp_server,
                    smtp_port,
                    smtp_ssl,
                    email_usuario AS smtp_user,
                    email_senha AS smtp_password,
                    nome_remetente AS sender_name,
                    email_remetente AS sender_email
                FROM email_config_nfe 
                WHERE empresa_id = %s AND ativo = 1 
                LIMIT 1
            """, [empresa_id])
        
        # Se não encontrou, tentar buscar config padrão (empresa 1)
        if not config:
            config = db.fetch_one("""
                SELECT 
                    smtp_server,
                    smtp_port,
                    smtp_ssl,
                    email_usuario AS smtp_user,
                    email_senha AS smtp_password,
                    nome_remetente AS sender_name,
                    email_remetente AS sender_email
                FROM email_config_nfe 
                WHERE ativo = 1 
                ORDER BY id
                LIMIT 1
            """)
        
        if config:
            return {
                'smtp_server': config.get('smtp_server', EMAIL_CONFIG['smtp_server']),
                'smtp_port': config.get('smtp_port', EMAIL_CONFIG['smtp_port']),
                'smtp_user': config.get('smtp_user', EMAIL_CONFIG['smtp_user']),
                'smtp_password': config.get('smtp_password', EMAIL_CONFIG['smtp_password']),
                'sender_name': config.get('sender_name', EMAIL_CONFIG['sender_name']),
                'sender_email': config.get('sender_email', EMAIL_CONFIG['sender_email']),
                'use_tls': not config.get('smtp_ssl', 0)  # TLS se não for SSL
            }
    except Exception as e:
        print(f"[EMAIL] Erro ao carregar config: {e}")
    
    return EMAIL_CONFIG


def enviar_email_simples(destinatario, assunto, corpo_texto):
    """
    Envia email simples (texto puro)
    
    Args:
        destinatario: email do destinatário
        assunto: assunto do email
        corpo_texto: corpo do email em texto puro
    
    Returns:
        bool: True se enviou com sucesso, False caso contrário
    """
    config = carregar_config_email()
    
    if not config['smtp_user'] or not config['smtp_password']:
        print("[EMAIL] Credenciais SMTP nao configuradas")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = formataddr((config['sender_name'], config['sender_email'] or config['smtp_user']))
        msg['To'] = destinatario
        msg['Subject'] = assunto
        
        msg.attach(MIMEText(corpo_texto, 'plain', 'utf-8'))
        
        # Conectar e enviar
        if config['use_tls']:
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'])
        
        server.login(config['smtp_user'], config['smtp_password'])
        server.sendmail(config['smtp_user'], destinatario, msg.as_string())
        server.quit()
        
        print(f"[EMAIL] Enviado com sucesso para {destinatario}")
        return True
        
    except Exception as e:
        print(f"[EMAIL] Erro ao enviar: {e}")
        return False


def enviar_email_html(destinatario, assunto, corpo_html, corpo_texto=None):
    """
    Envia email com corpo HTML
    
    Args:
        destinatario: email do destinatário
        assunto: assunto do email
        corpo_html: corpo do email em HTML
        corpo_texto: corpo alternativo em texto (opcional)
    
    Returns:
        bool: True se enviou com sucesso
    """
    config = carregar_config_email()
    
    if not config['smtp_user'] or not config['smtp_password']:
        print("[EMAIL] Credenciais SMTP nao configuradas")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr((config['sender_name'], config['sender_email'] or config['smtp_user']))
        msg['To'] = destinatario
        msg['Subject'] = assunto
        
        # Versão texto (fallback)
        if corpo_texto:
            msg.attach(MIMEText(corpo_texto, 'plain', 'utf-8'))
        
        # Versão HTML
        msg.attach(MIMEText(corpo_html, 'html', 'utf-8'))
        
        # Conectar e enviar
        if config['use_tls']:
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'])
        
        server.login(config['smtp_user'], config['smtp_password'])
        server.sendmail(config['smtp_user'], destinatario, msg.as_string())
        server.quit()
        
        print(f"[EMAIL] Enviado com sucesso para {destinatario}")
        return True
        
    except Exception as e:
        print(f"[EMAIL] Erro ao enviar: {e}")
        return False


def enviar_email_com_anexo(destinatario, assunto, corpo_html, anexo, nome_anexo, corpo_texto=None, empresa_id=None):
    """
    Envia email com anexo (PDF, etc)
    
    Args:
        destinatario: email do destinatário
        assunto: assunto do email
        corpo_html: corpo do email em HTML
        anexo: bytes do arquivo anexo
        nome_anexo: nome do arquivo anexo
        corpo_texto: corpo alternativo em texto (opcional)
        empresa_id: ID da empresa para buscar configurações de email (opcional)
    
    Returns:
        bool: True se enviou com sucesso
    """
    config = carregar_config_email(empresa_id)
    
    if not config['smtp_user'] or not config['smtp_password']:
        print("[EMAIL] Credenciais SMTP nao configuradas")
        return False
    
    try:
        msg = MIMEMultipart('mixed')
        msg['From'] = formataddr((config['sender_name'], config['sender_email'] or config['smtp_user']))
        msg['To'] = destinatario
        msg['Subject'] = assunto
        
        # Parte alternativa (texto/html)
        msg_alt = MIMEMultipart('alternative')
        
        if corpo_texto:
            msg_alt.attach(MIMEText(corpo_texto, 'plain', 'utf-8'))
        
        msg_alt.attach(MIMEText(corpo_html, 'html', 'utf-8'))
        msg.attach(msg_alt)
        
        # Anexo
        if anexo:
            attachment = MIMEApplication(anexo, Name=nome_anexo)
            attachment['Content-Disposition'] = f'attachment; filename="{nome_anexo}"'
            msg.attach(attachment)
        
        # Conectar e enviar
        if config['use_tls']:
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'])
        
        server.login(config['smtp_user'], config['smtp_password'])
        server.sendmail(config['smtp_user'], destinatario, msg.as_string())
        server.quit()
        
        print(f"[EMAIL] Enviado com sucesso para {destinatario} (com anexo: {nome_anexo})")
        return True
        
    except Exception as e:
        print(f"[EMAIL] Erro ao enviar: {e}")
        return False


def testar_conexao_smtp():
    """Testa a conexão com o servidor SMTP"""
    config = carregar_config_email()
    
    if not config['smtp_user'] or not config['smtp_password']:
        return False, "Credenciais SMTP nao configuradas"
    
    try:
        if config['use_tls']:
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'])
        
        server.login(config['smtp_user'], config['smtp_password'])
        server.quit()
        
        return True, "Conexao SMTP OK"
        
    except smtplib.SMTPAuthenticationError:
        return False, "Erro de autenticacao. Verifique usuario e senha."
    except smtplib.SMTPConnectError:
        return False, "Erro ao conectar no servidor SMTP."
    except Exception as e:
        return False, f"Erro: {str(e)}"
