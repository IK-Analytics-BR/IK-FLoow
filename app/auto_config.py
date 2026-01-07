"""
Módulo de detecção automática de ambiente
Detecta se está rodando em LOCAL ou PRODUÇÃO (AWS)
"""
import socket
import os
import platform

def detect_environment():
    """
    Detecta automaticamente o ambiente de execução
    
    Returns:
        str: 'production' se estiver na AWS, 'local' caso contrário
    """
    
    # Método 1: Verificar hostname
    hostname = socket.gethostname().lower()
    
    # Se hostname contém 'aws', 'ec2', 'ip-' ou 'ubuntu' (comum em AWS)
    if any(keyword in hostname for keyword in ['aws', 'ec2', 'ip-172', 'ip-10']):
        return 'production'
    
    # Método 2: Verificar variável de ambiente
    env = os.getenv('FLASK_ENV', '').lower()
    if env == 'production':
        return 'production'
    
    # Método 3: Verificar se é sistema Linux sem display (servidor)
    if platform.system() == 'Linux':
        # Se não tem DISPLAY, provavelmente é servidor
        if not os.getenv('DISPLAY'):
            return 'production'
    
    # Método 4: Verificar IP local
    try:
        # Pegar IP da máquina
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        # Se começa com 172.x ou 10.x (AWS private IP)
        if local_ip.startswith('172.') or local_ip.startswith('10.'):
            return 'production'
    except:
        pass
    
    # Padrão: ambiente local
    return 'local'

def get_config():
    """
    Retorna a configuração correta baseada no ambiente detectado
    
    Returns:
        module: Módulo de configuração (config_local ou config_production)
    """
    env = detect_environment()
    
    if env == 'production':
        print("[AUTO-CONFIG] Ambiente detectado: PRODUCAO (AWS)")
        from config_production import DB_CONFIG, DEBUG, FLASK_ENV, SECRET_KEY
    else:
        print("[AUTO-CONFIG] Ambiente detectado: LOCAL (Desenvolvimento)")
        from config_local import DB_CONFIG, DEBUG, FLASK_ENV, SECRET_KEY
    
    # Criar objeto de configuração
    class Config:
        pass
    
    config = Config()
    config.DB_CONFIG = DB_CONFIG
    config.DEBUG = DEBUG
    config.FLASK_ENV = FLASK_ENV
    config.SECRET_KEY = SECRET_KEY
    config.ENVIRONMENT = env
    
    return config

# Exportar configuração automaticamente
config = get_config()

# Printar informações
print(f"[AUTO-CONFIG] Banco de dados: {config.DB_CONFIG['host']}")
print(f"[AUTO-CONFIG] Debug: {config.DEBUG}")
print("=" * 60)
