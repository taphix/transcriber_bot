from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from config import TELEGRAM_API_URL, BOT_TOKEN

api_server = TelegramAPIServer.from_base(TELEGRAM_API_URL, is_local=True)

bot = Bot(
    token=BOT_TOKEN,
    parse_mode="HTML",
    session=AiohttpSession(api=api_server),
)
