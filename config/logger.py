


log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "celeryTask": {
            "()": "celery.app.log.TaskFormatter",
            "fmt": "[%(asctime)s: {} %(levelname)s %(message)s] ",
        },
        'default': {
            'format': '[%(asctime)s:%(levelname)s:%(name)s:%(threadName)s] %(message)s',
        },
        'base': {
            'format': '%(message)s'
        }
    },
    "handlers": {
        "console": {
            "class": "rich.logging.RichHandler",
            "formatter": "base",
            "level": "INFO",
        },
        "file": {
            "formatter": "default",
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "mode": "a",
            "encoding": "utf-8",
            "filename": f"logs/{__name__}.log",
            'maxBytes': 5000000,
            'backupCount': 30
        }
    },
    "loggers": {
        "mainLog": {
            "handlers": ["file"],
            "level": "INFO",
        }
    },
    'root': {
        'handlers': ["console"],
        'level': 'DEBUG',
    },
}
