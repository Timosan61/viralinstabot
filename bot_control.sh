#!/bin/bash
# Bot control script - Easy management of Viral Instagram Bot

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SERVICE_NAME="viralinstabot"

# Function to show menu
show_menu() {
    echo -e "${BLUE}=== Viral Instagram Bot Control Panel ===${NC}"
    echo
    echo "1) Start bot"
    echo "2) Stop bot"
    echo "3) Restart bot"
    echo "4) Show status"
    echo "5) View logs (live)"
    echo "6) View last 50 log lines"
    echo "7) Update and restart"
    echo "8) Install as service"
    echo "9) Uninstall service"
    echo "0) Exit"
    echo
}

# Function to check if service is installed
is_service_installed() {
    if systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
        return 0
    else
        return 1
    fi
}

# Function to start bot
start_bot() {
    if is_service_installed; then
        echo -e "${YELLOW}Starting bot...${NC}"
        sudo systemctl start $SERVICE_NAME
        sleep 2
        if systemctl is-active --quiet $SERVICE_NAME; then
            echo -e "${GREEN}✓ Bot started successfully${NC}"
        else
            echo -e "${RED}✗ Failed to start bot${NC}"
        fi
    else
        echo -e "${RED}Service not installed. Please install first (option 8)${NC}"
    fi
}

# Function to stop bot
stop_bot() {
    if is_service_installed; then
        echo -e "${YELLOW}Stopping bot...${NC}"
        sudo systemctl stop $SERVICE_NAME
        echo -e "${GREEN}✓ Bot stopped${NC}"
    else
        echo -e "${RED}Service not installed${NC}"
    fi
}

# Function to restart bot
restart_bot() {
    if is_service_installed; then
        echo -e "${YELLOW}Restarting bot...${NC}"
        sudo systemctl restart $SERVICE_NAME
        sleep 2
        if systemctl is-active --quiet $SERVICE_NAME; then
            echo -e "${GREEN}✓ Bot restarted successfully${NC}"
        else
            echo -e "${RED}✗ Failed to restart bot${NC}"
        fi
    else
        echo -e "${RED}Service not installed${NC}"
    fi
}

# Function to show status
show_status() {
    if is_service_installed; then
        sudo systemctl status $SERVICE_NAME --no-pager
    else
        echo -e "${RED}Service not installed${NC}"
    fi
}

# Function to view logs
view_logs() {
    if is_service_installed; then
        echo -e "${YELLOW}Showing live logs (Ctrl+C to exit)...${NC}"
        sudo journalctl -u $SERVICE_NAME -f
    else
        echo -e "${RED}Service not installed${NC}"
    fi
}

# Function to view last logs
view_last_logs() {
    if is_service_installed; then
        sudo journalctl -u $SERVICE_NAME -n 50 --no-pager
    else
        echo -e "${RED}Service not installed${NC}"
    fi
}

# Function to update and restart
update_restart() {
    if [[ -f ./update_bot.sh ]]; then
        ./update_bot.sh
    else
        echo -e "${RED}Update script not found${NC}"
    fi
}

# Function to install service
install_service() {
    if [[ -f ./install_service.sh ]]; then
        ./install_service.sh
    else
        echo -e "${RED}Install script not found${NC}"
    fi
}

# Function to uninstall service
uninstall_service() {
    if is_service_installed; then
        echo -e "${YELLOW}Uninstalling service...${NC}"
        
        # Stop service
        sudo systemctl stop $SERVICE_NAME 2>/dev/null || true
        
        # Disable service
        sudo systemctl disable $SERVICE_NAME 2>/dev/null || true
        
        # Remove service file
        sudo rm -f /etc/systemd/system/${SERVICE_NAME}.service
        
        # Reload daemon
        sudo systemctl daemon-reload
        
        echo -e "${GREEN}✓ Service uninstalled${NC}"
    else
        echo -e "${YELLOW}Service is not installed${NC}"
    fi
}

# Main loop
while true; do
    clear
    show_menu
    
    # Show current status
    if is_service_installed; then
        if systemctl is-active --quiet $SERVICE_NAME; then
            echo -e "Status: ${GREEN}● Running${NC}"
        else
            echo -e "Status: ${RED}● Stopped${NC}"
        fi
    else
        echo -e "Status: ${YELLOW}⚠ Not installed${NC}"
    fi
    echo
    
    read -p "Select option: " choice
    
    case $choice in
        1) start_bot ;;
        2) stop_bot ;;
        3) restart_bot ;;
        4) show_status ;;
        5) view_logs ;;
        6) view_last_logs ;;
        7) update_restart ;;
        8) install_service ;;
        9) uninstall_service ;;
        0) echo "Exiting..."; exit 0 ;;
        *) echo -e "${RED}Invalid option${NC}" ;;
    esac
    
    echo
    read -p "Press Enter to continue..."
done