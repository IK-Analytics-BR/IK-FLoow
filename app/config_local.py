# ========================================
# CONFIGURAÇÃO: AMBIENTE LOCAL
# ========================================

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'aritana',
    'database': 'supply_chain_system',
    'port': 3306,
    'autocommit': True,
    'buffered': True,
    'connection_timeout': 120,  # Aumentado para 120 segundos (2 minutos)
    'ssl_disabled': True,  # Desabilita SSL para conexões localhost
    'pool_name': 'mypool',
    'pool_size': 10,  # Aumentado de 5 para 10
    'pool_reset_session': True,
    'use_pure': True,  # Usar implementação Python pura (mais estável)
    'auth_plugin': 'mysql_native_password',  # Plugin de autenticação
    'charset': 'utf8mb4',  # Charset UTF8
    'collation': 'utf8mb4_unicode_ci',  # Collation UTF8
    'sql_mode': '',  # Remover restrições SQL rígidas
    'raise_on_warnings': False,  # Não parar em warnings
    'get_warnings': False,  # Não buscar warnings
    'consume_results': True  # Consumir todos os resultados
}

# Configurações da aplicação
DEBUG = True
FLASK_ENV = 'development'
SECRET_KEY = 'chave_secreta_do_sistema_local'
