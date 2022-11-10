"""Здесь будет докстринг."""
import logging

import os
import time

import requests

from datetime import datetime

from telegram import Bot

from dotenv import load_dotenv

load_dotenv()


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

STATUS = None

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def send_message(bot, message):
    """Здесь будет докстринг."""
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp):
    """Здесь будет докстринг."""
    params = {"from_date": current_timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    return response.json()


def check_response(response):
    """Здесь будет докстринг."""
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


def check_tokens():
    """Проверяет доступность переменных окружения."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    return False


def main():
    """Основная логика работы бота."""
    check = check_tokens()
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0
    while check:
        try:
            response = get_api_answer(current_timestamp)
            # current_timestamp = response.get("current_date")
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
        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logging.error(message)
            time.sleep(RETRY_TIME)
        else:
            pass


if __name__ == "__main__":
    main()
