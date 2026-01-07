"""
Script de migração para criar as tabelas dos novos módulos:
- Simulador de Cenários
- Hardening & Auditoria
"""

import os
import sys
import logging
from datetime import datetime

# Adicionar o diretório raiz ao path para importar os módulos da aplicação
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import db, create_app
from app.simulator.models import Scenario, SimulationResult

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'migration.log'))
    ]
)
logger = logging.getLogger('migration')

def create_tables():
    """Cria as tabelas dos novos módulos no banco de dados."""
    try:
        # Criar aplicação Flask com configuração de desenvolvimento
        app = create_app('development')
        
        # Criar contexto de aplicação
        with app.app_context():
            # Verificar se as tabelas já existem
            engine = db.engine
            inspector = db.inspect(engine)
            existing_tables = inspector.get_table_names()
            
            # Tabelas a serem criadas
            tables_to_create = []
            
            # Verificar tabela de cenários
            if 'scenarios' not in existing_tables:
                tables_to_create.append('scenarios')
            else:
                logger.info("Tabela 'scenarios' já existe.")
            
            # Verificar tabela de resultados de simulação
            if 'simulation_results' not in existing_tables:
                tables_to_create.append('simulation_results')
            else:
                logger.info("Tabela 'simulation_results' já existe.")
            
            # Criar tabelas que não existem
            if tables_to_create:
                logger.info(f"Criando tabelas: {', '.join(tables_to_create)}")
                
                # Criar tabelas específicas
                if 'scenarios' in tables_to_create or 'simulation_results' in tables_to_create:
                    # Criar tabelas do Simulador de Cenários
                    db.metadata.create_all(
                        engine, 
                        tables=[
                            Scenario.__table__ if 'scenarios' in tables_to_create else None,
                            SimulationResult.__table__ if 'simulation_results' in tables_to_create else None
                        ]
                    )
                    logger.info("Tabelas do Simulador de Cenários criadas com sucesso.")
                
                logger.info("Migração concluída com sucesso.")
            else:
                logger.info("Todas as tabelas já existem. Nenhuma migração necessária.")
    
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {str(e)}")
        raise

if __name__ == '__main__':
    logger.info("Iniciando migração para criar tabelas dos novos módulos...")
    create_tables()
    logger.info("Processo de migração finalizado.")
