import logging
import os
from config import config_


"""Настройка логирования"""


# Предполагается, что бот упаковывается в docker. log_file_path - это внешний путь (не в контейнере) по которому
# будет храниться файл с логами app.log. Путь задаётся в файле конфигурации .env в константе DIR_PATH
log_file_path = os.path.join(config_.DIR_PATH, "app.log")
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, encoding="utf-8")
    ]
)
logger = logging.getLogger("openproject_notificator")
