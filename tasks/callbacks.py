from app.celery_server import celery
from config.settings import settings

logger = settings.logger

@celery.task()
def mediaCallback(*args):
    logger.info(f'Result: {args[0]}')
    return args[0]


@celery.task()
def NewProductCallback(*args):
    logger.info(f'Results count: {len(args)}')
    return args[0][0]


@celery.task()
def dummy(self, *args, **kwargs):
    pass
