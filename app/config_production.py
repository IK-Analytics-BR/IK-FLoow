# ========================================
# CONFIGURAÇÃO: AMBIENTE PRODUÇÃO (AWS)
# ========================================

DB_CONFIG = {
    'host': '3.19.63.247',
    'user': 'usuario',
    'password': 'Verme958984!',
    'database': 'supply_chain_system',
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
