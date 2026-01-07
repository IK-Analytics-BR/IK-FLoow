"""
Serviço para gerenciar alertas e notificações do sistema CMMS.

Antes da solicitação: caso já tenha na versão atual, avance para a próxima.
"""

from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json

from database import get_db

class NotificationService:
    """Serviço para gerenciar alertas e notificações."""
    
    # Tipos de alerta
    ALERT_TYPES = {
        'wear_80': 'Desgaste 80%',
        'wear_100': 'Desgaste 100%',
        'stock_low': 'Estoque Baixo',
        'maintenance_due': 'Manutenção Programada',
        'os_created': 'OS Criada',
        'os_assigned': 'OS Atribuída',
        'os_completed': 'OS Concluída'
    }
    
    # Níveis de prioridade
    PRIORITY_LEVELS = {
        'low': 'Baixa',
        'medium': 'Média',
        'high': 'Alta',
        'critical': 'Crítica'
    }
    
    @staticmethod
    def create_alert(equipment_id, supply_id, alert_type, message=None, priority='medium'):
        """
        Cria um alerta no sistema.
        
        Args:
            equipment_id (int): ID do equipamento
            supply_id (int): ID do componente (pode ser None)
            alert_type (str): Tipo de alerta (wear_80, wear_100, stock_low, maintenance_due, os_created, os_assigned, os_completed)
            message (str): Mensagem personalizada (opcional)
            priority (str): Prioridade do alerta (low, medium, high, critical)
            
        Returns:
            int: ID do alerta criado ou None se falhar
        """
        db = get_db()
        
        # Verificar se o tipo de alerta é válido
        if alert_type not in NotificationService.ALERT_TYPES:
            print(f"Tipo de alerta inválido: {alert_type}")
            return None
        
        # Verificar se a prioridade é válida
        if priority not in NotificationService.PRIORITY_LEVELS:
            print(f"Prioridade inválida: {priority}")
            priority = 'medium'  # Valor padrão
        
        # Verificar se já existe um alerta ativo para este equipamento/componente/tipo
        if supply_id is None:
            existing_alert = db.fetch_one("""
                SELECT id FROM alerts
                WHERE equipment_id = %s
                  AND supply_id IS NULL
                  AND alert_type = %s
                  AND status = 'active'
            """, (equipment_id, alert_type))
        else:
            existing_alert = db.fetch_one("""
                SELECT id FROM alerts
                WHERE equipment_id = %s
                  AND supply_id = %s
                  AND alert_type = %s
                  AND status = 'active'
            """, (equipment_id, supply_id, alert_type))
        
        if existing_alert:
            print(f"Já existe um alerta ativo para o equipamento {equipment_id}, componente {supply_id}, tipo {alert_type}.")
            return existing_alert['id']
        
        # Gerar mensagem padrão se não for fornecida
        if not message:
            equipment = db.fetch_one("SELECT name FROM equipment WHERE id = %s", (equipment_id,))
            equipment_name = equipment['name'] if equipment else f"Equipamento #{equipment_id}"
            
            supply_name = None
            if supply_id:
                supply = db.fetch_one("SELECT name FROM supplies WHERE id = %s", (supply_id,))
                supply_name = supply['name'] if supply else f"Componente #{supply_id}"
            
            # Mensagens padrão por tipo de alerta
            if alert_type == 'wear_80':
                message = f"O {'componente ' + supply_name if supply_name else equipment_name} atingiu 80% da vida útil ajustada."
            elif alert_type == 'wear_100':
                message = f"O {'componente ' + supply_name if supply_name else equipment_name} atingiu 100% da vida útil ajustada."
            elif alert_type == 'stock_low':
                message = f"O estoque do componente {supply_name} está abaixo do mínimo."
            elif alert_type == 'maintenance_due':
                message = f"Manutenção programada pendente para {equipment_name}."
            elif alert_type == 'os_created':
                message = f"Nova ordem de serviço criada para {equipment_name}."
            elif alert_type == 'os_assigned':
                message = f"Ordem de serviço atribuída para {equipment_name}."
            elif alert_type == 'os_completed':
                message = f"Ordem de serviço concluída para {equipment_name}."
        
        # Criar o alerta
        alert_id = db.insert("""
            INSERT INTO alerts
            (equipment_id, supply_id, alert_type, status, message, priority)
            VALUES (%s, %s, %s, 'active', %s, %s)
        """, (equipment_id, supply_id, alert_type, message, priority))
        
        if alert_id:
            print(f"Alerta {alert_type} criado com sucesso para o equipamento {equipment_id}, componente {supply_id}.")
            
            # Enviar notificação por e-mail (se configurado)
            NotificationService.send_email_notification(alert_id)
            
            return alert_id
        else:
            print(f"Erro ao criar alerta {alert_type} para o equipamento {equipment_id}, componente {supply_id}.")
            return None
    
    @staticmethod
    def acknowledge_alert(alert_id, user_id):
        """
        Reconhece um alerta.
        
        Args:
            alert_id (int): ID do alerta
            user_id (int): ID do usuário que reconheceu o alerta
            
        Returns:
            bool: True se o alerta foi reconhecido com sucesso, False caso contrário
        """
        db = get_db()
        
        # Verificar se o alerta existe e está ativo
        alert = db.fetch_one("""
            SELECT * FROM alerts
            WHERE id = %s AND status = 'active'
        """, (alert_id,))
        
        if not alert:
            print(f"Alerta {alert_id} não encontrado ou não está ativo.")
            return False
        
        # Atualizar o status do alerta
        affected_rows = db.update("""
            UPDATE alerts
            SET status = 'acknowledged', acknowledged_by = %s, acknowledged_at = NOW()
            WHERE id = %s
        """, (user_id, alert_id))
        
        if affected_rows > 0:
            print(f"Alerta {alert_id} reconhecido com sucesso.")
            return True
        else:
            print(f"Erro ao reconhecer alerta {alert_id}.")
            return False
    
    @staticmethod
    def resolve_alert(alert_id, user_id):
        """
        Resolve um alerta.
        
        Args:
            alert_id (int): ID do alerta
            user_id (int): ID do usuário que resolveu o alerta
            
        Returns:
            bool: True se o alerta foi resolvido com sucesso, False caso contrário
        """
        db = get_db()
        
        # Verificar se o alerta existe e não está resolvido
        alert = db.fetch_one("""
            SELECT * FROM alerts
            WHERE id = %s AND status != 'resolved'
        """, (alert_id,))
        
        if not alert:
            print(f"Alerta {alert_id} não encontrado ou já está resolvido.")
            return False
        
        # Atualizar o status do alerta
        affected_rows = db.update("""
            UPDATE alerts
            SET status = 'resolved', resolved_by = %s, resolved_at = NOW()
            WHERE id = %s
        """, (user_id, alert_id))
        
        if affected_rows > 0:
            print(f"Alerta {alert_id} resolvido com sucesso.")
            return True
        else:
            print(f"Erro ao resolver alerta {alert_id}.")
            return False
    
    @staticmethod
    def get_active_alerts(equipment_id=None, supply_id=None, alert_type=None, limit=50):
        """
        Obtém alertas ativos.
        
        Args:
            equipment_id (int): Filtrar por ID do equipamento (opcional)
            supply_id (int): Filtrar por ID do componente (opcional)
            alert_type (str): Filtrar por tipo de alerta (opcional)
            limit (int): Limite de alertas a retornar
            
        Returns:
            list: Lista de alertas ativos
        """
        db = get_db()
        
        # Construir a consulta SQL
        query = """
            SELECT a.*, e.name as equipment_name, s.name as supply_name,
                   u1.name as acknowledged_by_name, u2.name as resolved_by_name
            FROM alerts a
            JOIN equipment e ON a.equipment_id = e.id
            LEFT JOIN supplies s ON a.supply_id = s.id
            LEFT JOIN users u1 ON a.acknowledged_by = u1.id
            LEFT JOIN users u2 ON a.resolved_by = u2.id
            WHERE a.status != 'resolved'
        """
        
        params = []
        
        if equipment_id:
            query += " AND a.equipment_id = %s"
            params.append(equipment_id)
        
        if supply_id:
            query += " AND a.supply_id = %s"
            params.append(supply_id)
        
        if alert_type:
            query += " AND a.alert_type = %s"
            params.append(alert_type)
        
        query += " ORDER BY a.created_at DESC LIMIT %s"
        params.append(limit)
        
        # Executar a consulta
        alerts = db.fetch_all(query, tuple(params))
        
        return alerts
    
    @staticmethod
    def get_alert_history(equipment_id=None, supply_id=None, alert_type=None, limit=50):
        """
        Obtém histórico de alertas.
        
        Args:
            equipment_id (int): Filtrar por ID do equipamento (opcional)
            supply_id (int): Filtrar por ID do componente (opcional)
            alert_type (str): Filtrar por tipo de alerta (opcional)
            limit (int): Limite de alertas a retornar
            
        Returns:
            list: Lista de alertas
        """
        db = get_db()
        
        # Construir a consulta SQL
        query = """
            SELECT a.*, e.name as equipment_name, s.name as supply_name,
                   u1.name as acknowledged_by_name, u2.name as resolved_by_name
            FROM alerts a
            JOIN equipment e ON a.equipment_id = e.id
            LEFT JOIN supplies s ON a.supply_id = s.id
            LEFT JOIN users u1 ON a.acknowledged_by = u1.id
            LEFT JOIN users u2 ON a.resolved_by = u2.id
            WHERE 1=1
        """
        
        params = []
        
        if equipment_id:
            query += " AND a.equipment_id = %s"
            params.append(equipment_id)
        
        if supply_id:
            query += " AND a.supply_id = %s"
            params.append(supply_id)
        
        if alert_type:
            query += " AND a.alert_type = %s"
            params.append(alert_type)
        
        query += " ORDER BY a.created_at DESC LIMIT %s"
        params.append(limit)
        
        # Executar a consulta
        alerts = db.fetch_all(query, tuple(params))
        
        return alerts
    
    @staticmethod
    def send_email_notification(alert_id):
        """
        Envia uma notificação por e-mail para um alerta.
        
        Args:
            alert_id (int): ID do alerta
            
        Returns:
            bool: True se o e-mail foi enviado com sucesso, False caso contrário
        """
        # Verificar se as configurações de e-mail estão definidas
        config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'email_config.json')
        
        if not os.path.exists(config_file):
            print("Arquivo de configuração de e-mail não encontrado.")
            return False
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"Erro ao ler arquivo de configuração de e-mail: {e}")
            return False
        
        # Verificar se as configurações estão completas
        required_fields = ['smtp_server', 'smtp_port', 'username', 'password', 'from_email', 'to_email']
        for field in required_fields:
            if field not in config:
                print(f"Campo obrigatório ausente na configuração de e-mail: {field}")
                return False
        
        # Obter informações do alerta
        db = get_db()
        alert = db.fetch_one("""
            SELECT a.*, e.name as equipment_name, s.name as supply_name
            FROM alerts a
            JOIN equipment e ON a.equipment_id = e.id
            LEFT JOIN supplies s ON a.supply_id = s.id
            WHERE a.id = %s
        """, (alert_id,))
        
        if not alert:
            print(f"Alerta {alert_id} não encontrado.")
            return False
        
        # Criar o e-mail
        msg = MIMEMultipart()
        msg['From'] = config['from_email']
        msg['To'] = config['to_email']
        msg['Subject'] = f"[CMMS] Alerta: {NotificationService.ALERT_TYPES.get(alert['alert_type'], 'Desconhecido')}"
        
        # Corpo do e-mail
        body = f"""
        <html>
        <body>
            <h2>Alerta do Sistema CMMS</h2>
            <p><strong>Tipo:</strong> {NotificationService.ALERT_TYPES.get(alert['alert_type'], 'Desconhecido')}</p>
            <p><strong>Prioridade:</strong> {NotificationService.PRIORITY_LEVELS.get(alert['priority'], 'Média')}</p>
            <p><strong>Equipamento:</strong> {alert['equipment_name']}</p>
            {'<p><strong>Componente:</strong> ' + alert['supply_name'] + '</p>' if alert['supply_name'] else ''}
            <p><strong>Mensagem:</strong> {alert['message']}</p>
            <p><strong>Data:</strong> {alert['created_at'].strftime('%d/%m/%Y %H:%M:%S')}</p>
            <p>Para mais detalhes, acesse o sistema CMMS.</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Enviar o e-mail
        try:
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
            server.login(config['username'], config['password'])
            server.send_message(msg)
            server.quit()
            print(f"E-mail enviado com sucesso para o alerta {alert_id}.")
            return True
        except Exception as e:
            print(f"Erro ao enviar e-mail para o alerta {alert_id}: {e}")
            return False
    
    @staticmethod
    def create_email_config(smtp_server, smtp_port, username, password, from_email, to_email):
        """
        Cria o arquivo de configuração de e-mail.
        
        Args:
            smtp_server (str): Servidor SMTP
            smtp_port (int): Porta SMTP
            username (str): Nome de usuário
            password (str): Senha
            from_email (str): E-mail de origem
            to_email (str): E-mail de destino
            
        Returns:
            bool: True se o arquivo foi criado com sucesso, False caso contrário
        """
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config')
        
        # Criar o diretório de configuração se não existir
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        config_file = os.path.join(config_dir, 'email_config.json')
        
        # Criar o arquivo de configuração
        config = {
            'smtp_server': smtp_server,
            'smtp_port': smtp_port,
            'username': username,
            'password': password,
            'from_email': from_email,
            'to_email': to_email
        }
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
            print(f"Arquivo de configuração de e-mail criado com sucesso: {config_file}")
            return True
        except Exception as e:
            print(f"Erro ao criar arquivo de configuração de e-mail: {e}")
            return False
