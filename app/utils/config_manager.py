"""
Gerenciador de configurações para o sistema.

Este módulo fornece uma classe para gerenciar configurações do sistema,
permitindo carregar, salvar e atualizar configurações de diferentes módulos.
"""

import os
import json
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigManager:
    """Gerenciador de configurações do sistema."""
    
    def __init__(self, config_dir=None):
        """
        Inicializa o gerenciador de configurações.
        
        Args:
            config_dir (str, optional): Diretório de configurações. Se não fornecido,
                                       usa o diretório padrão.
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Diretório padrão: app/config
            self.config_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / 'config'
        
        # Criar diretório de configurações se não existir
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True)
            logger.info(f"Diretório de configurações criado: {self.config_dir}")
    
    def get_config_file(self, module_name):
        """
        Retorna o caminho para o arquivo de configuração de um módulo.
        
        Args:
            module_name (str): Nome do módulo.
            
        Returns:
            Path: Caminho para o arquivo de configuração.
        """
        return self.config_dir / f"{module_name}.json"
    
    def get_config(self, module_name):
        """
        Carrega a configuração de um módulo.
        
        Args:
            module_name (str): Nome do módulo.
            
        Returns:
            dict: Configuração do módulo. Retorna um dicionário vazio se o arquivo não existir.
        """
        config_file = self.get_config_file(module_name)
        
        if not config_file.exists():
            logger.info(f"Arquivo de configuração não encontrado para {module_name}. Retornando configuração vazia.")
            return {}
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar configuração de {module_name}: {str(e)}")
            return {}
    
    def save_config(self, module_name, config_data):
        """
        Salva a configuração de um módulo.
        
        Args:
            module_name (str): Nome do módulo.
            config_data (dict): Dados de configuração a serem salvos.
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário.
        """
        config_file = self.get_config_file(module_name)
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Configuração de {module_name} salva com sucesso.")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar configuração de {module_name}: {str(e)}")
            return False
    
    def update_config(self, module_name, update_data):
        """
        Atualiza a configuração de um módulo.
        
        Args:
            module_name (str): Nome do módulo.
            update_data (dict): Dados de configuração a serem atualizados.
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário.
        """
        # Carregar configuração atual
        current_config = self.get_config(module_name)
        
        # Atualizar configuração
        current_config.update(update_data)
        
        # Salvar configuração atualizada
        return self.save_config(module_name, current_config)
    
    def delete_config(self, module_name):
        """
        Exclui a configuração de um módulo.
        
        Args:
            module_name (str): Nome do módulo.
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário.
        """
        config_file = self.get_config_file(module_name)
        
        if not config_file.exists():
            logger.warning(f"Arquivo de configuração não encontrado para {module_name}.")
            return True
        
        try:
            config_file.unlink()
            logger.info(f"Configuração de {module_name} excluída com sucesso.")
            return True
        except Exception as e:
            logger.error(f"Erro ao excluir configuração de {module_name}: {str(e)}")
            return False
    
    def list_configs(self):
        """
        Lista todos os módulos com configurações.
        
        Returns:
            list: Lista de nomes de módulos com configurações.
        """
        try:
            return [f.stem for f in self.config_dir.glob('*.json')]
        except Exception as e:
            logger.error(f"Erro ao listar configurações: {str(e)}")
            return []
    
    def get_all_configs(self):
        """
        Retorna todas as configurações.
        
        Returns:
            dict: Dicionário com todas as configurações, onde as chaves são os nomes dos módulos.
        """
        configs = {}
        
        for module_name in self.list_configs():
            configs[module_name] = self.get_config(module_name)
        
        return configs
