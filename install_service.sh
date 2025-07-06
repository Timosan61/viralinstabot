#!/bin/bash
# Script to install the Viral Instagram Bot as a systemd service

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BOT_DIR="/home/coder/Desktop/2202/Viralinstabot"
SERVICE_FILE="viralinstabot.service"
SERVICE_NAME="viralinstabot"

echo -e "${BLUE}=== Viral Instagram Bot Service Installation ===${NC}"
echo

# Check if running with proper permissions
if [[ $EUID -eq 0 ]]; then
    echo -e "${RED}This script should not be run as root!${NC}"
    echo "Run it as a regular user, it will ask for sudo when needed."
    exit 1
fi

# Check if service file exists
if [[ ! -f "$BOT_DIR/$SERVICE_FILE" ]]; then
    echo -e "${RED}Service file not found: $BOT_DIR/$SERVICE_FILE${NC}"
    exit 1
fi

# Function to stop any running instances
stop_existing() {
    echo -e "${YELLOW}Stopping any existing bot instances...${NC}"
    
    # Stop systemd service if exists
    if systemctl is-active --quiet $SERVICE_NAME 2>/dev/null; then
        sudo systemctl stop $SERVICE_NAME
        echo "  - Stopped systemd service"
    fi
    
    # Kill any remaining python processes running the bot
    pkill -f "python.*run.py" 2>/dev/null || true
    pkill -f "python.*main.py" 2>/dev/null || true
    
    echo -e "${GREEN}✓ All instances stopped${NC}"
}

# Function to install service
install_service() {
    echo -e "${YELLOW}Installing systemd service...${NC}"
    
    # Copy service file to systemd directory
    sudo cp "$BOT_DIR/$SERVICE_FILE" /etc/systemd/system/
    
    # Reload systemd daemon
    sudo systemctl daemon-reload
    
    # Enable service to start on boot
    sudo systemctl enable $SERVICE_NAME
    
    echo -e "${GREEN}✓ Service installed and enabled${NC}"
}

# Function to start service
start_service() {
    echo -e "${YELLOW}Starting the bot service...${NC}"
    
    # Start the service
    sudo systemctl start $SERVICE_NAME
    
    # Wait a moment for startup
    sleep 3
    
    # Check if running
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo -e "${GREEN}✓ Bot service started successfully${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to start bot service${NC}"
        echo "Checking logs..."
        sudo journalctl -u $SERVICE_NAME -n 20 --no-pager
        return 1
    fi
}

# Function to show status
show_status() {
    echo -e "${YELLOW}Service status:${NC}"
    sudo systemctl status $SERVICE_NAME --no-pager || true
}

# Main installation process
main() {
    echo "This will install the Viral Instagram Bot as a system service."
    echo "The bot will:"
    echo "  - Start automatically on system boot"
    echo "  - Restart automatically if it crashes"
    echo "  - Log to system journal"
    echo
    read -p "Continue with installation? (y/N) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    
    echo
    echo "1. Stopping existing instances..."
    stop_existing
    
    echo
    echo "2. Installing service..."
    install_service
    
    echo
    echo "3. Starting service..."
    if start_service; then
        echo
        echo "4. Checking status..."
        show_status
        
        echo
        echo -e "${GREEN}=== Installation complete! ===${NC}"
        echo
        echo "Service management commands:"
        echo "  - Start:   sudo systemctl start $SERVICE_NAME"
        echo "  - Stop:    sudo systemctl stop $SERVICE_NAME"
        echo "  - Restart: sudo systemctl restart $SERVICE_NAME"
        echo "  - Status:  sudo systemctl status $SERVICE_NAME"
        echo "  - Logs:    sudo journalctl -u $SERVICE_NAME -f"
        echo "  - Update:  ./update_bot.sh"
        echo
        echo "The bot is now running as a system service!"
    else
        echo
        echo -e "${RED}Installation completed but the service failed to start.${NC}"
        echo "Please check the logs and fix any issues."
        exit 1
    fi
}

# Run main function
main