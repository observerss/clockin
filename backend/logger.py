from loguru import logger

import os

log_path = os.path.join(os.path.dirname(__file__), "..", "logs", "clockin.log")

logger.add(log_path, rotation="1 day", retention="30 days")
