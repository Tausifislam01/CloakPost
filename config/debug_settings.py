import logging
import os

# Base dir for optional local log file (used only when DEBUG=true)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USE_FILE = os.getenv("DEBUG", "False").lower() == "true"

handlers = {
    "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
}
if USE_FILE:
    handlers["file"] = {
        "class": "logging.FileHandler",
        "filename": os.path.join(BASE_DIR, "debug.log"),
        "formatter": "verbose",
    }

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"}
    },
    "handlers": handlers,
    "loggers": {
        "django": {"handlers": list(handlers.keys()), "level": "INFO"},
        "django.channels": {"handlers": list(handlers.keys()), "level": "DEBUG"},
        "messaging": {"handlers": list(handlers.keys()), "level": "DEBUG"},
    },
}
