"""
Entry point для Telegram бота.
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.bot.handlers import router
from app.bot.states import ConversationState


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def async_main():
    """
    Async main function для запуска бота.
    """
    # Initialize Bot instance
    bot = Bot(token=settings.telegram_bot_token)
    
    # Initialize Dispatcher with FSM storage
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register router with handlers
    dp.include_router(router)
    
    logger.info("Starting bot...")
    
    try:
        # Start polling
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
    finally:
        await bot.session.close()


def main():
    """
    Entry point для command-line scripts.
    Синхронная обёртка для async_main().
    """
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")


if __name__ == "__main__":
    main()
