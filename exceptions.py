from datetime import datetime


class EndpointResponseError(Exception):
    """Ошибка ответа API."""

    def __init__(self, status_code):
        self.status_code = status_code

    def __str__(self) -> str:
        return (
            "Эндпоинт API Яндекс.Практикума недоступен: "
            f"Код ответа: {self.status_code}"
        )


class NotHomeWorks(Exception):
    """Ошибка вызванная отсутствием новых работ от даты current_date."""

    def __init__(self, response):
        self.current_date = response.get("current_date")

    def __str__(self) -> str:
        dt = datetime.utcfromtimestamp(self.current_date).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        return f"Начиная с {dt}, домашних работ нет."
