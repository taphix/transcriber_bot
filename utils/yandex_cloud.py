import asyncio
import json
import logging
import time

import aiohttp
import jwt

import config
from config import YANDEX_CLOUD_ID, YANDEX_OAUTH, YANDEX_SERVICE_ACCOUNT_FOLDER_NAME, YANDEX_SERVICE_ACCOUNT_NAME, \
    YANDEX_BUCKET_NAME, YANDEX_BUCKET_FOLDER_NAME
from utils.db import Redis


class Updater:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.url = 'https://iam.api.cloud.yandex.net/iam/v1/tokens'

    async def start(self) -> None:
        """
            Обновляет токены IAM
        :return:
        """
        redis = Redis()
        try:
            # Обновление iam токена облака
            iam_token = await self.update_iam_token()
            await redis.update(key='iam_token', value=iam_token)

            # Обновление iam токена сервисного аккаунта
            structure = CreateStructure(iam_token=iam_token, session=self.session)
            service_account_id = await redis.get(key='service_account_id')
            service_account_id = service_account_id.decode('utf-8')
            encoded_token = await structure.create_encode_jwt_token(
                service_account_id=service_account_id)
            logging.info(f'ID СЕРВИСНОГО АККАУНТА {service_account_id}')
            config.YANDEX_SERVICE_ACCOUNT_ID = service_account_id

            service_account_iam_token = await self.update_service_account_iam_token(
                encoded_token=encoded_token
            )
            await redis.update(key='service_account_iam_token', value=service_account_iam_token)

        except Exception as e:
            logging.error(f'Ошибка при обновлении токенов IAM: {e}')

        await redis.close()
        await asyncio.sleep(60)

    async def update_iam_token(self) -> str:
        """
            Обновляет iam токен аккаунта
        :return: Возвращает iam токен
        """
        payload = {"yandexPassportOauthToken": YANDEX_OAUTH}
        async with self.session.post(url=self.url, json=payload) as response:
            result = await response.json()
            return result['iamToken']

    async def update_service_account_iam_token(self, encoded_token: str) -> str:
        """
            Обновляет iam токен сервисного аккаунта
        :param encoded_token: JWT декодированный ключ
        :return: Возвращает iam токен сервисного аккаунта
        """
        if not encoded_token:
            logging.error('Не могу получить iam токен сервисного аккаунта. Не указан декодированный JWT токен.')
            raise ValueError

        headers = {'Content-Type': 'application/json'}
        payload = {"jwt": encoded_token}
        async with self.session.post(url=self.url, headers=headers, json=payload) as response:
            result = await response.json()
            return result['iamToken']

    async def close(self) -> None:
        """
            Закрывает подключение
        :return:
        """
        await self.session.close()


