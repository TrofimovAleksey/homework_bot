"""Здесь будет докстринг."""
import logging
import os
import requests
import sys
import time

import exceptions

from datetime import datetime
from telegram import Bot
from dotenv import load_dotenv
from http import HTTPStatus

load_dotenv()

# Переменные окружения
PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_TIME = 1
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}

HOMEWORK_STATUSES = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}

# Статус д.з. храним глобально
STATUS = None

# Статус отправленного исключения
EXCEPT_MESSAGE_STATUS = None

# Начало настройки логгирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

FORMAT = "%(asctime)s [%(levelname)s] - %(message)s"
formatter = logging.Formatter(FORMAT)

handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)

logger.addHandler(handler)
# Конец настройки логгирования


def send_message(bot, message):
    """Бот отправляет сообщение."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logger.error(f"Ошибка при отправке сообшения: {error}")
    else:
        logger.info(f"Бот отправил сообщение {message}")


def get_api_answer(current_timestamp: int) -> dict:
    """Делаем запрос к эндпоинту API-сервиса."""
    params = {"from_date": current_timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        logging.error(f"Ошибка при запросе к основному API: {error}")
    if response.status_code != HTTPStatus.OK:
        raise exceptions.EndpointResponseError(response.status_code)
    return response.json()


def check_response(response):
    """Проверяем API на корректность."""
    if "homeworks" in response:
        return response.get("homeworks")
    return "Список пуст"


def parse_status(homework):
    """Проверяет статус проверки домшней работы."""
    global STATUS
    homework_name = homework.get("homework_name")
    homework_status = homework.get("status")
    if homework_status == STATUS:
        return "Не изменился"
    STATUS = homework_status
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверяет доступность переменных окружения."""
    env_variables = {
        "PRACTICUM_TOKEN": PRACTICUM_TOKEN,
        "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
    }
    for variable in env_variables:
        if not env_variables[variable]:
            logger.critical(
                f"Отсутствует обязательная переменная окружения: '{variable}' "
                "Программа принудительно остановлена."
            )
            return False
    return True


def main() -> None:
    """Основная логика работы бота."""
    check = check_tokens()

    if not check:
        sys.exit()

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0

    while check:
        try:
            response = get_api_answer(current_timestamp)
            # сurrent_timestamp = response.get("current_date")
            homeworks = check_response(response)
            if len(homeworks) == 0:
                dt = datetime.utcfromtimestamp(current_timestamp).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                message = f"Начиная с {dt}, новых работ нет."
                send_message(bot, message)
            else:
                message = parse_status(homeworks[0])
                if message != "Не изменился":
                    send_message(bot, message)
                time.sleep(RETRY_TIME)
        # except exceptions.EndpointResponseError as error:
        #     logger.error(error)
        except Exception as error:
            global EXCEPT_MESSAGE_STATUS
            message = f"Сбой в работе программы: {error}"
            logger.error(message)
            if message != EXCEPT_MESSAGE_STATUS:
                send_message(bot, message)
                EXCEPT_MESSAGE_STATUS = message
            time.sleep(RETRY_TIME)
        else:
            pass


if __name__ == "__main__":
    main()
