# ========================================
# CONFIGURAÇÃO: AMBIENTE PRODUÇÃO (AWS)
# ========================================

DB_CONFIG = {
    'host': 'localhost',
    'user': 'ikflow_user',
    'password': 'IkFl0w@2024!DB',
    'database': 'ikflow',
    'port': 3306,
    'autocommit': True,
    'buffered': True,
    'connection_timeout': 10,
    'ssl_disabled': True  # Desabilita SSL (conexão direta)
}

# Configurações da aplicação
DEBUG = False
FLASK_ENV = 'production'
SECRET_KEY = 'chave_secreta_super_segura_producao_ikflow_2024'
