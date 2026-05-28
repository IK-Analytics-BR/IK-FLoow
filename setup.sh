#!/bin/bash
# =====================================================
# Script de Setup Automático - IK Flow
# Este script configura o ambiente completo para produção
# =====================================================

set -e

echo "=========================================="
echo "  IK Flow - Setup Automático"
echo "=========================================="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para imprimir mensagens
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERRO]${NC} $1"
}

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then 
    print_error "Este script precisa ser executado como root (sudo)"
    exit 1
fi

# Diretório da aplicação
APP_DIR="/var/www/ikflow"
DB_NAME="ikflow"
DB_USER="ikflow_user"
DB_PASS="IkFl0w@2024!DB"

print_status "Diretório da aplicação: $APP_DIR"

# 1. Criar diretório da aplicação
print_status "1. Criando estrutura de diretórios..."
mkdir -p $APP_DIR
mkdir -p $APP_DIR/app/static/uploads
mkdir -p /var/www/certbot
chmod -R 755 $APP_DIR

# 2. Verificar MySQL
print_status "2. Verificando MySQL..."
if ! command -v mysql &> /dev/null; then
    print_warning "MySQL não encontrado. Instalando..."
    apt-get update
    apt-get install -y mysql-server
    systemctl start mysql
    systemctl enable mysql
fi

# 3. Criar banco de dados e usuário
print_status "3. Configurando banco de dados..."
mysql -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -e "CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';"
mysql -e "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

# 4. Importar schema inicial
print_status "4. Importando schema do banco de dados..."
if [ -f "$APP_DIR/app/scripts/init_database.sql" ]; then
    mysql -u $DB_USER -p'$DB_PASS' $DB_NAME < $APP_DIR/app/scripts/init_database.sql
    print_status "   ✓ Schema importado com sucesso"
else
    print_warning "   Arquivo init_database.sql não encontrado. Execute manualmente depois."
fi

# 5. Configurar ambiente Python
print_status "5. Configurando ambiente Python..."
cd $APP_DIR
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Instalar dependências
print_status "   Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt 2>/dev/null || {
    print_warning "   requirements.txt não encontrado, instalando dependências básicas..."
    pip install flask flask-login mysql-connector-python python-dotenv werkzeug gunicorn
}

# 6. Configurar arquivo .env
print_status "6. Configurando variáveis de ambiente..."
cat > $APP_DIR/app/.env << EOF
# Configuração de Banco de Dados MySQL
DB_HOST=localhost
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASS
DB_NAME=$DB_NAME
DB_PORT=3306

# Configuração Flask
SECRET_KEY=ikflow-secret-key-production-$(date +%s)
FLASK_ENV=production
DEBUG=False

# Configuração de Email (opcional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=
MAIL_PASSWORD=

# Configurações adicionais
TIMEZONE=America/Sao_Paulo
EOF

chmod 600 $APP_DIR/app/.env

# 7. Configurar Nginx
print_status "7. Configurando Nginx..."
if ! command -v nginx &> /dev/null; then
    print_warning "   Nginx não encontrado. Instalando..."
    apt-get install -y nginx
fi

cat > /etc/nginx/sites-available/ikflow << 'NGINX_EOF'
server {
    listen 80;
    server_name ikflow.cloud www.ikflow.cloud _;

    # Permitir validação Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirecionar / para /login
    location = / {
        return 302 /login;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static {
        alias /var/www/ikflow/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
NGINX_EOF

# Ativar site
ln -sf /etc/nginx/sites-available/ikflow /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Testar configuração
nginx -t && systemctl restart nginx

# 8. Configurar Gunicorn como serviço systemd
print_status "8. Configurando serviço Gunicorn..."
cat > /etc/systemd/system/ikflow.service << 'SERVICE_EOF'
[Unit]
Description=IK Flow Gunicorn Service
After=network.target mysql.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/var/www/ikflow
Environment="PATH=/var/www/ikflow/venv/bin"
ExecStart=/var/www/ikflow/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 120 wsgi:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE_EOF

systemctl daemon-reload
systemctl enable ikflow.service

# 9. Iniciar serviço
print_status "9. Iniciando serviço..."
systemctl start ikflow.service

# 10. Verificar status
print_status "10. Verificando instalação..."
sleep 3

if systemctl is-active --quiet ikflow.service; then
    print_status "   ✓ Serviço IK Flow está rodando"
else
    print_error "   ✗ Serviço não iniciou. Verificando logs..."
    journalctl -u ikflow.service -n 20
fi

if systemctl is-active --quiet nginx; then
    print_status "   ✓ Nginx está rodando"
else
    print_error "   ✗ Nginx não iniciou"
fi

echo ""
echo "=========================================="
echo -e "  ${GREEN}Setup concluído!${NC}"
echo "=========================================="
echo ""
echo "Informações de acesso:"
echo "  URL: http://ikflow.cloud/login"
echo "  Usuário: admin"
echo "  Senha: admin123"
echo ""
echo "Banco de dados:"
echo "  Nome: $DB_NAME"
echo "  Usuário: $DB_USER"
echo "  Senha: $DB_PASS"
echo ""
echo "Comandos úteis:"
echo "  Ver logs: journalctl -u ikflow.service -f"
echo "  Reiniciar: systemctl restart ikflow.service"
echo "  Status: systemctl status ikflow.service"
echo ""
echo "Para SSL (Let's Encrypt):"
echo "  certbot --nginx -d ikflow.cloud -d www.ikflow.cloud"
echo ""
