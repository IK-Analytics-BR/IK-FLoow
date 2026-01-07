from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import sys
import hashlib
import re
from functools import wraps

# Funções de segurança simplificadas
def verify_password(stored_password, provided_password):
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    # Se a senha armazenada já for um hash SHA-256 (64 caracteres hex)
    if len(stored_password) == 64 and all(c in '0123456789abcdef' for c in stored_password.lower()):
        return stored_password == hashlib.sha256(provided_password.encode()).hexdigest()
    # Caso contrário, é uma senha em texto plano (para compatibilidade com usuários existentes)
    return stored_password == provided_password

def sanitize_input(input_string):
    """Sanitiza uma string de entrada para prevenir injeção de SQL e XSS."""
    if input_string is None:
        return None
    # Remover caracteres potencialmente perigosos
    sanitized = re.sub(r'[\'";\\\\/]', '', input_string)
    # Escapar tags HTML
    sanitized = sanitized.replace('<', '&lt;').replace('>', '&gt;')
    return sanitized

# Importar os blueprints
from routes.cliente_routes import cliente_bp
from routes.produto_routes import produto_bp
from routes.insumo_routes import insumo_bp
from routes.equipamento_routes import equipamento_bp
from routes.fornecedor_routes import fornecedor_bp
from routes.usuario_routes import usuario_bp

# Criar a aplicação Flask
app = Flask(__name__)
app.secret_key = 'chave_secreta_do_sistema'

# Registrar os blueprints
app.register_blueprint(cliente_bp)
app.register_blueprint(produto_bp)
app.register_blueprint(insumo_bp)
app.register_blueprint(equipamento_bp)
app.register_blueprint(fornecedor_bp)
app.register_blueprint(usuario_bp)

# Banco de dados em memória
db = {
    'users': [
        {'id': '1', 'name': 'Administrador', 'username': 'admin', 'password': 'admin123', 'email': 'admin@sistema.com', 'role': 'admin'},
        {'id': '2', 'name': 'Usuário Padrão', 'username': 'user', 'password': 'user123', 'email': 'user@sistema.com', 'role': 'user'}
    ],
    'customers': [
        {'id': '1', 'name': 'Indústria Química ABC', 'cnpj': '12.345.678/0001-90', 'address': 'Rua Industrial, 123', 'city': 'São Paulo', 'state': 'SP', 'phone': '(11) 3456-7890', 'email': 'contato@industriaabc.com', 'active': True},
        {'id': '2', 'name': 'Metalúrgica XYZ', 'cnpj': '98.765.432/0001-10', 'address': 'Av. das Indústrias, 456', 'city': 'Belo Horizonte', 'state': 'MG', 'phone': '(31) 3456-7890', 'email': 'contato@metalxyz.com', 'active': True}
    ],
    'products': [
        {'id': '1', 'name': 'Bomba Centrífuga BC-300', 'description': 'Bomba centrífuga para líquidos industriais', 'price': 5000.00, 'category': 'bomba', 'active': True},
        {'id': '2', 'name': 'Motor Elétrico 15CV', 'description': 'Motor elétrico trifásico de alta eficiência', 'price': 3200.00, 'category': 'motor', 'active': True}
    ],
    'supplies': [
        {'id': '1', 'name': 'Rolamento 6204', 'description': 'Rolamento de esferas para motores', 'stock': 5, 'min_stock': 10, 'price': 45.00, 'supplier_id': '1', 'active': True},
        {'id': '2', 'name': 'Correia A36', 'description': 'Correia de transmissão industrial', 'stock': 3, 'min_stock': 8, 'price': 28.50, 'supplier_id': '2', 'active': True}
    ],
    'equipment': [
        {'id': '1', 'name': 'Bomba Centrífuga BC-300', 'customer_id': '1', 'installation_date': '2025-01-15', 'next_maintenance': '2025-07-15', 'notes': 'Instalação realizada com sucesso.', 'active': True},
        {'id': '2', 'name': 'Motor Elétrico 15CV', 'customer_id': '2', 'installation_date': '2025-02-20', 'next_maintenance': '2025-08-20', 'notes': 'Verificar ruído após 100 horas de uso.', 'active': True}
    ],
    'suppliers': [
        {'id': '1', 'name': 'Rolamentos Brasil', 'cnpj': '11.222.333/0001-44', 'address': 'Av. Industrial, 1000', 'city': 'São Paulo', 'state': 'SP', 'phone': '(11) 3333-4444', 'email': 'contato@rolamentosbrasil.com', 'website': 'https://www.rolamentosbrasil.com', 'notes': 'Fornecedor principal de rolamentos.', 'active': True},
        {'id': '2', 'name': 'Correias & Cia', 'cnpj': '22.333.444/0001-55', 'address': 'Rua das Indústrias, 500', 'city': 'Belo Horizonte', 'state': 'MG', 'phone': '(31) 4444-5555', 'email': 'vendas@correiasecia.com', 'website': 'https://www.correiasecia.com', 'notes': 'Especialista em correias industriais.', 'active': True}
    ]
}

# Funções auxiliares
def get_user_by_username(username):
    return next((user for user in db['users'] if user['username'] == username), None)

def get_low_stock_supplies():
    return [supply for supply in db['supplies'] if supply['active'] and supply['stock'] < supply['min_stock']]

def get_maintenance_equipment():
    from datetime import datetime, timedelta
    today = datetime.now()
    next_month = today + timedelta(days=30)
    next_month_str = next_month.strftime('%Y-%m-%d')
    
    return [equip for equip in db['equipment'] if equip['active'] and equip.get('next_maintenance') and equip['next_maintenance'] <= next_month_str]

# Decorador para verificar se o usuário está logado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Por favor, faça login para acessar esta página.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorador para verificar se o usuário é administrador
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Por favor, faça login para acessar esta página.', 'danger')
            return redirect(url_for('login'))
        
        if session.get('role') != 'admin':
            flash('Você não tem permissão para acessar esta página.', 'danger')
            return redirect(url_for('dashboard'))
            
        return f(*args, **kwargs)
    return decorated_function

# Rotas de autenticação
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = sanitize_input(request.form['username'])
        password = request.form['password']
        
        user = get_user_by_username(username)
        if user and verify_password(user['password'], password):
            session['username'] = username
            session['role'] = user['role']
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha inválidos. Tente novamente.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))

# Rota do dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    # Contagem de itens
    customers_count = len([c for c in db['customers'] if c['active']])
    products_count = len([p for p in db['products'] if p['active']])
    supplies_count = len([s for s in db['supplies'] if s['active']])
    suppliers_count = len([s for s in db['suppliers'] if s['active']])
    
    # Insumos com estoque baixo
    low_stock_supplies = []
    for supply in get_low_stock_supplies():
        supplier = next((s for s in db['suppliers'] if s['id'] == supply['supplier_id']), None)
        low_stock_supplies.append({
            'id': supply['id'],
            'name': supply['name'],
            'stock': supply['stock'],
            'min_stock': supply['min_stock'],
            'supplier_name': supplier['name'] if supplier else 'N/A'
        })
    
    # Equipamentos para manutenção
    maintenance_equipment = get_maintenance_equipment()
    
    return render_template(
        'dashboard.html',
        active_page='dashboard',
        customers_count=customers_count,
        products_count=products_count,
        supplies_count=supplies_count,
        suppliers_count=suppliers_count,
        low_stock_supplies=low_stock_supplies,
        maintenance_equipment=maintenance_equipment
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
