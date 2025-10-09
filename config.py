import os
from dotenv import load_dotenv


# загружаем переменные окружения из .env
load_dotenv()


class Config:
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    HOST = os.getenv("SERVER_HOST")
    PORT = os.getenv("SERVER_PORT")
    DOMAIN = os.getenv("OPENPROJECT_DOMAIN")
    USER_API_KEY = os.getenv("OPENPROJECT_USER_API_KEY")

config_ = Config()
