import logging
import os
from config import config_


"""Logging configuration"""


# It is assumed that the bot is packaged in Docker. log_file_path is the external path (not in the container)
# where the app.log file will be stored. The path is specified in the .env configuration file in the DIR_PATH constant
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
