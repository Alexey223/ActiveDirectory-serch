import logging
import json
import os
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "activity.log")

os.makedirs(LOG_DIR, exist_ok=True)

class JsonFormatter(logging.Formatter):
    def format(self, record): 
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user": getattr(record, "user", "local_user"),
            "action": getattr(record, "action", "unknown"),
            "object": getattr(record, "object", "unknown"),
            "status": getattr(record, "status", "success"),
            "message": record.getMessage(),
        })

# File Handler
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(JsonFormatter())

# Console Handler
console_handler = logging.StreamHandler()
console_formatter = logging.Formatter("[%(asctime)s] |%(levelname)8s| |%(action)10s| %(message)s")
console_handler.setFormatter(console_formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def log_info(action: str, obj: str, message: str, status: str = "success", user: str = "local_user"):
    extra = {"action": action, "object": obj, "status": status, "user": user}
    logger.info(message, extra=extra)

def log_error(action: str, obj: str, message: str, status: str = "failure", user: str = "local_user"):
    extra = {"action": action, "object": obj, "status": status, "user": user}
    logger.error(message, extra=extra)

# Пример логов
if __name__ == "__main__":
    log_info("connect", "ldap", "Successfully connected to domain controller", status="success")
    log_error("addtogroup", "John Doe", "Group not found", status="failure") 