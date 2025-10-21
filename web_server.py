from fastapi import FastAPI, Request
import uvicorn
from config import config_
from service.open_project_service import open_prj_service
from telegram_bot.handlers import send_notifications
from telegram_bot.bot import bot as bot_obj
from logging_config import logger


app = FastAPI()


@app.post("/webhook")
# слушаем host:port/webhook на входящие вебхуки
async def openproject_webhook(request: Request):
    body_json: dict = await request.json()
    if body_json:
        try:
            # передаём сырое содержание вебхука в обработчик
            preparing_data = await open_prj_service.process_webhook_json(body_json)
            if isinstance(preparing_data, dict):
                await send_notifications(bot_obj, preparing_data)
        except Exception as e:
            # Записываем в лог сырой вебхук и имя исключения
            logger.error("Ошибка при обработке webhook_json: %s; body_json: %s", str(e), body_json)
            raise
    return {"status": "ok"}


async def start_fastapi():
    # main функция вебсервера которая импортируется из точки входа (run.py) с запуском программы
    config = uvicorn.Config(app, host=config_.HOST, port=int(config_.PORT), log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
