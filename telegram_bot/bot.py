from config import config_
from aiogram import Bot, Dispatcher
import telegram_bot.handlers as handlers


bot = Bot(token=config_.BOT_TOKEN)
dp = Dispatcher()
dp.include_router(handlers.router)


async def start_telegram_bot():
    await dp.start_polling(bot)