class CreateStructure:
    """
        Класс для создания нужной структуры и данных в облаке Яндекса
    """

    def __init__(self, iam_token: str, session: aiohttp.ClientSession):
        """
        :param iam_token: IAM токен облака
        """
        self.session = session
        self.iam_token = iam_token
        self.headers = {
            'Authorization': f'Bearer {iam_token}',
            'Content-Type': 'application/json'
        }

    async def start(self) -> None:
        """
            Запустить процесс создания нужной структуры в облаке если её нет и сохраняет полученные данные в редис.
            После выполнения закрывает свою сессию aiohttp сам.
        :return:
        """
        if not await self.need_structure_creating():
            return

        redis = Redis()

        # Создаём папку для проекта
        service_account_folder_id, bucket_folder_id = await self.create_folders()

        # Создаём сервис аккаунт
        service_account_id = await self.create_service_account(
            service_account_folder_id=service_account_folder_id
        )
        logging.info(f'ID сервисного аккаунта, {service_account_id}')
        await redis.update(key='service_account_id', value=service_account_id)

        # Выдаём ему права
        rights = await self.give_rights(
            service_account_folder_id=service_account_folder_id,
            service_account_id=service_account_id
        )

        # Декодируем jwt токен для получения iam сервис аккаунта
        encode_jwt_token = await self.create_encode_jwt_token(
            service_account_id=service_account_id
        )
        await redis.update(key='encode_jwt', value=encode_jwt_token)

        # Получаем iam токен сервис аккаунта
        async with aiohttp.ClientSession() as session:
            updater = Updater(session=session)
            service_account_iam = await updater.update_service_account_iam_token(
                encoded_token=encode_jwt_token
            )
        await redis.update(key='service_account_iam', value=service_account_iam)

        # Создаём внутри папки проекта хранилище для файлов
        bucket_id = await self.create_bucket(
            bucket_folder_id=bucket_folder_id
        )

        await redis.close()

    async def need_structure_creating(self) -> bool:
        """
            Если в облаке нет папки с нужным названием, то считается, что нужно создать структуру
        :return: True если нужно
        """
        url = 'https://resource-manager.api.cloud.yandex.net/resource-manager/v1/folders'
        payload = {"cloudId": YANDEX_CLOUD_ID}
        async with self.session.get(url=url, json=payload, headers=self.headers) as response:
            result = await response.json()
            logging.info(f'need_structure_creating {result}' )
            if YANDEX_SERVICE_ACCOUNT_FOLDER_NAME not in [folder_item['name'] for folder_item in result['folders']]:
                return True
            return False

    async def create_folders(self) -> tuple[str, str]:
        """
            Создаёт папку бота в облаке
        :return: ID созданной папки
        """
        url = 'https://resource-manager.api.cloud.yandex.net/resource-manager/v1/folders'
        payload = {
            'cloudId': YANDEX_CLOUD_ID,
            'name': YANDEX_SERVICE_ACCOUNT_FOLDER_NAME,
            'description': 'Папка сервисного аккаунта для телеграм бота, который переводит аудиофайлы в текст.'
        }
        async with self.session.post(url=url, json=payload, headers=self.headers) as response:
            service_account_result = await response.json()

        payload = {
            'cloudId': YANDEX_CLOUD_ID,
            'name': YANDEX_BUCKET_FOLDER_NAME,
            'description': 'Папка для хранения файлов телеграм бота, который переводит аудиофайлы в текст.'
        }
        async with self.session.post(url=url, json=payload, headers=self.headers) as response:
            bucket_result = await response.json()
            logging.info(f'create_folders {service_account_result, bucket_result}')

        return service_account_result['metadata']['folderId'], bucket_result['metadata']['folderId']

    async def create_service_account(self, service_account_folder_id: str) -> str:
        """
            Создаёт сервисный аккаунт внутри папки бота и даёт ему права
        :param service_account_folder_id: ID папки где лежит сервис аккаунт
        :return: ID сервис аккаунта
        """
        # Создание аккаунта
        url = 'https://iam.api.cloud.yandex.net/iam/v1/serviceAccounts'
        payload = {
            'folderId': service_account_folder_id,
            'name': YANDEX_SERVICE_ACCOUNT_NAME,
            'description': 'Сервисный аккаунт для телеграм бота, который переводит аудиофайлы в текст.'
        }
        async with self.session.post(url=url, headers=self.headers, json=payload) as response:
            service_account_result = await response.json()
            logging.info(f'create_service_account {service_account_result}')
        return service_account_result['metadata']['serviceAccountId']

    async def give_rights(self, service_account_folder_id: str, service_account_id: str) -> bool:
        """
            Выдаёт права сервисному аккаунту
        :param service_account_folder_id: ID папки где лежит сервис аккаунт
        :return: ID сервис аккаунта
        """
        url = (f'https://resource-manager.api.cloud.yandex.net/resource-manager/v1/folders/'
               f'{service_account_folder_id}:updateAccessBindings')
        payload = {
            "accessBindingDeltas": [{
                "action": "ADD",
                "accessBinding": {
                    "roleId": "editor",
                    "subject": {
                        "id": service_account_id,
                        "type": "serviceAccount"
                    }
                }
            }]
        }
        async with self.session.post(url=url, headers=self.headers, json=payload):
            pass

        for role_id in ['ai.speechkit-stt.user', 'storage.uploader']:
            url = f'https://iam.api.cloud.yandex.net/iam/v1/serviceAccounts/{service_account_id}:updateAccessBindings'
            payload = {
                "accessBindingDeltas": [
                    {
                        "action": "ADD",
                        "accessBinding": {
                            "roleId": role_id,
                            "subject": {
                                "id": "allUsers",
                                "type": "serviceAccount"
                            }
                        }
                    }
                ]
            }
            async with self.session.post(url=url, headers=self.headers, json=payload):
                pass
        return True

    async def create_encode_jwt_token(self, service_account_id: str) -> str:
        """
            Получение токена IAM через JWT ключи
        :param service_account_id: Id сервис аккаунта
        :return: encode_token, iam_key
        """
        # создание ключей
        url = 'https://iam.api.cloud.yandex.net/iam/v1/keys'
        payload = {'serviceAccountId': service_account_id}
        async with self.session.post(url=url, headers=self.headers, json=payload) as response:
            result = await response.json()

        with open('data/keys.json', 'w') as keys_file:
            keys_file.write(json.dumps(result))

        private_key = result['privateKey']
        key_id = result['key']['id']

        now = int(time.time())
        payload = {
            'aud': 'https://iam.api.cloud.yandex.net/iam/v1/tokens',
            'iss': service_account_id,
            'iat': now,
            'exp': now + 3600
        }
        encoded_token = jwt.encode(
            payload=payload,
            key=private_key,
            algorithm='PS256',
            headers={'kid': key_id}
        )
        logging.info(f'encoded_token {encoded_token}')
        return encoded_token

    async def create_bucket(self, bucket_folder_id: str) -> str:
        """
            Создаёт новый объект Bucket
        :param bucket_folder_id: ID папки где будет лежать хранилище
        :return: ID bucket
        """
        url = 'https://storage.api.cloud.yandex.net/storage/v1/buckets'
        payload = {
            "name": YANDEX_BUCKET_NAME,
            "folderId": bucket_folder_id,
            "acl": {
                "grants": [
                    {
                        "permission": "PERMISSION_FULL_CONTROL",
                        "grantType": "GRANT_TYPE_ALL_USERS"
                    }
                ]
            }
        }

        async with self.session.post(url=url, json=payload, headers=self.headers) as response:
            result = await response.json()
            logging.info(f'create_bucket {result}')
            return result['id']


