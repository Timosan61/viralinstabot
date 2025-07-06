"""Logging configuration."""

import logging
import logging.config
import os
from pathlib import Path
import yaml


def setup_logging() -> None:
    """Setup logging configuration."""
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Load logging config
    config_path = Path("config/logging.yml")
    
    if config_path.exists():
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
    else:
        # Fallback to basic config
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("logs/bot.log")
            ]
        )
    
    # Set aiogram logging level based on environment
    if os.getenv("ENV") == "production":
        logging.getLogger("aiogram").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)