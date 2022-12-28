from __future__ import absolute_import

from logging import config as Config

from celery import Celery, chord
from celery.signals import setup_logging
from app import flask_app
from config.logger import log_config

chord = chord


# Logging config
@setup_logging.connect
def config_logger(*args, **kwargs):
    Config.dictConfig(log_config)


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL'],
        include=["app.tasks"]
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

flask_app.config.update(
    CELERY_RESULT_BACKEND="redis://localhost:6379/0",
    CELERY_BROKER_URL="redis://localhost:6379/1"
)

celery = make_celery(flask_app)
