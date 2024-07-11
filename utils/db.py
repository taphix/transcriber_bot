import logging

import redis.asyncio as redis
from config import DB_HOST, DB_NAME, DB_PORT, DB_PASSWORD, DB_USER


class Redis:
    def __init__(self):
        try:
            self.conn = redis.Redis(
                host=DB_HOST,
                port=DB_PORT,
                db=DB_NAME,
                password=DB_PASSWORD,
            )
        except Exception as e:
            logging.error(f'Не могу подключиться к Redis', e)

    async def update(self, key: str | int, value) -> str | int:
        return await self.conn.set(name=key, value=value)

    async def get(self, key: str | int) -> bytes:
        return await self.conn.get(name=str(key))

    async def close(self) -> bool:
        try:
            await self.conn.close()
            return True
        except Exception as e:
            logging.error('Ошибка при закрытии подключения Redis', e)
            return False
