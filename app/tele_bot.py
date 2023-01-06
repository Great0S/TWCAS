from telethon.sync import TelegramClient
from config.settings import settings


bot = TelegramClient(session=settings.session_name,
                     api_id=settings.api_id,
                     api_hash=settings.api_hash,
                     sequential_updates=True)

alert_bot = TelegramClient(session=settings.alert_session,
                     api_id=settings.alert_api_id,
                     api_hash=settings.alert_api_hash)