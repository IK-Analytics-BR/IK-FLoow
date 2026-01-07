#!/bin/bash

# ========================================
# SCRIPT DE CONFIGURAÇÃO INICIAL - AWS EC2
# Supply Chain System
# Execute como: bash setup_ec2.sh
# ========================================

set -e

echo "========================================="
echo "CONFIGURAÇÃO INICIAL - AWS EC2"
echo "Supply Chain System"
echo "========================================="

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Verificar se está rodando como ubuntu
if [ "$USER" != "ubuntu" ]; then
    log_error "Execute este script como usuário ubuntu!"
    exit 1
fi

# 1. Atualizar sistema
log_info "Atualizando sistema..."
sudo apt update
sudo apt upgrade -y

# 2. Instalar dependências básicas
log_info "Instalando dependências básicas..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    git \
    curl \
    wget \
    unzip \
    vim \
    htop

# 3. Instalar MySQL
log_info "Instalando MySQL Server..."
sudo apt install -y mysql-server

# 4. Configurar MySQL
log_info "Configurando MySQL..."
sudo systemctl start mysql
sudo systemctl enable mysql

# 5. Instalar Nginx
log_info "Instalando Nginx..."
sudo apt install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# 6. Configurar Firewall
log_info "Configurando firewall (UFW)..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# 7. Criar diretórios
log_info "Criando diretórios..."
mkdir -p /home/ubuntu/backups
mkdir -p /home/ubuntu/SupplyChainSystem/logs

# 8. Configurar fuso horário
log_info "Configurando timezone para America/Sao_Paulo..."
sudo timedatectl set-timezone America/Sao_Paulo

# 9. Instalar Certbot (SSL)
log_info "Instalando Certbot..."
sudo apt install -y certbot python3-certbot-nginx

# 10. Otimizações de sistema
log_info "Aplicando otimizações..."
# Aumentar limites de arquivos
echo "fs.file-max = 65535" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# 11. Criar swap se não existir (recomendado para instâncias pequenas)
if [ ! -f /swapfile ]; then
    log_info "Criando arquivo swap (2GB)..."
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

# 12. Exibir informações
echo ""
echo "========================================="
log_info "CONFIGURAÇÃO INICIAL CONCLUÍDA!"
echo "========================================="
echo ""
echo "📋 Próximos passos:"
echo ""
echo "1. Configurar MySQL:"
echo "   sudo mysql_secure_installation"
echo ""
echo "2. Criar banco de dados:"
echo "   sudo mysql -u root -p"
echo "   CREATE DATABASE supply_chain_system;"
echo "   CREATE USER 'supply_user'@'localhost' IDENTIFIED BY 'senha';"
echo "   GRANT ALL ON supply_chain_system.* TO 'supply_user'@'localhost';"
echo ""
echo "3. Clonar repositório:"
echo "   cd /home/ubuntu"
echo "   git clone <seu-repositorio>"
echo ""
echo "4. Configurar aplicação:"
echo "   cd SupplyChainSystem"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo ""
echo "5. Configurar variáveis de ambiente:"
echo "   cp .env.production.example .env"
echo "   nano .env  # Editar com seus valores"
echo ""
echo "6. Configurar serviços:"
echo "   sudo cp supplychain.service.example /etc/systemd/system/supplychain.service"
echo "   sudo cp nginx.conf.example /etc/nginx/sites-available/supplychain"
echo "   sudo ln -s /etc/nginx/sites-available/supplychain /etc/nginx/sites-enabled/"
echo ""
echo "7. Iniciar serviços:"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl start supplychain"
echo "   sudo systemctl enable supplychain"
echo "   sudo systemctl restart nginx"
echo ""
echo "========================================="
echo "📊 Informações do Sistema:"
echo "========================================="
echo "IP Público: $(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo "Hostname: $(hostname)"
echo "Memória: $(free -h | awk 'NR==2{print $2}')"
echo "Disco: $(df -h / | awk 'NR==2{print $2}')"
echo "========================================="
