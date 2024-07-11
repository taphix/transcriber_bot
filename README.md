## Бот транскрибатор

### Конфигурация .env

```
BOT_TOKEN - Токен бота
TELEGRAM_API_URL - url с которого получаются новые обновления

COZE_TOKEN- Токен coze
COZE_BOT_ID - ID вашего coze ии

YANDEX_OAUTH - oauth токен яндекс облака
YANDEX_CLOUD_ID - id яндекс облака
YANDEX_SERVICE_ACCOUNT_ID - ID сервисного аккаунта. Оставить пустым что бы создать новый аккаунт
YANDEX_SERVICE_ACCOUNT_FOLDER_NAME - Имя папки с сервис аккаунтом в облаке
YANDEX_BUCKET_FOLDER_NAME - Имя папки с бакетом в облаке
YANDEX_SERVICE_ACCOUNT_NAME - Имя сервис аккаунта
YANDEX_BUCKET_NAME - Имя бакета

DB_NAME - Имя бд
DB_HOST - Хост бд
DB_PORT - Порт бд
DB_PASSWORD - Пароль от бд
DB_USER - Пользовтаель бд

TELEGRAM_API_ID - ID приложения телеграм
TELEGRAM_API_HASH - Api hash приложения телеграм
TELEGRAM_LOCAL - true для работы Local Telegram API локально
```

### Важно

```
Перед началом настройки проекта, опубликуйте (Publish) вашего бота в Coze с настройкой "Bot as API" (находится в самом низу), если вы этого ещё не сделали
```
```
Так же если приложение при запуске не находит в облаке папки с именем YANDEX_SERVICE_ACCOUNT_FOLDER_NAME из env, то начинает создавать все необходимые для работы компоненты.
```

### Получаем COZE_TOKEN и COZE_BOT_ID

```bash
# Для COZE_TOKEN

Заходим на https://www.coze.com/open/api
Нажимаем Add new token
Задаём любое имя
Задаём любое время жизни (желательно Permanent)
Задаём любое рабочее пространство
Важно! Permission задаём Bot и chat

Нажимаем Confirm и сохраняем токен
```

```bash
# Для COZE_BOT_ID

На главной странице нажимаем Personal и выбираем нужного нам бота
Выделяем последние цифры адреса открывшейся страницы от начала последнего '/', это и будет ID бота.

Например:

https://www.coze.com/space/111111111111111/bot/2222222222222222

'2222222222222222' - ID бота
```

### Получаем данные Yandex Cloud
```
1. На https://yandex.cloud/ru/docs/iam/operations/iam-token/create получите oauth токен.
2. В панели управления скопируйте ID вашего облака.
```

### Получаем данные telegram api
```
1. На https://my.telegram.org/auth получите api hash и api id.
```