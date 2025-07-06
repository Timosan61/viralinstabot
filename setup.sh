#!/bin/bash
# Setup script for Instagram Viral Bot

echo "Setting up Instagram Viral Bot..."

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p logs data/reports

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please update .env file with your API keys!"
fi

# Initialize database
echo "Initializing database..."
python -c "
import asyncio
from src.storage.sqlite import db
asyncio.run(db.init_db())
print('Database initialized!')
"

echo "Setup complete!"
echo ""
echo "To run the bot:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run the bot: python run.py"
echo ""
echo "Don't forget to update your API keys in .env file!"