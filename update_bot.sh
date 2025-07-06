#!/bin/bash
# Script to update and restart the Viral Instagram Bot

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Bot directory
BOT_DIR="/home/coder/Desktop/2202/Viralinstabot"
SERVICE_NAME="viralinstabot"

echo -e "${YELLOW}=== Viral Instagram Bot Update Script ===${NC}"
echo

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        echo -e "${RED}This script should not be run as root!${NC}"
        echo "Run it as the regular user and it will use sudo when needed."
        exit 1
    fi
}

# Function to check service status
check_status() {
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo -e "${GREEN}✓ Bot is currently running${NC}"
        return 0
    else
        echo -e "${RED}✗ Bot is not running${NC}"
        return 1
    fi
}

# Function to update code
update_code() {
    echo -e "${YELLOW}Updating code...${NC}"
    cd "$BOT_DIR"
    
    # If it's a git repository, pull latest changes
    if [[ -d .git ]]; then
        echo "Pulling latest changes from git..."
        git pull
    fi
    
    # Update dependencies if requirements.txt changed
    if [[ -f requirements.txt ]]; then
        echo "Checking for dependency updates..."
        pip3 install -r requirements.txt --upgrade --user
    fi
    
    echo -e "${GREEN}✓ Code updated${NC}"
}

# Function to restart service
restart_service() {
    echo -e "${YELLOW}Restarting bot service...${NC}"
    
    # Stop the service
    sudo systemctl stop $SERVICE_NAME
    sleep 2
    
    # Start the service
    sudo systemctl start $SERVICE_NAME
    sleep 3
    
    # Check if started successfully
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo -e "${GREEN}✓ Bot restarted successfully${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to restart bot${NC}"
        echo "Checking logs..."
        sudo journalctl -u $SERVICE_NAME -n 20 --no-pager
        return 1
    fi
}

# Main execution
main() {
    check_root
    
    echo "1. Checking current status..."
    check_status
    
    echo
    echo "2. Updating code..."
    update_code
    
    echo
    echo "3. Restarting service..."
    restart_service
    
    echo
    echo "4. Final status check..."
    check_status
    
    echo
    echo -e "${GREEN}=== Update complete! ===${NC}"
    echo
    echo "Useful commands:"
    echo "  - View logs:    sudo journalctl -u $SERVICE_NAME -f"
    echo "  - Check status: sudo systemctl status $SERVICE_NAME"
    echo "  - Stop bot:     sudo systemctl stop $SERVICE_NAME"
    echo "  - Start bot:    sudo systemctl start $SERVICE_NAME"
}

# Run main function
main