"""Импортируем дополнительные библиотеки."""
import json
import logging
import os
import requests
import sys
import time

import exceptions

from datetime import datetime
from dotenv import load_dotenv
from telegram import Bot
from http import HTTPStatus

load_dotenv()

# Переменные окружения
PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_TIME = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}

VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}

# Начало настройки логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

FORMAT = "%(asctime)s [%(levelname)s] - %(message)s"
formatter = logging.Formatter(FORMAT)

handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)

logger.addHandler(handler)
# Конец настройки логирования


def send_message(bot: Bot, message: str) -> bool:
    """Бот отправляет сообщение."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logger.error(f"Ошибка при отправке сообшения: {error}")
    else:
        return True


def get_api_answer(current_timestamp: int) -> dict:
    """Делаем запрос к эндпоинту API-сервиса."""
    params = {"from_date": current_timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        logging.error(f"Ошибка при запросе к основному API: {error}")
    if response.status_code != HTTPStatus.OK:
        raise exceptions.EndpointResponseError(response.status_code)
    try:
        response = response.json()
    except json.decoder.JSONDecodeError:
        logging.error("Ошибка в преобразовании ответа из JSON в Python")
    return response


def check_response(response: dict) -> list:
    """Проверяем API на корректность."""
    if not isinstance(response, dict):
        raise TypeError("В response отсутствует словарь")
    if "homeworks" not in response:
        raise KeyError("Ключа homeworks нет в response")
    homeworks = response.get("homeworks")
    if not isinstance(homeworks, list):
        raise TypeError("Ключ homeworks не сожедржит списка")
    return homeworks


def parse_status(homework: dict) -> str:
    """Проверяет статус проверки домшней работы."""
    homework_keys = ["homework_name", "status"]
    for key in homework_keys:
        if key not in homework:
            raise KeyError(f"Ключа {key} нет в словаре homework")
    homework_name = homework.get(homework_keys[0])
    homework_status = homework.get(homework_keys[1])

    if homework_status not in VERDICTS:
        raise ValueError(
            f"Статус {homework_status} не соответствует ожидаемому"
        )

    verdict = VERDICTS[homework_status]
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
        raise ValueError("Проверьте доступность переменных окружения")

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    except_message_status = None
    status = None

    while check:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get("current_date")
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                if message != status:
                    status = message
                    flag = send_message(bot, message)
                    if flag:
                        logger.info(f"Бот отправил сообщение {message}")
                else:
                    message = "Статус дз не изменился"
            else:
                ts = datetime.utcfromtimestamp(current_timestamp).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                message = (
                    f"Начиная с {ts} работ находящихся на проверке не "
                    "обнаружено."
                )
        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logger.error(message)
            if message != except_message_status:
                flag = send_message(bot, message)
                if flag:
                    except_message_status = message
                    logger.info(f"Бот отправил сообщение {message}")
            time.sleep(RETRY_TIME)
        else:
            logger.info(message)
            time.sleep(RETRY_TIME)


if __name__ == "__main__":
    main()
