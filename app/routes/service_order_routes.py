"""
Rotas para gerenciamento de ordens de serviço.

Antes da solicitação: caso já tenha na versão atual, avance para a próxima.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from datetime import datetime

from database import get_db
from services.notification_service import NotificationService

# Criar o blueprint
service_order_bp = Blueprint('service_order', __name__)

# Decorador para verificar se o usuário está logado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Por favor, faça login para acessar esta página.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@service_order_bp.route('/service_orders')
@login_required
def service_order_list():
    """Lista todas as ordens de serviço."""
    db = get_db()
    
    # Buscar as ordens de serviço
    orders = db.fetch_all("""
        SELECT so.*, c.name as customer_name, e.name as equipment_name, 
               s.name as supply_name, t.name as technician_name
        FROM service_orders so
        JOIN customers c ON so.customer_id = c.id
        JOIN equipment e ON so.equipment_id = e.id
        LEFT JOIN supplies s ON so.supply_id = s.id
        LEFT JOIN technicians t ON so.technician_id = t.id
        WHERE so.active = TRUE
        ORDER BY so.open_date DESC
    """)
    
    return render_template(
        'service_order_list.html',
        orders=orders,
        active_page='service_orders'
    )

@service_order_bp.route('/service_orders/add', methods=['GET', 'POST'])
@login_required
def service_order_add():
    """Adiciona uma nova ordem de serviço."""
    print("\n[DEBUG] Iniciando service_order_add")
    db = get_db()
    print("[DEBUG] Conexão com o banco de dados estabelecida")
    
    if request.method == 'POST':
        # Obter dados do formulário
        customer_id = request.form.get('customer_id')
        equipment_id = request.form.get('equipment_id')
        supply_id = request.form.get('supply_id') or None
        maintenance_plan_id = request.form.get('maintenance_plan_id') or None
        order_type = request.form.get('type')
        technician_id = request.form.get('technician_id') or None
        observations = request.form.get('observations')
        
        # Validar dados
        if not customer_id or not equipment_id or not order_type:
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            return redirect(url_for('service_order.service_order_add'))
        
        # Gerar número da OS (formato: OS-YYYYMMDD-XXX)
        today = datetime.now().strftime('%Y%m%d')
        last_order = db.fetch_one("""
            SELECT order_number FROM service_orders
            WHERE order_number LIKE %s
            ORDER BY id DESC LIMIT 1
        """, (f'OS-{today}-%',))
        
        if last_order:
            last_number = int(last_order['order_number'].split('-')[-1])
            order_number = f'OS-{today}-{last_number + 1:03d}'
        else:
            order_number = f'OS-{today}-001'
        
        # Inserir ordem de serviço no banco de dados
        query = """
            INSERT INTO service_orders (
                order_number, customer_id, equipment_id, supply_id, 
                maintenance_plan_id, type, technician_id, observations
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            order_number, customer_id, equipment_id, supply_id,
            maintenance_plan_id, order_type, technician_id, observations
        )
        
        order_id = db.insert(query, params)
        
        if order_id:
            flash(f'Ordem de serviço {order_number} cadastrada com sucesso!', 'success')
            
            # Criar alerta para a nova OS
            NotificationService.create_alert(
                equipment_id=equipment_id,
                supply_id=supply_id,
                alert_type='os_created',
                message=f'Nova ordem de serviço {order_number} criada para o equipamento.',
                priority='medium'
            )
            
            return redirect(url_for('service_order.service_order_view', order_id=order_id))
        else:
            flash('Erro ao cadastrar ordem de serviço.', 'danger')
    
    # Buscar clientes, equipamentos, insumos, planos de manutenção e técnicos para o formulário
    print("[DEBUG] Buscando clientes...")
    customers = db.fetch_all("""
        SELECT id, name FROM customers
        WHERE active = TRUE
        ORDER BY name
    """)
    print(f"[DEBUG] Clientes encontrados: {len(customers)}")
    for customer in customers:
        print(f"[DEBUG] Cliente: {customer['id']} - {customer['name']}")
        
    # Solução alternativa: se não houver clientes, criar alguns para teste
    if not customers:
        print("[DEBUG] Nenhum cliente encontrado. Criando clientes para teste...")
        # Inserir clientes de teste
        db.insert("""
            INSERT INTO customers (name, cnpj, contact_name, phone, email, address, city, state, zip_code, notes, active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, ('Cliente Teste 1', '12.345.678/0001-90', 'Contato Teste 1', '(11) 1234-5678', 'cliente1@teste.com', 'Rua Teste 1', 'São Paulo', 'SP', '01234-567', 'Cliente de teste 1', True))
        
        db.insert("""
            INSERT INTO customers (name, cnpj, contact_name, phone, email, address, city, state, zip_code, notes, active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, ('Cliente Teste 2', '98.765.432/0001-10', 'Contato Teste 2', '(11) 8765-4321', 'cliente2@teste.com', 'Rua Teste 2', 'São Paulo', 'SP', '01234-567', 'Cliente de teste 2', True))
        
        # Buscar os clientes novamente
        customers = db.fetch_all("""
            SELECT id, name FROM customers
            WHERE active = TRUE
            ORDER BY name
        """)
        print(f"[DEBUG] Clientes criados: {len(customers)}")
        for customer in customers:
            print(f"[DEBUG] Cliente: {customer['id']} - {customer['name']}")
            
    # Verificar se há equipamentos associados aos clientes
    equipments_count = db.fetch_one("""
        SELECT COUNT(*) as count FROM equipment
        WHERE active = TRUE
    """)
    
    if equipments_count and equipments_count['count'] == 0 and customers:
        print("[DEBUG] Nenhum equipamento encontrado. Criando equipamentos para teste...")
        # Criar equipamentos de teste para os clientes
        for customer in customers:
            db.insert("""
                INSERT INTO equipment (name, model, serial_number, customer_id, location, status, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (f'Equipamento Teste - {customer["name"]}', 'Modelo Teste', f'SN-{customer["id"]}-001', customer['id'], 'Local Teste', 'active', True))
        
        print("[DEBUG] Equipamentos criados com sucesso!")
    
    
    equipments = db.fetch_all("""
        SELECT id, name, customer_id FROM equipment
        WHERE active = TRUE
        ORDER BY name
    """)
    
    supplies = db.fetch_all("""
        SELECT id, name FROM supplies
        WHERE active = TRUE
        ORDER BY name
    """)
    
    maintenance_plans = db.fetch_all("""
        SELECT id, task, customer_id, equipment_id FROM maintenance_plans
        WHERE active = TRUE
        ORDER BY id DESC
    """)
    
    technicians = db.fetch_all("""
        SELECT id, name, specialty FROM technicians
        WHERE active = TRUE AND status = 'active'
        ORDER BY name
    """)
    
    print("[DEBUG] Renderizando template service_order_form.html")
    print(f"[DEBUG] Dados passados para o template:")
    print(f"[DEBUG] - customers: {len(customers)} itens")
    print(f"[DEBUG] - equipments: {len(equipments)} itens")
    print(f"[DEBUG] - supplies: {len(supplies)} itens")
    print(f"[DEBUG] - maintenance_plans: {len(maintenance_plans)} itens")
    print(f"[DEBUG] - technicians: {len(technicians)} itens")
    
    return render_template(
        'service_order_form.html',
        customers=customers,
        equipments=equipments,
        supplies=supplies,
        maintenance_plans=maintenance_plans,
        technicians=technicians,
        order=None,
        active_page='service_orders'
    )

@service_order_bp.route('/service_orders/edit/<int:order_id>', methods=['GET', 'POST'])
@login_required
def service_order_edit(order_id):
    """Edita uma ordem de serviço existente."""
    db = get_db()
    
    # Buscar a ordem de serviço
    order = db.fetch_one("""
        SELECT * FROM service_orders
        WHERE id = %s
    """, (order_id,))
    
    if not order:
        flash('Ordem de serviço não encontrada.', 'danger')
        return redirect(url_for('service_order.service_order_list'))
    
    # Verificar se a ordem de serviço pode ser editada
    if order['status'] == 'completed' or order['status'] == 'canceled':
        flash('Não é possível editar uma ordem de serviço concluída ou cancelada.', 'danger')
        return redirect(url_for('service_order.service_order_view', order_id=order_id))
    
    if request.method == 'POST':
        # Obter dados do formulário
        technician_id = request.form.get('technician_id') or None
        status = request.form.get('status')
        observations = request.form.get('observations')
        downtime_minutes = request.form.get('downtime_minutes') or 0
        
        # Validar dados
        if not status:
            flash('Por favor, selecione um status para a ordem de serviço.', 'danger')
            return redirect(url_for('service_order.service_order_edit', order_id=order_id))
        
        try:
            downtime_minutes = int(downtime_minutes)
            if downtime_minutes < 0:
                raise ValueError("Tempo de parada deve ser positivo")
        except ValueError:
            flash('O tempo de parada deve ser um número inteiro positivo.', 'danger')
            return redirect(url_for('service_order.service_order_edit', order_id=order_id))
        
        # Verificar se a ordem está sendo concluída
        completion_date = None
        if status == 'completed' and order['status'] != 'completed':
            completion_date = datetime.now()
            
        # Verificar se um técnico está sendo atribuído
        is_technician_assigned = False
        if technician_id and not order['technician_id']:
            is_technician_assigned = True
        
        # Atualizar ordem de serviço no banco de dados
        query = """
            UPDATE service_orders
            SET technician_id = %s, status = %s, observations = %s,
                downtime_minutes = %s, completion_date = %s
            WHERE id = %s
        """
        params = (
            technician_id, status, observations,
            downtime_minutes, completion_date, order_id
        )
        
        affected_rows = db.update(query, params)
        
        if affected_rows > 0:
            flash('Ordem de serviço atualizada com sucesso!', 'success')
            
            # Criar alerta se a OS foi concluída
            if status == 'completed' and order['status'] != 'completed':
                NotificationService.create_alert(
                    equipment_id=order['equipment_id'],
                    supply_id=order['supply_id'],
                    alert_type='os_completed',
                    message=f'Ordem de serviço {order["order_number"]} concluída.',
                    priority='medium'
                )
            
            # Criar alerta se um técnico foi atribuído
            if is_technician_assigned:
                # Buscar o nome do técnico
                technician = db.fetch_one("SELECT name FROM technicians WHERE id = %s", (technician_id,))
                technician_name = technician['name'] if technician else 'Desconhecido'
                
                NotificationService.create_alert(
                    equipment_id=order['equipment_id'],
                    supply_id=order['supply_id'],
                    alert_type='os_assigned',
                    message=f'Técnico {technician_name} atribuído à ordem de serviço {order["order_number"]}.',
                    priority='medium'
                )
            
            return redirect(url_for('service_order.service_order_view', order_id=order_id))
        else:
            flash('Erro ao atualizar ordem de serviço.', 'danger')
    
    # Buscar técnicos para o formulário
    technicians = db.fetch_all("""
        SELECT id, name, specialty FROM technicians
        WHERE active = TRUE AND status = 'active'
        ORDER BY name
    """)
    
    return render_template(
        'service_order_edit.html',
        order=order,
        technicians=technicians,
        active_page='service_orders'
    )

@service_order_bp.route('/service_orders/view/<int:order_id>')
@login_required
def service_order_view(order_id):
    """Visualiza uma ordem de serviço."""
    db = get_db()
    
    # Buscar a ordem de serviço
    order = db.fetch_one("""
        SELECT so.*, c.name as customer_name, e.name as equipment_name, 
               s.name as supply_name, t.name as technician_name,
               mp.task as maintenance_plan_task
        FROM service_orders so
        JOIN customers c ON so.customer_id = c.id
        JOIN equipment e ON so.equipment_id = e.id
        LEFT JOIN supplies s ON so.supply_id = s.id
        LEFT JOIN technicians t ON so.technician_id = t.id
        LEFT JOIN maintenance_plans mp ON so.maintenance_plan_id = mp.id
        WHERE so.id = %s
    """, (order_id,))
    
    if not order:
        flash('Ordem de serviço não encontrada.', 'danger')
        return redirect(url_for('service_order.service_order_list'))
    
    # Buscar itens da ordem de serviço
    items = db.fetch_all("""
        SELECT i.*, s.name as supply_name
        FROM service_order_items i
        JOIN supplies s ON i.supply_id = s.id
        WHERE i.service_order_id = %s
    """, (order_id,))
    
    # Buscar horas trabalhadas
    labor = db.fetch_all("""
        SELECT l.*, t.name as technician_name
        FROM service_order_labor l
        JOIN technicians t ON l.technician_id = t.id
        WHERE l.service_order_id = %s
    """, (order_id,))
    
    # Calcular totais
    total_items = sum(item['quantity'] * item['unit_cost'] for item in items)
    total_labor = sum(l['hours_worked'] * l['hourly_rate'] for l in labor)
    total_cost = total_items + total_labor
    
    return render_template(
        'service_order_view.html',
        order=order,
        items=items,
        labor=labor,
        total_items=total_items,
        total_labor=total_labor,
        total_cost=total_cost,
        active_page='service_orders'
    )

@service_order_bp.route('/service_orders/add_item/<int:order_id>', methods=['POST'])
@login_required
def service_order_add_item(order_id):
    """Adiciona um item a uma ordem de serviço."""
    db = get_db()
    
    # Verificar se a ordem de serviço existe e pode ser editada
    order = db.fetch_one("""
        SELECT * FROM service_orders
        WHERE id = %s
    """, (order_id,))
    
    if not order:
        flash('Ordem de serviço não encontrada.', 'danger')
        return redirect(url_for('service_order.service_order_list'))
    
    if order['status'] == 'completed' or order['status'] == 'canceled':
        flash('Não é possível adicionar itens a uma ordem de serviço concluída ou cancelada.', 'danger')
        return redirect(url_for('service_order.service_order_view', order_id=order_id))
    
    # Obter dados do formulário
    supply_id = request.form.get('supply_id')
    quantity = request.form.get('quantity')
    unit_cost = request.form.get('unit_cost')
    
    # Validar dados
    if not supply_id or not quantity or not unit_cost:
        flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
        return redirect(url_for('service_order.service_order_view', order_id=order_id))
    
    try:
        quantity = int(quantity)
        unit_cost = float(unit_cost)
        if quantity <= 0 or unit_cost < 0:
            raise ValueError("Valores devem ser positivos")
    except ValueError:
        flash('Quantidade e custo unitário devem ser números positivos.', 'danger')
        return redirect(url_for('service_order.service_order_view', order_id=order_id))
    
    # Inserir item no banco de dados
    query = """
        INSERT INTO service_order_items
        (service_order_id, supply_id, quantity, unit_cost)
        VALUES (%s, %s, %s, %s)
    """
    params = (order_id, supply_id, quantity, unit_cost)
    
    item_id = db.insert(query, params)
    
    if item_id:
        # Atualizar estoque
        db.update("""
            UPDATE supplies
            SET stock = stock - %s
            WHERE id = %s
        """, (quantity, supply_id))
        
        flash('Item adicionado com sucesso!', 'success')
    else:
        flash('Erro ao adicionar item.', 'danger')
    
    return redirect(url_for('service_order.service_order_view', order_id=order_id))

@service_order_bp.route('/service_orders/add_labor/<int:order_id>', methods=['POST'])
@login_required
def service_order_add_labor(order_id):
    """Adiciona horas trabalhadas a uma ordem de serviço."""
    db = get_db()
    
    # Verificar se a ordem de serviço existe e pode ser editada
    order = db.fetch_one("""
        SELECT * FROM service_orders
        WHERE id = %s
    """, (order_id,))
    
    if not order:
        flash('Ordem de serviço não encontrada.', 'danger')
        return redirect(url_for('service_order.service_order_list'))
    
    if order['status'] == 'completed' or order['status'] == 'canceled':
        flash('Não é possível adicionar horas trabalhadas a uma ordem de serviço concluída ou cancelada.', 'danger')
        return redirect(url_for('service_order.service_order_view', order_id=order_id))
    
    # Obter dados do formulário
    technician_id = request.form.get('technician_id')
    hours_worked = request.form.get('hours_worked')
    hourly_rate = request.form.get('hourly_rate')
    
    # Validar dados
    if not technician_id or not hours_worked or not hourly_rate:
        flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
        return redirect(url_for('service_order.service_order_view', order_id=order_id))
    
    try:
        hours_worked = float(hours_worked)
        hourly_rate = float(hourly_rate)
        if hours_worked <= 0 or hourly_rate < 0:
            raise ValueError("Valores devem ser positivos")
    except ValueError:
        flash('Horas trabalhadas e taxa horária devem ser números positivos.', 'danger')
        return redirect(url_for('service_order.service_order_view', order_id=order_id))
    
    # Inserir horas trabalhadas no banco de dados
    query = """
        INSERT INTO service_order_labor
        (service_order_id, technician_id, hours_worked, hourly_rate)
        VALUES (%s, %s, %s, %s)
    """
    params = (order_id, technician_id, hours_worked, hourly_rate)
    
    labor_id = db.insert(query, params)
    
    if labor_id:
        flash('Horas trabalhadas adicionadas com sucesso!', 'success')
    else:
        flash('Erro ao adicionar horas trabalhadas.', 'danger')
    
    return redirect(url_for('service_order.service_order_view', order_id=order_id))

@service_order_bp.route('/service_orders/cancel/<int:order_id>', methods=['POST'])
@login_required
def service_order_cancel(order_id):
    """Cancela uma ordem de serviço."""
    db = get_db()
    
    # Verificar se a ordem de serviço existe e pode ser cancelada
    order = db.fetch_one("""
        SELECT * FROM service_orders
        WHERE id = %s
    """, (order_id,))
    
    if not order:
        flash('Ordem de serviço não encontrada.', 'danger')
        return redirect(url_for('service_order.service_order_list'))
    
    if order['status'] == 'completed':
        flash('Não é possível cancelar uma ordem de serviço concluída.', 'danger')
        return redirect(url_for('service_order.service_order_view', order_id=order_id))
    
    if order['status'] == 'canceled':
        flash('Esta ordem de serviço já está cancelada.', 'warning')
        return redirect(url_for('service_order.service_order_view', order_id=order_id))
    
    # Cancelar a ordem de serviço
    affected_rows = db.update("""
        UPDATE service_orders
        SET status = 'canceled'
        WHERE id = %s
    """, (order_id,))
    
    if affected_rows > 0:
        # Devolver itens ao estoque
        items = db.fetch_all("""
            SELECT supply_id, quantity
            FROM service_order_items
            WHERE service_order_id = %s
        """, (order_id,))
        
        for item in items:
            db.update("""
                UPDATE supplies
                SET stock = stock + %s
                WHERE id = %s
            """, (item['quantity'], item['supply_id']))
        
        flash('Ordem de serviço cancelada com sucesso!', 'success')
    else:
        flash('Erro ao cancelar ordem de serviço.', 'danger')
    
    return redirect(url_for('service_order.service_order_view', order_id=order_id))

@service_order_bp.route('/service_orders/dashboard')
@login_required
def service_order_dashboard():
    """Dashboard de ordens de serviço."""
    db = get_db()
    
    # Estatísticas de ordens de serviço
    stats = db.fetch_one("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_count,
            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_count,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count,
            SUM(CASE WHEN status = 'canceled' THEN 1 ELSE 0 END) as canceled_count
        FROM service_orders
        WHERE active = TRUE
    """)
    
    # Ordens de serviço por tipo
    by_type = db.fetch_all("""
        SELECT type, COUNT(*) as count
        FROM service_orders
        WHERE active = TRUE
        GROUP BY type
    """)
    
    # Ordens de serviço por cliente (top 5)
    by_customer = db.fetch_all("""
        SELECT c.name as customer_name, COUNT(*) as count
        FROM service_orders so
        JOIN customers c ON so.customer_id = c.id
        WHERE so.active = TRUE
        GROUP BY c.name
        ORDER BY count DESC
        LIMIT 5
    """)
    
    # Ordens de serviço por técnico
    by_technician = db.fetch_all("""
        SELECT t.name as technician_name, COUNT(*) as count
        FROM service_orders so
        JOIN technicians t ON so.technician_id = t.id
        WHERE so.active = TRUE
        GROUP BY t.name
        ORDER BY count DESC
    """)
    
    # Ordens de serviço recentes
    recent_orders = db.fetch_all("""
        SELECT so.*, c.name as customer_name, e.name as equipment_name, 
               t.name as technician_name
        FROM service_orders so
        JOIN customers c ON so.customer_id = c.id
        JOIN equipment e ON so.equipment_id = e.id
        LEFT JOIN technicians t ON so.technician_id = t.id
        WHERE so.active = TRUE
        ORDER BY so.open_date DESC
        LIMIT 5
    """)
    
    return render_template(
        'service_order_dashboard.html',
        stats=stats,
        by_type=by_type,
        by_customer=by_customer,
        by_technician=by_technician,
        recent_orders=recent_orders,
        active_page='service_orders'
    )
