"""
Script para criar um alerta de teste no sistema.

Este script demonstra como criar alertas manualmente usando o NotificationService.
"""

import sys
import os

# Adicionar o diretório pai ao caminho de importação
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from services.notification_service import NotificationService
from database import get_db

def create_test_alert(equipment_id, alert_type='maintenance_due', priority='high', message=None, supply_id=None):
    """
    Cria um alerta de teste no sistema.
    
    Args:
        equipment_id (int): ID do equipamento
        alert_type (str): Tipo de alerta (wear_80, wear_100, stock_low, maintenance_due, os_created, os_assigned, os_completed)
        priority (str): Prioridade do alerta (low, medium, high, critical)
        message (str): Mensagem personalizada (opcional)
        supply_id (int): ID do componente (opcional)
    
    Returns:
        int: ID do alerta criado ou None se falhar
    """
    print(f"Criando alerta de teste para o equipamento {equipment_id}...")
    
    # Verificar se o equipamento existe
    db = get_db()
    equipment = db.fetch_one("SELECT name FROM equipment WHERE id = %s", (equipment_id,))
    
    if not equipment:
        print(f"Erro: Equipamento com ID {equipment_id} não encontrado.")
        return None
    
    print(f"Equipamento encontrado: {equipment['name']}")
    
    # Verificar o componente, se fornecido
    if supply_id:
        supply = db.fetch_one("SELECT name FROM supplies WHERE id = %s", (supply_id,))
        if not supply:
            print(f"Erro: Componente com ID {supply_id} não encontrado.")
            return None
        print(f"Componente encontrado: {supply['name']}")
    
    # Criar o alerta
    alert_id = NotificationService.create_alert(
        equipment_id=equipment_id,
        supply_id=supply_id,
        alert_type=alert_type,
        message=message,
        priority=priority
    )
    
    if alert_id:
        print(f"Alerta criado com sucesso! ID: {alert_id}")
        
        # Buscar detalhes do alerta criado
        alert = db.fetch_one("""
            SELECT a.*, e.name as equipment_name, s.name as supply_name
            FROM alerts a
            JOIN equipment e ON a.equipment_id = e.id
            LEFT JOIN supplies s ON a.supply_id = s.id
            WHERE a.id = %s
        """, (alert_id,))
        
        if alert:
            print("\nDetalhes do alerta:")
            print(f"ID: {alert['id']}")
            print(f"Tipo: {NotificationService.ALERT_TYPES.get(alert['alert_type'], 'Desconhecido')}")
            print(f"Prioridade: {NotificationService.PRIORITY_LEVELS.get(alert['priority'], 'Média')}")
            print(f"Equipamento: {alert['equipment_name']}")
            if alert['supply_name']:
                print(f"Componente: {alert['supply_name']}")
            print(f"Mensagem: {alert['message']}")
            print(f"Data de criação: {alert['created_at']}")
            print(f"Status: {alert['status']}")
    else:
        print("Erro ao criar alerta.")
    
    return alert_id

if __name__ == "__main__":
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("Uso: python create_alert.py <equipment_id> [supply_id] [alert_type] [priority] [message]")
        print("\nTipos de alerta disponíveis:")
        for key, value in NotificationService.ALERT_TYPES.items():
            print(f"  - {key}: {value}")
        print("\nNíveis de prioridade disponíveis:")
        for key, value in NotificationService.PRIORITY_LEVELS.items():
            print(f"  - {key}: {value}")
        
        # Listar equipamentos disponíveis
        db = get_db()
        equipments = db.fetch_all("SELECT id, name FROM equipment WHERE active = TRUE ORDER BY name")
        
        if equipments:
            print("\nEquipamentos disponíveis:")
            for equipment in equipments:
                print(f"  - ID: {equipment['id']}, Nome: {equipment['name']}")
        
        sys.exit(1)
    
    # Obter argumentos
    equipment_id = int(sys.argv[1])
    supply_id = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else None
    alert_type = sys.argv[3] if len(sys.argv) > 3 else 'maintenance_due'
    priority = sys.argv[4] if len(sys.argv) > 4 else 'high'
    message = sys.argv[5] if len(sys.argv) > 5 else None
    
    # Criar o alerta
    create_test_alert(equipment_id, alert_type, priority, message, supply_id)
