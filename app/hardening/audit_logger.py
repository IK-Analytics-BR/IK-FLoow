import logging
import json
from datetime import datetime
from flask import request, g
from functools import wraps
import os
import hashlib
import uuid

# Configuração do logger de auditoria
audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO)

# Garantir que o diretório de logs existe
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configurar handler para arquivo de log
audit_file_handler = logging.FileHandler(os.path.join(log_dir, 'audit.log'))
audit_file_handler.setLevel(logging.INFO)

# Configurar formato do log
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
audit_file_handler.setFormatter(formatter)
audit_logger.addHandler(audit_file_handler)

class AuditLogger:
    """Classe para gerenciar logs de auditoria."""
    
    @staticmethod
    def log_event(event_type, user_id, resource_type, resource_id, action, details=None, status="success"):
        """
        Registra um evento de auditoria.
        
        Args:
            event_type (str): Tipo de evento (login, logout, create, update, delete, etc.)
            user_id (int): ID do usuário que realizou a ação
            resource_type (str): Tipo de recurso afetado (user, equipment, maintenance_plan, etc.)
            resource_id (int): ID do recurso afetado
            action (str): Ação realizada
            details (dict, optional): Detalhes adicionais sobre o evento
            status (str, optional): Status do evento (success, failure, etc.)
        """
        # Gerar ID único para o evento
        event_id = str(uuid.uuid4())
        
        # Obter informações do request atual
        ip_address = request.remote_addr if request else "N/A"
        user_agent = request.user_agent.string if request and request.user_agent else "N/A"
        
        # Criar payload do evento
        event = {
            "event_id": event_id,
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "details": details or {},
            "status": status,
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        
        # Calcular hash do evento para garantir integridade
        event_hash = hashlib.sha256(json.dumps(event, sort_keys=True).encode()).hexdigest()
        event["hash"] = event_hash
        
        # Registrar evento no log
        audit_logger.info(json.dumps(event))
        
        return event_id
    
    @staticmethod
    def log_login(user_id, status="success", details=None):
        """Registra um evento de login."""
        return AuditLogger.log_event("authentication", user_id, "user", user_id, "login", details, status)
    
    @staticmethod
    def log_logout(user_id):
        """Registra um evento de logout."""
        return AuditLogger.log_event("authentication", user_id, "user", user_id, "logout")
    
    @staticmethod
    def log_create(user_id, resource_type, resource_id, details=None):
        """Registra um evento de criação de recurso."""
        return AuditLogger.log_event("data_modification", user_id, resource_type, resource_id, "create", details)
    
    @staticmethod
    def log_update(user_id, resource_type, resource_id, details=None):
        """Registra um evento de atualização de recurso."""
        return AuditLogger.log_event("data_modification", user_id, resource_type, resource_id, "update", details)
    
    @staticmethod
    def log_delete(user_id, resource_type, resource_id, details=None):
        """Registra um evento de exclusão de recurso."""
        return AuditLogger.log_event("data_modification", user_id, resource_type, resource_id, "delete", details)
    
    @staticmethod
    def log_view(user_id, resource_type, resource_id):
        """Registra um evento de visualização de recurso."""
        return AuditLogger.log_event("data_access", user_id, resource_type, resource_id, "view")
    
    @staticmethod
    def log_export(user_id, resource_type, resource_id, details=None):
        """Registra um evento de exportação de dados."""
        return AuditLogger.log_event("data_export", user_id, resource_type, resource_id, "export", details)
    
    @staticmethod
    def log_error(user_id, error_type, details=None):
        """Registra um evento de erro."""
        return AuditLogger.log_event("system_error", user_id, "error", 0, error_type, details, "failure")

def audit_trail(event_type, resource_type, action):
    """
    Decorator para adicionar log de auditoria a uma função.
    
    Args:
        event_type (str): Tipo de evento
        resource_type (str): Tipo de recurso
        action (str): Ação realizada
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Obter ID do recurso dos argumentos ou kwargs
            resource_id = kwargs.get('id', 0)
            
            # Obter usuário atual
            user_id = g.user.id if hasattr(g, 'user') and g.user else 0
            
            # Registrar evento antes da execução da função
            try:
                result = f(*args, **kwargs)
                
                # Registrar evento após execução bem-sucedida
                AuditLogger.log_event(event_type, user_id, resource_type, resource_id, action)
                
                return result
            except Exception as e:
                # Registrar erro
                AuditLogger.log_error(user_id, "exception", {"error": str(e)})
                raise
        
        return decorated_function
    
    return decorator
