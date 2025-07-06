"""Main bot entry point."""

import asyncio
import sys
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from src.bot.handlers import router
from src.bot.handlers_export import router as export_router
from src.bot.handlers_contexts import router as contexts_router
from src.storage.sqlite import db
from src.storage.cleaner import cleaner
from src.utils.logger import setup_logging, get_logger
from src.utils.config import config

# Import services for initialization
from src.features.user_context import initialize_context_manager
from src.features.vision_analysis import initialize_scenario_generator


# Setup logging
setup_logging()
logger = get_logger(__name__)


async def on_startup(bot: Bot):
    """Startup handler."""
    logger.info("Bot starting...")
    
    # Initialize database
    await db.init_db()
    
    # Initialize services
    try:
        # Initialize context manager with database session
        context_manager = initialize_context_manager(db.async_session())
        logger.info("Context manager initialized")
        
        # Initialize scenario generator
        scenario_generator = initialize_scenario_generator(config.api.openai_api_key)
        logger.info("Scenario generator initialized")
        
    except Exception as e:
        logger.error(f"Error initializing services: {e}")
    
    # Start report cleaner
    cleaner.start()
    
    # Set bot commands
    from aiogram.types import BotCommand
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать работу с ботом"),
        BotCommand(command="help", description="Показать справку"),
        BotCommand(command="cancel", description="Отменить текущую операцию")
    ])
    
    logger.info("Bot started successfully")


async def on_shutdown(bot: Bot):
    """Shutdown handler."""
    logger.info("Bot shutting down...")
    
    # Stop cleaner
    cleaner.stop()
    
    # No MCP service to close anymore
    
    # Close database
    await db.close()
    
    logger.info("Bot stopped")


async def main():
    """Main function."""
    # Create bot and dispatcher
    bot = Bot(token=config.api.telegram_token)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Register handlers
    dp.include_router(router)
    dp.include_router(export_router)
    dp.include_router(contexts_router)
    
    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Start polling
    try:
        logger.info(f"Bot {config.bot.name} starting in {config.environment} mode")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Create necessary directories
    Path("logs").mkdir(exist_ok=True)
    Path("data/reports").mkdir(parents=True, exist_ok=True)
    
    # Run bot
    asyncio.run(main())