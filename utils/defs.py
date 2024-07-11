import asyncio
from datetime import datetime

import aiohttp

from utils.yandex_cloud import Updater


async def update_iam_every_hour(update=True) -> None:
    """
        Обновляет iam токены каждый час
    :param update: Если True, тогда при первом запуске функции она сразу обновит токен
    :return:
    """
    while True:
        now = datetime.now()
        if now.minute == 0 or update:
            async with aiohttp.ClientSession() as session:
                updater = Updater(session=session)
                await updater.start()
                update = False
        await asyncio.sleep(60)