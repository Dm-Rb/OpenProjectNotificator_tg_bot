from telegram_bot.bot import start_telegram_bot
from web_server import start_fastapi
import asyncio


async def main():
    await asyncio.gather(
        start_telegram_bot(),
        start_fastapi()
    )

if __name__ == "__main__":
    asyncio.run(main())