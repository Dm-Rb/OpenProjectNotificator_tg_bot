from fastapi import FastAPI, Request
import uvicorn
from config import config_
from service.open_project_service import open_prj_service
from telegram_bot.handlers import send_notifications
from telegram_bot.bot import bot as bot_obj
app = FastAPI()


@app.post("/webhook")
async def openproject_webhook(request: Request):
    body_json = await request.json()
    if body_json:
        preparing_data = open_prj_service.process_webhook_json(body_json)
        await send_notifications(bot_obj, preparing_data)

    return {"status": "ok"}


async def start_fastapi():
    config = uvicorn.Config(app, host=config_.HOST, port=int(config_.PORT), log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
