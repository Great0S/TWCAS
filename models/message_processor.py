from config.settings import settings
from app.tele_bot import bot as client

logger = settings.logger
client.start(phone=settings.phone)


