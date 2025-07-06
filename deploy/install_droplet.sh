#!/bin/bash

# =============================================================================
# Viralinstabot Droplet Installation Script
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="viralinstabot"
APP_USER="botuser"
APP_DIR="/opt/$APP_NAME"
SERVICE_NAME="$APP_NAME.service"
REPO_URL="https://github.com/Timosan61/viralinstabot.git"

# Functions
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root (use sudo)"
    fi
}

install_dependencies() {
    log "Installing system dependencies..."
    
    # Update system
    apt update && apt upgrade -y
    
    # Install required packages
    apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        git \
        curl \
        wget \
        unzip \
        supervisor \
        nginx \
        ufw \
        htop \
        fail2ban \
        logrotate
    
    # Install Docker and Docker Compose (optional)
    if ! command -v docker &> /dev/null; then
        log "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm get-docker.sh
        
        # Install Docker Compose
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi
}

create_user() {
    log "Creating application user..."
    
    if ! id "$APP_USER" &>/dev/null; then
        useradd -r -s /bin/bash -m -d /home/$APP_USER $APP_USER
        usermod -aG docker $APP_USER 2>/dev/null || true
    fi
}

setup_application() {
    log "Setting up application directory..."
    
    # Create app directory
    mkdir -p $APP_DIR
    cd $APP_DIR
    
    # Clone repository
    if [ -d ".git" ]; then
        log "Updating existing repository..."
        git pull origin main
    else
        log "Cloning repository..."
        git clone $REPO_URL .
    fi
    
    # Set permissions
    chown -R $APP_USER:$APP_USER $APP_DIR
    
    # Create data directories
    sudo -u $APP_USER mkdir -p $APP_DIR/{data,logs,exports}
    sudo -u $APP_USER mkdir -p $APP_DIR/data/reports
}

setup_python_environment() {
    log "Setting up Python virtual environment..."
    
    cd $APP_DIR
    
    # Create virtual environment
    sudo -u $APP_USER python3 -m venv venv
    
    # Install Python dependencies
    sudo -u $APP_USER bash -c "
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
    "
}

setup_environment_file() {
    log "Setting up environment configuration..."
    
    # Create .env file from template
    if [ ! -f "$APP_DIR/.env" ]; then
        sudo -u $APP_USER cp $APP_DIR/.env.example $APP_DIR/.env
        
        warn "IMPORTANT: Edit $APP_DIR/.env and set your API tokens:"
        warn "  - TELEGRAM_BOT_TOKEN"
        warn "  - APIFY_API_TOKEN"
        warn "  - OPENAI_API_KEY"
        warn ""
        warn "Example: nano $APP_DIR/.env"
    fi
}

create_systemd_service() {
    log "Creating systemd service..."
    
    cat > /etc/systemd/system/$SERVICE_NAME << EOF
[Unit]
Description=Viralinstabot Telegram Bot
After=network.target
Wants=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/python -m src.bot.main
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$APP_NAME

# Security
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_DIR/data $APP_DIR/logs $APP_DIR/exports /tmp

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable $SERVICE_NAME
}

setup_logrotate() {
    log "Setting up log rotation..."
    
    cat > /etc/logrotate.d/$APP_NAME << EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $APP_USER $APP_USER
    postrotate
        systemctl reload $SERVICE_NAME > /dev/null 2>&1 || true
    endscript
}
EOF
}

setup_nginx() {
    log "Setting up Nginx (optional)..."
    
    # Create simple health check endpoint config
    cat > /etc/nginx/sites-available/$APP_NAME << EOF
server {
    listen 80;
    server_name _;
    
    location /health {
        access_log off;
        return 200 "Viralinstabot is running\\n";
        add_header Content-Type text/plain;
    }
    
    location / {
        return 404;
    }
}
EOF

    # Enable site (optional)
    # ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
    # nginx -t && systemctl reload nginx
}

setup_firewall() {
    log "Configuring firewall..."
    
    # Enable UFW
    ufw --force enable
    
    # Allow SSH
    ufw allow ssh
    
    # Allow HTTP/HTTPS (if using nginx)
    ufw allow 80
    ufw allow 443
    
    # Show status
    ufw status
}

create_management_scripts() {
    log "Creating management scripts..."
    
    # Bot control script
    cat > $APP_DIR/bot_control.sh << 'EOF'
#!/bin/bash

SERVICE_NAME="viralinstabot.service"
APP_DIR="/opt/viralinstabot"

case "$1" in
    start)
        echo "Starting bot..."
        sudo systemctl start $SERVICE_NAME
        ;;
    stop)
        echo "Stopping bot..."
        sudo systemctl stop $SERVICE_NAME
        ;;
    restart)
        echo "Restarting bot..."
        sudo systemctl restart $SERVICE_NAME
        ;;
    status)
        sudo systemctl status $SERVICE_NAME
        ;;
    logs)
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    update)
        echo "Updating bot..."
        cd $APP_DIR
        sudo -u botuser git pull origin main
        sudo -u botuser bash -c "source venv/bin/activate && pip install -r requirements.txt"
        sudo systemctl restart $SERVICE_NAME
        echo "Bot updated and restarted"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|update}"
        exit 1
        ;;
esac
EOF

    chmod +x $APP_DIR/bot_control.sh
    ln -sf $APP_DIR/bot_control.sh /usr/local/bin/botctl
    
    # Update script
    cat > $APP_DIR/update_bot.sh << 'EOF'
#!/bin/bash
cd /opt/viralinstabot
sudo -u botuser git pull origin main
sudo -u botuser bash -c "source venv/bin/activate && pip install -r requirements.txt"
sudo systemctl restart viralinstabot.service
echo "Bot updated successfully!"
EOF

    chmod +x $APP_DIR/update_bot.sh
    chown $APP_USER:$APP_USER $APP_DIR/*.sh
}

main() {
    log "Starting Viralinstabot installation on Droplet..."
    
    check_root
    install_dependencies
    create_user
    setup_application
    setup_python_environment
    setup_environment_file
    create_systemd_service
    setup_logrotate
    setup_nginx
    setup_firewall
    create_management_scripts
    
    log "Installation completed!"
    echo ""
    log "Next steps:"
    echo "1. Edit configuration: nano $APP_DIR/.env"
    echo "2. Start the bot: systemctl start $SERVICE_NAME"
    echo "3. Check status: systemctl status $SERVICE_NAME"
    echo "4. View logs: journalctl -u $SERVICE_NAME -f"
    echo ""
    log "Management commands:"
    echo "- botctl start|stop|restart|status|logs|update"
    echo "- $APP_DIR/bot_control.sh start|stop|restart|status|logs|update"
    echo ""
    warn "Remember to set your API tokens in $APP_DIR/.env before starting!"
}

# Run main function
main "$@"
EOF