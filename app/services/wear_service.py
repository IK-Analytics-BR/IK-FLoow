"""
Serviço para gerenciar o cálculo de desgaste e atualização de equipamentos.

Antes da solicitação: caso já tenha na versão atual, avance para a próxima.
"""

from datetime import datetime
from database import get_db
from utils.wear_calculator import WearCalculator
from services.notification_service import NotificationService

class WearService:
    """Serviço para gerenciar o desgaste de equipamentos e componentes."""
    
    @staticmethod
    def update_equipment_wear(equipment_id):
        """
        Atualiza o desgaste de um equipamento com base nos parâmetros de uso.
        
        Args:
            equipment_id (int): ID do equipamento
            
        Returns:
            bool: Se a atualização foi bem-sucedida
        """
        db = get_db()
        
        # Buscar os dados do equipamento
        equipment = db.fetch_one("""
            SELECT * FROM equipment 
            WHERE id = %s AND active = TRUE
        """, (equipment_id,))
        
        if not equipment:
            print(f"Equipamento {equipment_id} não encontrado ou inativo.")
            return False
        
        # Verificar se todos os parâmetros necessários estão presentes
        required_params = ['base_life_hours', 'standard_hours_day', 'real_hours_day', 
                          'k_intensity', 'k_environment', 'accumulated_hours']
        
        for param in required_params:
            if param not in equipment or equipment[param] is None:
                print(f"Parâmetro {param} não encontrado para o equipamento {equipment_id}.")
                return False
        
        # Calcular a vida útil ajustada
        adjusted_life = WearCalculator.calculate_adjusted_life(
            equipment['base_life_hours'],
            equipment['standard_hours_day'],
            equipment['real_hours_day'],
            equipment['k_intensity'],
            equipment['k_environment']
        )
        
        if adjusted_life is None:
            print(f"Não foi possível calcular a vida útil ajustada para o equipamento {equipment_id}.")
            return False
        
        # Calcular o percentual de desgaste
        wear_percentage = WearCalculator.calculate_wear_percentage(
            equipment['accumulated_hours'],
            adjusted_life
        )
        
        if wear_percentage is None:
            print(f"Não foi possível calcular o percentual de desgaste para o equipamento {equipment_id}.")
            return False
        
        # Atualizar o equipamento no banco de dados
        affected_rows = db.update("""
            UPDATE equipment
            SET adjusted_life_hours = %s,
                wear_percentage = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (adjusted_life, wear_percentage, equipment_id))
        
        if affected_rows > 0:
            print(f"Desgaste do equipamento {equipment_id} atualizado com sucesso.")
            
            # Verificar se deve gerar alerta
            should_alert, alert_type = WearCalculator.should_generate_alert(wear_percentage)
            if should_alert:
                NotificationService.create_alert(
                    equipment_id=equipment_id,
                    supply_id=None,
                    alert_type=alert_type,
                    priority='high' if alert_type == 'wear_100' else 'medium'
                )
            
            return True
        else:
            print(f"Erro ao atualizar desgaste do equipamento {equipment_id}.")
            return False
    
    @staticmethod
    def update_supply_wear(installed_supply_id):
        """
        Atualiza o desgaste de um insumo instalado com base nos parâmetros de uso do equipamento.
        
        Args:
            installed_supply_id (int): ID do insumo instalado
            
        Returns:
            bool: Se a atualização foi bem-sucedida
        """
        db = get_db()
        
        # Buscar os dados do insumo instalado
        installed_supply = db.fetch_one("""
            SELECT i.*, e.accumulated_hours, e.real_hours_day, e.standard_hours_day,
                   e.k_intensity, e.k_environment, s.base_life_hours, s.preventive_percentage
            FROM installed_supplies i
            JOIN equipment e ON i.equipment_id = e.id
            JOIN supplies s ON i.supply_id = s.id
            WHERE i.id = %s AND i.active = TRUE
        """, (installed_supply_id,))
        
        if not installed_supply:
            print(f"Insumo instalado {installed_supply_id} não encontrado ou inativo.")
            return False
        
        # Verificar se todos os parâmetros necessários estão presentes
        required_params = ['base_life_hours', 'standard_hours_day', 'real_hours_day', 
                          'k_intensity', 'k_environment', 'accumulated_hours']
        
        for param in required_params:
            if param not in installed_supply or installed_supply[param] is None:
                print(f"Parâmetro {param} não encontrado para o insumo instalado {installed_supply_id}.")
                return False
        
        # Calcular a vida útil ajustada
        adjusted_life = WearCalculator.calculate_adjusted_life(
            installed_supply['base_life_hours'],
            installed_supply['standard_hours_day'],
            installed_supply['real_hours_day'],
            installed_supply['k_intensity'],
            installed_supply['k_environment']
        )
        
        if adjusted_life is None:
            print(f"Não foi possível calcular a vida útil ajustada para o insumo instalado {installed_supply_id}.")
            return False
        
        # Calcular o percentual de desgaste
        wear_percentage = WearCalculator.calculate_wear_percentage(
            installed_supply['accumulated_hours'],
            adjusted_life
        )
        
        if wear_percentage is None:
            print(f"Não foi possível calcular o percentual de desgaste para o insumo instalado {installed_supply_id}.")
            return False
        
        # Atualizar o insumo instalado no banco de dados
        affected_rows = db.update("""
            UPDATE installed_supplies
            SET wear_level = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (wear_percentage, installed_supply_id))
        
        if affected_rows > 0:
            print(f"Desgaste do insumo instalado {installed_supply_id} atualizado com sucesso.")
            
            # Verificar se deve gerar alerta
            should_alert, alert_type = WearCalculator.should_generate_alert(wear_percentage)
            if should_alert:
                NotificationService.create_alert(
                    equipment_id=installed_supply['equipment_id'],
                    supply_id=installed_supply['supply_id'],
                    alert_type=alert_type,
                    priority='high' if alert_type == 'wear_100' else 'medium'
                )
            
            # Verificar se deve gerar manutenção preventiva
            preventive_percentage = installed_supply.get('preventive_percentage', 90)
            if WearCalculator.should_generate_maintenance(wear_percentage, preventive_percentage):
                WearService.create_maintenance_order(
                    installed_supply['equipment_id'],
                    installed_supply['supply_id']
                )
            
            return True
        else:
            print(f"Erro ao atualizar desgaste do insumo instalado {installed_supply_id}.")
            return False
    
    @staticmethod
    def update_hour_meter(equipment_id, hours, reading_date=None, user_id=None, reading_type='manual'):
        """
        Registra uma nova leitura de horímetro e atualiza as horas acumuladas do equipamento.
        
        Args:
            equipment_id (int): ID do equipamento
            hours (int): Leitura do horímetro em horas
            reading_date (str): Data da leitura (formato YYYY-MM-DD)
            user_id (int): ID do usuário que registrou a leitura
            reading_type (str): Tipo de leitura ('manual' ou 'iot')
            
        Returns:
            bool: Se a atualização foi bem-sucedida
        """
        db = get_db()
        
        # Definir a data da leitura
        if reading_date is None:
            reading_date = datetime.now().strftime('%Y-%m-%d')
        
        # Registrar a leitura do horímetro
        reading_id = db.insert("""
            INSERT INTO hour_meter_readings
            (equipment_id, reading_date, hours, reading_type, user_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (equipment_id, reading_date, hours, reading_type, user_id))
        
        if not reading_id:
            print(f"Erro ao registrar leitura do horímetro para o equipamento {equipment_id}.")
            return False
        
        # Atualizar as horas acumuladas do equipamento
        affected_rows = db.update("""
            UPDATE equipment
            SET accumulated_hours = %s,
                last_hour_update = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (hours, reading_date, equipment_id))
        
        if affected_rows > 0:
            print(f"Horímetro do equipamento {equipment_id} atualizado com sucesso.")
            
            # Atualizar o desgaste do equipamento
            WearService.update_equipment_wear(equipment_id)
            
            # Atualizar o desgaste dos insumos instalados
            installed_supplies = db.fetch_all("""
                SELECT id FROM installed_supplies
                WHERE equipment_id = %s AND active = TRUE
            """, (equipment_id,))
            
            for supply in installed_supplies:
                WearService.update_supply_wear(supply['id'])
            
            return True
        else:
            print(f"Erro ao atualizar horímetro do equipamento {equipment_id}.")
            return False
    
    @staticmethod
    def create_alert(equipment_id, supply_id, alert_type):
        """
        Cria um alerta para um equipamento ou insumo.
        Este método está obsoleto. Use NotificationService.create_alert() em vez disso.
        
        Args:
            equipment_id (int): ID do equipamento
            supply_id (int): ID do insumo (pode ser None)
            alert_type (str): Tipo de alerta ('wear_80', 'wear_100', 'stock_low', 'maintenance_due')
            
        Returns:
            int: ID do alerta criado ou None se falhar
        """
        print("DEPRECATED: Use NotificationService.create_alert() em vez deste método.")
        
        # Determinar a prioridade com base no tipo de alerta
        priority = 'high' if alert_type == 'wear_100' else 'medium'
        
        # Usar o novo serviço de notificações
        return NotificationService.create_alert(
            equipment_id=equipment_id,
            supply_id=supply_id,
            alert_type=alert_type,
            priority=priority
        )
    
    @staticmethod
    def create_maintenance_order(equipment_id, supply_id=None):
        """
        Cria uma ordem de serviço de manutenção preventiva.
        Este é um stub que será implementado completamente na etapa de Ordens de Serviço.
        
        Args:
            equipment_id (int): ID do equipamento
            supply_id (int): ID do insumo (pode ser None)
            
        Returns:
            int: ID da ordem de serviço criada ou None se falhar
        """
        # Esta função será implementada completamente na etapa de Ordens de Serviço
        print(f"Ordem de manutenção preventiva seria criada para o equipamento {equipment_id}, insumo {supply_id}.")
        return None
