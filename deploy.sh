#!/bin/bash

# ========================================
# SCRIPT DE DEPLOY AUTOMÁTICO - AWS EC2
# Supply Chain System
# ========================================

set -e  # Para execução em caso de erro

echo "=================================="
echo "DEPLOY - SUPPLY CHAIN SYSTEM"
echo "=================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variáveis
APP_DIR="/home/ubuntu/SupplyChainSystem"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="supplychain"

# Função para log
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. Atualizar código
log_info "Atualizando código..."
cd $APP_DIR
git pull origin main

# 2. Ativar ambiente virtual
log_info "Ativando ambiente virtual..."
source $VENV_DIR/bin/activate

# 3. Atualizar dependências
log_info "Atualizando dependências..."
pip install -r requirements.txt --upgrade

# 4. Executar migrations (se houver)
log_info "Verificando migrations..."
if [ -d "$APP_DIR/database/migrations" ]; then
    for sql_file in $APP_DIR/database/migrations/*.sql; do
        if [ -f "$sql_file" ]; then
            log_info "Executando: $(basename $sql_file)"
            # Nota: ajuste user/senha conforme seu .env
            # mysql -u supply_user -p supply_chain_system < "$sql_file"
        fi
    done
fi

# 5. Coletar arquivos estáticos (se necessário)
log_info "Coletando arquivos estáticos..."
# Se tiver comando específico, adicionar aqui

# 6. Reiniciar serviço
log_info "Reiniciando serviço $SERVICE_NAME..."
sudo systemctl restart $SERVICE_NAME

# 7. Verificar status
sleep 3
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    log_info "✓ Serviço $SERVICE_NAME está rodando!"
else
    log_error "✗ Falha ao iniciar $SERVICE_NAME"
    sudo systemctl status $SERVICE_NAME
    exit 1
fi

# 8. Reiniciar Nginx
log_info "Reiniciando Nginx..."
sudo systemctl restart nginx

if sudo systemctl is-active --quiet nginx; then
    log_info "✓ Nginx está rodando!"
else
    log_error "✗ Falha ao iniciar Nginx"
    exit 1
fi

# 9. Verificar logs
log_info "Últimas linhas do log:"
sudo journalctl -u $SERVICE_NAME -n 10 --no-pager

echo ""
log_info "=================================="
log_info "DEPLOY CONCLUÍDO COM SUCESSO!"
log_info "=================================="
log_info "Acesse: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
