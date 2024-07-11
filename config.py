from os import getenv
from aiogram.types import BotCommand
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = getenv('BOT_TOKEN')
TELEGRAM_API_URL = getenv('TELEGRAM_API_URL')

COZE_TOKEN = getenv('COZE_TOKEN')
COZE_BOT_ID = getenv('COZE_BOT_ID')

YANDEX_OAUTH = getenv('YANDEX_OAUTH')
YANDEX_CLOUD_ID = getenv('YANDEX_CLOUD_ID')
YANDEX_SERVICE_ACCOUNT_FOLDER_NAME = getenv('YANDEX_SERVICE_ACCOUNT_FOLDER_NAME')
YANDEX_BUCKET_FOLDER_NAME = getenv('YANDEX_BUCKET_FOLDER_NAME')
YANDEX_SERVICE_ACCOUNT_NAME = getenv('YANDEX_SERVICE_ACCOUNT_NAME')
YANDEX_BUCKET_NAME = getenv('YANDEX_BUCKET_NAME')
YANDEX_SERVICE_ACCOUNT_ID = getenv('YANDEX_SERVICE_ACCOUNT_ID')

DB_NAME = int(getenv('DB_NAME'))
DB_HOST = getenv('DB_HOST')
DB_PORT = int(getenv('DB_PORT'))
DB_PASSWORD = getenv('DB_PASSWORD')
DB_USER = getenv('DB_USER')

menu_commands = [
    BotCommand(
        command='start',
        description='Старт'
    )
]
