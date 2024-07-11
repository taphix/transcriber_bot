import asyncio
import logging

import aiohttp


from utils.db import Redis
from utils.yandex_cloud import Storage


async def translate(object_name: str, bucket_name: str) -> dict:
    """
        переводит звуковой файл в текст
    :param object_name: Имя файла на облаке
    :param bucket_name: Имя bucket где хранится файл
    :return: Речь текстом
    """
    async with aiohttp.ClientSession() as session:
        redis = Redis()
        service_account_iam_token = await redis.get(key='service_account_iam_token')
        file_url = f'https://{bucket_name}.storage.yandexcloud.net/{object_name}'
        url = 'https://transcribe.api.cloud.yandex.net/speech/stt/v2/longRunningRecognize'
        request_body = {
            "config": {
                "specification": {
                    "audioEncoding": 'MP3',
                    "languageCode": 'auto'
                }
            },
            "audio": {
                "uri": file_url
            }
        }
        headers = {
            'Authorization': f'Bearer {service_account_iam_token.decode("utf8")}',
            'Content-Type': 'application/json'
        }
        try:
            async with session.post(url=url, json=request_body, headers=headers) as response:
                if response.status == 404:
                    logging.error(f'Ошибка при переводе {request_body}')
                    return {'success': False, 'msg': f'Ошибка в запросе на перевод.'}
                result = await response.json()

            while True:
                await asyncio.sleep(3)
                url = f'https://operation.api.cloud.yandex.net/operations/{result["id"]}'
                async with session.get(url=url, headers=headers) as response:
                    result = await response.json()
                    if not result.get('done'):
                        continue

                    if not result['response'].get('chunks'):
                        return {'success': False, 'msg': f'В {object_name} нет речи.'}
                    all_text = ''
                    for chunk in result['response']['chunks']:
                        all_text += chunk['alternatives'][0]['text'] + ' '

                    return {'success': True, 'msg': all_text}

        except Exception as e:
            logging.error(f'Ошибка при переводе {e}')
            return {'success': False, 'msg': f'Ошибка при переводе {e}'}

        finally:
            iam_token = await redis.get(key='iam_token')
            await redis.close()
            storage = Storage(session=session, iam_token=iam_token.decode("utf8"))
            await storage.remove(object_name=object_name)
