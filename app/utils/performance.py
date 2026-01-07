"""
Utilitários de desempenho para o sistema.
"""

import time
import functools
import gc
import threading
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='performance.log'
)
logger = logging.getLogger('performance')

# Cache simples para armazenar resultados de funções
_cache = {}
_cache_lock = threading.Lock()

def cache_result(ttl=300):
    """
    Decorator para cache de resultados de funções.
    
    Args:
        ttl (int): Tempo de vida do cache em segundos
        
    Returns:
        function: Função decorada com cache
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Criar uma chave única para os argumentos
            key = str(func.__name__) + str(args) + str(kwargs)
            
            # Verificar se o resultado está no cache e não expirou
            with _cache_lock:
                if key in _cache:
                    result, timestamp = _cache[key]
                    if time.time() - timestamp < ttl:
                        return result
            
            # Executar a função e armazenar o resultado no cache
            result = func(*args, **kwargs)
            with _cache_lock:
                _cache[key] = (result, time.time())
            
            return result
        return wrapper
    return decorator

def clear_cache():
    """Limpa o cache de resultados."""
    with _cache_lock:
        _cache.clear()

def measure_time(func):
    """
    Decorator para medir o tempo de execução de uma função.
    
    Args:
        func (function): Função a ser medida
        
    Returns:
        function: Função decorada com medição de tempo
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        # Registrar o tempo de execução
        execution_time = end_time - start_time
        logger.info(f"Função {func.__name__} executada em {execution_time:.4f} segundos")
        
        return result
    return wrapper

def optimize_memory(func):
    """
    Decorator para otimizar o uso de memória de uma função.
    
    Args:
        func (function): Função a ser otimizada
        
    Returns:
        function: Função decorada com otimização de memória
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Executar coleta de lixo antes da função
        gc.collect()
        
        # Executar a função
        result = func(*args, **kwargs)
        
        # Executar coleta de lixo após a função
        gc.collect()
        
        return result
    return wrapper

def batch_process(batch_size=100):
    """
    Decorator para processar dados em lotes.
    
    Args:
        batch_size (int): Tamanho do lote
        
    Returns:
        function: Função decorada com processamento em lotes
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(items, *args, **kwargs):
            results = []
            
            # Processar os itens em lotes
            for i in range(0, len(items), batch_size):
                batch = items[i:i+batch_size]
                batch_result = func(batch, *args, **kwargs)
                results.extend(batch_result)
            
            return results
        return wrapper
    return decorator

def lazy_load(func):
    """
    Decorator para carregar dados sob demanda.
    
    Args:
        func (function): Função a ser carregada sob demanda
        
    Returns:
        function: Função decorada com carregamento sob demanda
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Verificar se a função já foi executada
        if not hasattr(wrapper, 'result'):
            wrapper.result = func(*args, **kwargs)
        
        return wrapper.result
    
    # Resetar o resultado
    wrapper.reset = lambda: delattr(wrapper, 'result') if hasattr(wrapper, 'result') else None
    
    return wrapper
