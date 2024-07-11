import asyncio
import logging
import sys

import aiohttp
from aiogram import Dispatcher
from aiogram.types import Update

from config import TELEGRAM_API_URL, BOT_TOKEN, YANDEX_SERVICE_ACCOUNT_ID
from core import bot
from handlers import routers
from utils.db import Redis
from utils.defs import update_iam_every_hour
from utils.yandex_cloud import CreateStructure, Updater

dp = Dispatcher()
dp.include_routers(*routers)


async def polling():
    logging.info('Начались запросы к локальному серверу Telegram API')
    url = f"{TELEGRAM_API_URL}/bot{BOT_TOKEN}/getUpdates"
    offset = None

    try:
        session = aiohttp.ClientSession()
        while True:
            try:
                payload = {"offset": offset, "timeout": 60}
                async with session.get(url=url, json=payload) as response:
                    response.raise_for_status()
                    data = await response.json()

                if data.get('ok'):
                    for update in data["result"]:
                        offset = update["update_id"] + 1
                        update_obj = Update(**update)
                        await dp.feed_update(bot, update_obj)
            except Exception as e:
                logging.error(f"Ошибка при полинге к локальному серверу: {e}", e)
                await asyncio.sleep(5)
    finally:
        logging.error(f"Всё")


async def start():
    """
        Запускает бота
    :return:
    """
    async with aiohttp.ClientSession() as session:
        if not YANDEX_SERVICE_ACCOUNT_ID:
            updater = Updater(session=session)
            iam_token = await updater.update_iam_token()
            structure_of_app = CreateStructure(
                session=session,
                iam_token=iam_token
            )
            await structure_of_app.start()

    redis = Redis()
    await redis.update(
        key='service_account_id',
        value=YANDEX_SERVICE_ACCOUNT_ID
    )
    await redis.close()

    updater_task = asyncio.create_task(update_iam_every_hour())
    logging.info('Обновляю AIM ключи.')
    await asyncio.sleep(5)

    await bot.delete_webhook()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(start())
