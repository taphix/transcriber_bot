import logging

import aiohttp
import json
from aiogram.fsm.context import FSMContext

from config import COZE_TOKEN, COZE_BOT_ID

headers = {
    "Authorization": f"Bearer {COZE_TOKEN}",
    'Content-Type': 'application/json',
    'Connection': 'keep-alive'
}


def get_answer(messages: list):
    for msg in messages:
        if msg['type'] == 'answer':
            return msg['content']
            
    return False


async def new_msg(promt: str, state: FSMContext):
    """
        Создаёт сообщение от пользователя к Coze ИИ
    :param promt: Промт для ИИ
    :param state: FSMContext
    :return: Str ответ ИИ
    """
    async with aiohttp.ClientSession() as session:
        state_data = await state.get_data()
        if not 'chat_history' in state_data.keys():
            state_data['chat_history'] = []

        payload = {
            'bot_id': COZE_BOT_ID,
            'query': promt,
            'user': 'user',
            'chat_history': state_data['chat_history']
        }

        async with session.post(f"https://api.coze.com/open_api/v2/chat",
                                headers=headers,
                                json=payload) as response:
            result = await response.json()

        if not result['msg'] == 'success':
            logging.error(f'new_msg {result}')
            return ''
            
        state_data['chat_history'].append({'role': 'user', 'content': payload['query']})
        state_data['chat_history'].append({'role': 'assistant', 'content': result['messages'][0]['content']})

        await state.update_data(chat_history=state_data['chat_history'])
        return get_answer(result['messages'])
