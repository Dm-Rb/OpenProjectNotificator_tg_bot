import os
from dotenv import load_dotenv


"""Load environment variables from .env"""


load_dotenv()


class Config:
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    HOST = os.getenv("SERVER_HOST")
    PORT = os.getenv("SERVER_PORT")
    DOMAIN = os.getenv("OPENPROJECT_DOMAIN")
    USER_API_KEY = os.getenv("OPENPROJECT_USER_API_KEY")
    DIR_PATH = os.getenv("DIR_PATH")


config_ = Config()
