from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from app.models.validators import apply_validators

@apply_validators
class User(UserMixin, db.Model):
    """Modelo para usuários do sistema."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(64))
    role = db.Column(db.String(20), default='user')  # 'admin', 'user', 'supplier'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    @property
    def password(self):
        """Impede acesso direto à senha."""
        raise AttributeError('password is not a readable attribute')
        
    @password.setter
    def password(self, password):
        """Define o hash da senha."""
        self.password_hash = generate_password_hash(password)
        
    def verify_password(self, password):
        """Verifica se a senha está correta."""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Verifica se o usuário é administrador."""
        return self.role == 'admin'
    
    def is_supplier(self):
        """Verifica se o usuário é fornecedor."""
        return self.role == 'supplier'
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    """Carrega um usuário pelo ID para o Flask-Login."""
    return User.query.get(int(user_id))
