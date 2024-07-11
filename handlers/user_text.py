import asyncio
import logging
import os
import random
import string

import aiohttp
from aiogram import Router, F
from aiogram.enums.chat_action import ChatAction
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile
from pydub import AudioSegment

from config import YANDEX_BUCKET_NAME
from core import bot
from utils import coze_api
from utils.db import Redis
from utils.voice_to_text import translate
from utils.yandex_cloud import Storage

router = Router()


@router.message(F.text)
async def text_handler(msg: Message) -> None:
    """
        Ловит все сообщения
    :param msg: Message
    :return:
    """
    await msg.answer('Отправьте ваш аудиофайл, пожалуйста:')


@router.message(F.content_type.in_({'voice', 'audio'}))
async def file_handler(msg: Message, state: FSMContext) -> None:
    """
        Ловит все аудиофайлы
    :param msg: Message
    :param state: FSMContext
    :return:
    """
    chat_action_task = asyncio.create_task(
        send_chat_action(chat_id=msg.from_user.id)
    )
    if msg.voice:
        file_name = f'voice-message-{msg.message_id}.oga'
        file_id = msg.voice.file_id
        folder = 'voice'
    else:
        file_name = msg.audio.file_name
        file_id = msg.audio.file_id
        folder = 'music'

    wait_msg = await msg.answer(f'1️⃣ Начинаю обработку файла {file_name}')
    # msg_animation_task = asyncio.create_task(
    #     msg_animation(msg=wait_msg)
    # )
    file_info = await bot.get_file(
        file_id=file_id
    )

    object_name = ''.join(random.choice(string.ascii_lowercase) for _ in range(5))
    name, file_extension = os.path.splitext(file_name)
    object_name += file_extension

    server_destination = f'telegram-data/{bot.token}/{folder}/{file_info.file_path.split("/")[-1]}'
    mp3_destination = f'data/{name}.mp3'

    sound = AudioSegment.from_file(server_destination)
    sound.export(mp3_destination, format="mp3")

    async with aiohttp.ClientSession() as session:
        redis = Redis()
        iam_token = await redis.get(key='iam_token')
        await redis.close()
        storage = Storage(
            session=session,
            iam_token=iam_token.decode("utf8")
        )
        await storage.upload(
            file_path=mp3_destination,
            object_name=object_name
        )

    translated_text = await translate(
        object_name=object_name,
        bucket_name=YANDEX_BUCKET_NAME
    )

    os.remove(server_destination)
    os.remove(mp3_destination)

    # msg_animation_task.cancel()
    if not translated_text.get('success'):
        await wait_msg.answer('❌ Ошибка обработки файлы, попробуйте снова')
        return

    # await wait_msg.edit_text('2️⃣ Транскрибация прошла успешно, начинаю обработку через ИИ')
    # msg_animation_task = asyncio.create_task(
    #     msg_animation(msg=wait_msg)
    # )
    # ai_answer = await coze_api.new_msg(
    #     promt=translated_text['msg'],
    #     state=state
    # )

    # msg_animation_task.cancel()
    chat_action_task.cancel()
    await wait_msg.delete()

    if translated_text['msg']:
        file = f'{name}.txt'

        with open(file=file, mode='w') as f:
            f.write(translated_text['msg'])

        await msg.answer('3️⃣ Результат обработки:')
        await msg.answer_document(
            document=FSInputFile(file)
        )
        os.remove(file)
        # for text_part in [translated_text['msg'][i:i + 4096] for i in range(0, len(translated_text['msg']), 4096)]:
        #     await msg.answer(text_part)

    else:
        await msg.answer('❌ Ошибка обработки файлы, попробуйте снова')


async def msg_animation(msg: Message) -> None:
    """
        Делает анимацию трёх точек в конце сообщения
    :param msg: Message
    :return:
    """
    points = ''
    while True:
        if len(points) > 3:
            points = ''
        points += '.'

        await msg.edit_text(msg.text + points)
        await asyncio.sleep(1)


async def send_chat_action(chat_id: int | str) -> None:
    """
        Бесконечно отправляет действие чата "UPLOAD_DOCUMENT"
    :param chat_id: ID чата
    :return:
    """
    while True:
        await bot.send_chat_action(chat_id, ChatAction.TYPING)
        await asyncio.sleep(5)
