from fastapi import FastAPI, Request
import uvicorn
from config import config_
from service.open_project_service import open_prj_service
from telegram_bot.handlers import send_notifications
from telegram_bot.bot import bot as bot_obj
import logging
import os



log_file_path = os.path.join(config_.DIR_PATH, "app.log")

# Создание директории, если она не существует
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, encoding="utf-8")
    ]
)
logger = logging.getLogger("openproject_notificator")


app = FastAPI()


@app.post("/webhook")
async def openproject_webhook(request: Request):
    body_json = await request.json()
    if body_json:
        try:
            preparing_data = await open_prj_service.process_webhook_json(body_json)
            if isinstance(preparing_data, dict):
                await send_notifications(bot_obj, preparing_data)
        except Exception as e:
            logger.error("Ошибка при обработке webhook_json: %s; body_json: %s", str(e), body_json)
            # Можно также пробросить ошибку или вернуть корректный ответ FastAPI
            raise
    return {"status": "ok"}


async def start_fastapi():
    config = uvicorn.Config(app, host=config_.HOST, port=int(config_.PORT), log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
