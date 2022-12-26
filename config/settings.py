from configparser import ConfigParser as config
from pydantic import BaseSettings

class Settings(BaseSettings):

    # Telegram API Config
    api_id: int = 7148663
    api_hash: str = '81c16de88cd5e25fcbf01e5af332b41f'

    # Telegram BOT info
    username: str = 'albeyanfashion2'
    phone: int = 905434050709
    token: str = '5754073767:AAE3IbbE7-zXKGMg1fqunFxsUOg5K-kH6GI'
    channel_id: str = '@BeyanStorebot'
    session_name: str = 'tele_bot'

    # Telegram Channels info
    women_ids = [-1001411372097, -1001188747858, -1001147535835, -1001237631051, -1001653408221]


    # Server Config
    Target: str = 'https://5121-213-254-138-110.eu.ngrok.io'

    # Ecwid info    
    category_id: int = 127443592

    logs_dir: str = 'logs/'

    class Config:
        case_sensitive = True


settings = Settings()