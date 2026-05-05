from fastapi import FastAPI, Request
import uvicorn
from config import config_
from service.open_project_service import open_prj_service
from telegram_bot.handlers import send_notifications
from telegram_bot.bot import bot as bot_obj
from logging_config import logger


app = FastAPI()


@app.post("/webhook")
# Listening to https://yout_host:port/webhook and receiving webhooks from your "Open Project"
async def openproject_webhook(request: Request):
    body_json: dict = await request.json()
    if body_json:
        try:
            # Passing the raw webhook content to the handler
            prepared_data = await open_prj_service.processing_webhook_json(body_json)
            if isinstance(prepared_data, dict):
                # Sending the prepared data to the Telegram bot for distribution to users
                await send_notifications(bot_obj, prepared_data)
        except Exception as e:
            logger.error("Error processing 'webhook_json': %s; body_json: %s", str(e), body_json)
    return {"status": "ok"}


async def start_fastapi():
    # Main function to start the web server that is imported from the entry point (run.py)
    config = uvicorn.Config(app, host=config_.HOST, port=int(config_.PORT), log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
