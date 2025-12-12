from config import config_
from aiogram import Bot, Dispatcher
import telegram_bot.handlers as handlers


bot = Bot(token=config_.BOT_TOKEN)
dp = Dispatcher()
dp.include_router(handlers.router)


async def start_telegram_bot():
    """Main function to start the telegram bot that is imported from the entry point (run.py)"""

    await dp.start_polling(bot)