class Storage:
    def __init__(self, iam_token: str, session: aiohttp.ClientSession):
        """
        :param iam_token: IAM токен облака
        :param session: aiohttp сессия
        """
        self.session = session
        self.iam_token = iam_token
        self.headers = {
            'Authorization': f'Bearer {iam_token}'
        }

    async def upload(self, file_path: str, object_name: str) -> str:
        """
            Загружает файл в BaseStorage облака
        :param file_path: Путь до файла
        :param object_name: Имя файла на облаке
        :return: uri файла
        """
        try:
            url = f'https://storage.yandexcloud.net/{YANDEX_BUCKET_NAME}/{object_name}'
            with open(file_path, 'rb') as file_data:
                async with self.session.put(url=url, data=file_data, headers=self.headers) as response:
                    if not response.status == 200:
                        logging.error(f'Ошибка при загрузке файла в bucket {await response.text()}')
                        return ''
                    return url
        except Exception as e:
            logging.error(f'Ошибка при загрузке файла в bucket {e}')
            return ''

    async def remove(self, object_name: str) -> bool:
        """
            Удаляет файл из BaseStorage облака
        :param object_name: Имя файла на облаке
        :return: true или false
        """
        try:
            url = f'https://storage.yandexcloud.net/{YANDEX_BUCKET_NAME}/{object_name}'
            async with self.session.put(url=url, headers=self.headers) as response:
                if not response.status == 200:
                    logging.error(f'Ошибка при удалении файла из bucket {await response.text()}')
                    return False
                return True
        except Exception as e:
            logging.error(f'Ошибка при удалении файла из bucket {e}')
            return False

    # async def get(self, object_name: str) -> str:
    #     """
    #         Получает файл из BaseStorage облака
    #     :param object_name: Имя файла на облаке
    #     :return: Данные файла
    #     """
    #     try:
    #         url = f'https://storage.yandexcloud.net/{YANDEX_BUCKET_NAME}/{object_name}'
    #         async with self.session.get(url=url, headers=self.headers) as response:
    #             if not response.status == 200:
    #                 logging.error(f'Ошибка при получении файла из bucket {await response.text()}')
    #                 return False
    #             return await response.text()
    #     except Exception as e:
    #         logging.error(f'Ошибка при получении файла из bucket {e}')
    #         return {}

