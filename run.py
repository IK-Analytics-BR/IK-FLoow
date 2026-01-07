"""
Script principal para executar a aplicação
Detecta automaticamente o ambiente através do .env
"""
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
env_path = os.path.join('app', '.env')
load_dotenv(env_path)

# Detectar ambiente
db_host = os.getenv('DB_HOST', 'localhost')
debug_mode = os.getenv('DEBUG', 'True') == 'True'
flask_env = os.getenv('FLASK_ENV', 'development')

print("=" * 60)
if flask_env == 'production':
    print("☁️  MODO: PRODUÇÃO")
else:
    print("🏠 MODO: DESENVOLVIMENTO")
print("=" * 60)
print(f"🗄️  Banco: {db_host}")
print(f"🐛 Debug: {debug_mode}")
print("=" * 60)
print()

# Importar aplicação
from app.main_mysql import app

if __name__ == '__main__':
    app.run(debug=debug_mode, host='0.0.0.0', port=8080)
