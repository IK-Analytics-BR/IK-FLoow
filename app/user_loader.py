"""
Módulo para carregar usuários para o Flask-Login.
"""
from database import get_db

def load_user(user_id):
    """Carrega um usuário pelo ID para o Flask-Login."""
    db = get_db()
    user = db.fetch_one("SELECT * FROM users WHERE id = %s", (user_id,))
    if user:
        # Adicionar propriedades necessárias para o Flask-Login
        user['is_authenticated'] = True
        user['is_active'] = True
        user['is_anonymous'] = False
        user['get_id'] = lambda: str(user['id'])
    return user
