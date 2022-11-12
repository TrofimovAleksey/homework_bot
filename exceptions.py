from homework import Bot


class EndpointResponseError(Exception):
    """Ошибка ответа API."""

    def __init__(self, status_code):
        self.status_code = status_code

    def __str__(self) -> str:
        return (
            "Эндпоинт API Яндекс.Практикума недоступен: "
            f"Код ответа: {self.status_code}"
        )
