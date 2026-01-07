"""
Serviço para integração com sistemas ERP.

Este serviço fornece métodos para integrar o CMMS com sistemas ERP externos,
permitindo a sincronização de dados de equipamentos, estoque, ordens de serviço e custos.
"""

import json
import requests
import logging
from datetime import datetime
from database import get_db
from utils.config_manager import ConfigManager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ERPIntegrationService:
    """Serviço para integração com sistemas ERP."""
    
    def __init__(self):
        """Inicializa o serviço de integração com ERP."""
        self.config = ConfigManager().get_config('erp_integration')
        self.base_url = self.config.get('base_url', '')
        self.api_key = self.config.get('api_key', '')
        self.username = self.config.get('username', '')
        self.password = self.config.get('password', '')
        self.enabled = self.config.get('enabled', False)
        self.sync_interval = self.config.get('sync_interval', 3600)  # Padrão: 1 hora
        self.last_sync = self.config.get('last_sync', None)
        self.erp_type = self.config.get('erp_type', 'generic')
    
    def is_enabled(self):
        """Verifica se a integração está habilitada."""
        return self.enabled and self.base_url and (self.api_key or (self.username and self.password))
    
    def get_auth_header(self):
        """Retorna o cabeçalho de autenticação para requisições à API do ERP."""
        if self.api_key:
            return {'Authorization': f'Bearer {self.api_key}'}
        else:
            # Implementar autenticação básica ou OAuth se necessário
            return {}
    
    def test_connection(self):
        """Testa a conexão com o ERP."""
        if not self.is_enabled():
            return {'success': False, 'message': 'Integração com ERP não está configurada.'}
        
        try:
            headers = self.get_auth_header()
            response = requests.get(f"{self.base_url}/api/test", headers=headers, timeout=10)
            
            if response.status_code == 200:
                return {'success': True, 'message': 'Conexão com ERP estabelecida com sucesso.'}
            else:
                return {
                    'success': False, 
                    'message': f'Erro ao conectar com ERP. Status: {response.status_code}',
                    'details': response.text
                }
        except Exception as e:
            logger.error(f"Erro ao testar conexão com ERP: {str(e)}")
            return {'success': False, 'message': f'Erro ao conectar com ERP: {str(e)}'}
    
    def sync_equipment(self, direction='pull'):
        """
        Sincroniza dados de equipamentos com o ERP.
        
        Args:
            direction (str): Direção da sincronização ('pull' para importar do ERP, 'push' para exportar para o ERP)
        
        Returns:
            dict: Resultado da sincronização
        """
        if not self.is_enabled():
            return {'success': False, 'message': 'Integração com ERP não está configurada.'}
        
        try:
            if direction == 'pull':
                # Importar equipamentos do ERP
                headers = self.get_auth_header()
                response = requests.get(f"{self.base_url}/api/equipment", headers=headers, timeout=30)
                
                if response.status_code != 200:
                    return {
                        'success': False, 
                        'message': f'Erro ao obter equipamentos do ERP. Status: {response.status_code}',
                        'details': response.text
                    }
                
                equipment_data = response.json()
                
                # Processar e inserir/atualizar equipamentos no banco de dados
                db = get_db()
                count_inserted = 0
                count_updated = 0
                
                for item in equipment_data:
                    # Verificar se o equipamento já existe
                    existing = db.fetch_one(
                        "SELECT id FROM equipment WHERE erp_id = %s", 
                        (item.get('id'),)
                    )
                    
                    if existing:
                        # Atualizar equipamento existente
                        db.update("""
                            UPDATE equipment 
                            SET name = %s, model = %s, serial_number = %s, 
                                manufacturer = %s, category = %s, updated_at = NOW()
                            WHERE erp_id = %s
                        """, (
                            item.get('name'), 
                            item.get('model'), 
                            item.get('serial_number'),
                            item.get('manufacturer'),
                            item.get('category'),
                            item.get('id')
                        ))
                        count_updated += 1
                    else:
                        # Inserir novo equipamento
                        db.insert("""
                            INSERT INTO equipment 
                            (name, model, serial_number, manufacturer, category, erp_id, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                        """, (
                            item.get('name'), 
                            item.get('model'), 
                            item.get('serial_number'),
                            item.get('manufacturer'),
                            item.get('category'),
                            item.get('id')
                        ))
                        count_inserted += 1
                
                return {
                    'success': True, 
                    'message': f'Sincronização de equipamentos concluída. {count_inserted} inseridos, {count_updated} atualizados.'
                }
            
            elif direction == 'push':
                # Exportar equipamentos para o ERP
                db = get_db()
                equipment = db.fetch_all("""
                    SELECT id, name, model, serial_number, manufacturer, category, 
                           customer_id, location, status, purchase_date, warranty_end_date,
                           adjusted_life, wear_percentage
                    FROM equipment
                    WHERE active = TRUE
                """)
                
                # Converter para formato compatível com o ERP
                equipment_data = []
                for item in equipment:
                    equipment_data.append({
                        'cmms_id': item['id'],
                        'name': item['name'],
                        'model': item['model'],
                        'serial_number': item['serial_number'],
                        'manufacturer': item['manufacturer'],
                        'category': item['category'],
                        'customer_id': item['customer_id'],
                        'location': item['location'],
                        'status': item['status'],
                        'purchase_date': item['purchase_date'].isoformat() if item['purchase_date'] else None,
                        'warranty_end_date': item['warranty_end_date'].isoformat() if item['warranty_end_date'] else None,
                        'adjusted_life': item['adjusted_life'],
                        'wear_percentage': item['wear_percentage']
                    })
                
                # Enviar para o ERP
                headers = self.get_auth_header()
                headers['Content-Type'] = 'application/json'
                response = requests.post(
                    f"{self.base_url}/api/equipment/batch", 
                    headers=headers,
                    data=json.dumps(equipment_data),
                    timeout=30
                )
                
                if response.status_code not in [200, 201]:
                    return {
                        'success': False, 
                        'message': f'Erro ao enviar equipamentos para o ERP. Status: {response.status_code}',
                        'details': response.text
                    }
                
                return {
                    'success': True, 
                    'message': f'Exportação de {len(equipment_data)} equipamentos para o ERP concluída.'
                }
            
            else:
                return {'success': False, 'message': f'Direção de sincronização inválida: {direction}'}
                
        except Exception as e:
            logger.error(f"Erro na sincronização de equipamentos: {str(e)}")
            return {'success': False, 'message': f'Erro na sincronização de equipamentos: {str(e)}'}
    
    def sync_inventory(self, direction='pull'):
        """
        Sincroniza dados de estoque com o ERP.
        
        Args:
            direction (str): Direção da sincronização ('pull' para importar do ERP, 'push' para exportar para o ERP)
        
        Returns:
            dict: Resultado da sincronização
        """
        if not self.is_enabled():
            return {'success': False, 'message': 'Integração com ERP não está configurada.'}
        
        try:
            if direction == 'pull':
                # Importar estoque do ERP
                headers = self.get_auth_header()
                response = requests.get(f"{self.base_url}/api/inventory", headers=headers, timeout=30)
                
                if response.status_code != 200:
                    return {
                        'success': False, 
                        'message': f'Erro ao obter estoque do ERP. Status: {response.status_code}',
                        'details': response.text
                    }
                
                inventory_data = response.json()
                
                # Processar e inserir/atualizar itens de estoque no banco de dados
                db = get_db()
                count_inserted = 0
                count_updated = 0
                
                for item in inventory_data:
                    # Verificar se o item já existe
                    existing = db.fetch_one(
                        "SELECT id FROM supplies WHERE erp_id = %s", 
                        (item.get('id'),)
                    )
                    
                    if existing:
                        # Atualizar item existente
                        db.update("""
                            UPDATE supplies 
                            SET name = %s, description = %s, category = %s,
                                stock_quantity = %s, min_stock = %s, unit_cost = %s,
                                updated_at = NOW()
                            WHERE erp_id = %s
                        """, (
                            item.get('name'), 
                            item.get('description'), 
                            item.get('category'),
                            item.get('quantity', 0),
                            item.get('min_quantity', 0),
                            item.get('unit_cost', 0),
                            item.get('id')
                        ))
                        count_updated += 1
                    else:
                        # Inserir novo item
                        db.insert("""
                            INSERT INTO supplies 
                            (name, description, category, stock_quantity, min_stock, unit_cost, erp_id, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        """, (
                            item.get('name'), 
                            item.get('description'), 
                            item.get('category'),
                            item.get('quantity', 0),
                            item.get('min_quantity', 0),
                            item.get('unit_cost', 0),
                            item.get('id')
                        ))
                        count_inserted += 1
                
                return {
                    'success': True, 
                    'message': f'Sincronização de estoque concluída. {count_inserted} itens inseridos, {count_updated} atualizados.'
                }
            
            elif direction == 'push':
                # Exportar estoque para o ERP
                db = get_db()
                supplies = db.fetch_all("""
                    SELECT id, name, description, category, stock_quantity, min_stock, unit_cost
                    FROM supplies
                    WHERE active = TRUE
                """)
                
                # Converter para formato compatível com o ERP
                inventory_data = []
                for item in supplies:
                    inventory_data.append({
                        'cmms_id': item['id'],
                        'name': item['name'],
                        'description': item['description'],
                        'category': item['category'],
                        'quantity': item['stock_quantity'],
                        'min_quantity': item['min_stock'],
                        'unit_cost': float(item['unit_cost']) if item['unit_cost'] else 0
                    })
                
                # Enviar para o ERP
                headers = self.get_auth_header()
                headers['Content-Type'] = 'application/json'
                response = requests.post(
                    f"{self.base_url}/api/inventory/batch", 
                    headers=headers,
                    data=json.dumps(inventory_data),
                    timeout=30
                )
                
                if response.status_code not in [200, 201]:
                    return {
                        'success': False, 
                        'message': f'Erro ao enviar estoque para o ERP. Status: {response.status_code}',
                        'details': response.text
                    }
                
                return {
                    'success': True, 
                    'message': f'Exportação de {len(inventory_data)} itens de estoque para o ERP concluída.'
                }
            
            else:
                return {'success': False, 'message': f'Direção de sincronização inválida: {direction}'}
                
        except Exception as e:
            logger.error(f"Erro na sincronização de estoque: {str(e)}")
            return {'success': False, 'message': f'Erro na sincronização de estoque: {str(e)}'}
    
    def sync_service_orders(self, direction='push'):
        """
        Sincroniza ordens de serviço com o ERP.
        
        Args:
            direction (str): Direção da sincronização ('pull' para importar do ERP, 'push' para exportar para o ERP)
        
        Returns:
            dict: Resultado da sincronização
        """
        if not self.is_enabled():
            return {'success': False, 'message': 'Integração com ERP não está configurada.'}
        
        try:
            if direction == 'push':
                # Exportar ordens de serviço para o ERP
                db = get_db()
                
                # Buscar ordens de serviço que foram atualizadas desde a última sincronização
                last_sync = self.last_sync or '1970-01-01'
                orders = db.fetch_all("""
                    SELECT so.*, c.name as customer_name, e.name as equipment_name, 
                           u.name as technician_name
                    FROM service_orders so
                    JOIN customers c ON so.customer_id = c.id
                    JOIN equipment e ON so.equipment_id = e.id
                    LEFT JOIN users u ON so.technician_id = u.id
                    WHERE so.updated_at > %s
                """, (last_sync,))
                
                # Para cada ordem, buscar itens e horas trabalhadas
                orders_data = []
                for order in orders:
                    # Buscar itens da ordem
                    items = db.fetch_all("""
                        SELECT soi.*, s.name as supply_name
                        FROM service_order_items soi
                        JOIN supplies s ON soi.supply_id = s.id
                        WHERE soi.service_order_id = %s
                    """, (order['id'],))
                    
                    # Buscar horas trabalhadas
                    labor = db.fetch_all("""
                        SELECT sol.*, u.name as technician_name
                        FROM service_order_labor sol
                        JOIN users u ON sol.technician_id = u.id
                        WHERE sol.service_order_id = %s
                    """, (order['id'],))
                    
                    # Calcular custos
                    items_cost = sum(item['quantity'] * item['unit_cost'] for item in items)
                    labor_cost = sum(l['hours_worked'] * l['hourly_rate'] for l in labor)
                    total_cost = items_cost + labor_cost
                    
                    # Preparar dados para o ERP
                    order_data = {
                        'cmms_id': order['id'],
                        'order_number': order['order_number'],
                        'customer': {
                            'id': order['customer_id'],
                            'name': order['customer_name']
                        },
                        'equipment': {
                            'id': order['equipment_id'],
                            'name': order['equipment_name']
                        },
                        'technician': {
                            'id': order['technician_id'],
                            'name': order['technician_name']
                        } if order['technician_id'] else None,
                        'type': order['type'],
                        'status': order['status'],
                        'open_date': order['open_date'].isoformat() if order['open_date'] else None,
                        'completion_date': order['completion_date'].isoformat() if order['completion_date'] else None,
                        'observations': order['observations'],
                        'downtime_minutes': order['downtime_minutes'],
                        'items': [
                            {
                                'id': item['id'],
                                'supply_id': item['supply_id'],
                                'supply_name': item['supply_name'],
                                'quantity': item['quantity'],
                                'unit_cost': float(item['unit_cost']) if item['unit_cost'] else 0
                            } for item in items
                        ],
                        'labor': [
                            {
                                'id': l['id'],
                                'technician_id': l['technician_id'],
                                'technician_name': l['technician_name'],
                                'hours_worked': l['hours_worked'],
                                'hourly_rate': float(l['hourly_rate']) if l['hourly_rate'] else 0
                            } for l in labor
                        ],
                        'costs': {
                            'items_cost': float(items_cost),
                            'labor_cost': float(labor_cost),
                            'total_cost': float(total_cost)
                        }
                    }
                    
                    orders_data.append(order_data)
                
                # Enviar para o ERP
                if orders_data:
                    headers = self.get_auth_header()
                    headers['Content-Type'] = 'application/json'
                    response = requests.post(
                        f"{self.base_url}/api/service-orders/batch", 
                        headers=headers,
                        data=json.dumps(orders_data),
                        timeout=30
                    )
                    
                    if response.status_code not in [200, 201]:
                        return {
                            'success': False, 
                            'message': f'Erro ao enviar ordens de serviço para o ERP. Status: {response.status_code}',
                            'details': response.text
                        }
                    
                    # Atualizar timestamp da última sincronização
                    self.last_sync = datetime.now().isoformat()
                    ConfigManager().update_config('erp_integration', {'last_sync': self.last_sync})
                    
                    return {
                        'success': True, 
                        'message': f'Exportação de {len(orders_data)} ordens de serviço para o ERP concluída.'
                    }
                else:
                    return {
                        'success': True, 
                        'message': 'Nenhuma ordem de serviço nova ou atualizada para sincronizar.'
                    }
            
            else:
                return {'success': False, 'message': f'Direção de sincronização inválida ou não suportada: {direction}'}
                
        except Exception as e:
            logger.error(f"Erro na sincronização de ordens de serviço: {str(e)}")
            return {'success': False, 'message': f'Erro na sincronização de ordens de serviço: {str(e)}'}
    
    def sync_all(self):
        """
        Sincroniza todos os dados com o ERP.
        
        Returns:
            dict: Resultado da sincronização
        """
        results = {
            'equipment_pull': self.sync_equipment('pull'),
            'inventory_pull': self.sync_inventory('pull'),
            'service_orders_push': self.sync_service_orders('push')
        }
        
        success = all(result['success'] for result in results.values())
        
        if success:
            # Atualizar timestamp da última sincronização
            self.last_sync = datetime.now().isoformat()
            ConfigManager().update_config('erp_integration', {'last_sync': self.last_sync})
        
        return {
            'success': success,
            'message': 'Sincronização completa com o ERP concluída.' if success else 'Erros na sincronização com o ERP.',
            'details': results
        }
    
    def get_erp_status(self):
        """
        Retorna o status da integração com o ERP.
        
        Returns:
            dict: Status da integração
        """
        return {
            'enabled': self.is_enabled(),
            'erp_type': self.erp_type,
            'base_url': self.base_url,
            'last_sync': self.last_sync,
            'sync_interval': self.sync_interval
        }
    
    def update_config(self, config_data):
        """
        Atualiza a configuração da integração com o ERP.
        
        Args:
            config_data (dict): Novos dados de configuração
            
        Returns:
            dict: Resultado da atualização
        """
        try:
            # Validar URL base
            if 'base_url' in config_data and config_data['base_url']:
                if not config_data['base_url'].startswith(('http://', 'https://')):
                    return {'success': False, 'message': 'URL base deve começar com http:// ou https://'}
            
            # Atualizar configuração
            ConfigManager().update_config('erp_integration', config_data)
            
            # Recarregar configuração
            self.__init__()
            
            return {'success': True, 'message': 'Configuração da integração com ERP atualizada com sucesso.'}
        
        except Exception as e:
            logger.error(f"Erro ao atualizar configuração da integração com ERP: {str(e)}")
            return {'success': False, 'message': f'Erro ao atualizar configuração: {str(e)}'}
