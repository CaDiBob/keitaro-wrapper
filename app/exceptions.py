from fastapi import HTTPException, status


class BaseAppException(HTTPException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Внутренняя ошибка сервера"

    def __init__(self) -> None:
        super().__init__(
            status_code=self.status_code,
            detail=self.detail,
        )


class KeitaroRequestException(BaseAppException):
    status_code = status.HTTP_502_BAD_GATEWAY
    detail = "Keitaro не ответил или вернул ошибку"


class KeitaroNotFoundException(BaseAppException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "В Keitaro нет такого объекта"


class KeitaroNotConfiguredException(BaseAppException):
    status_code = status.HTTP_409_CONFLICT
    detail = "В Keitaro не найден домен, группа или источник"


class OfferNotFoundException(BaseAppException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Оффер не найден в Keitaro"


class StreamNotFoundException(BaseAppException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Поток не найден, обновите потоки из Keitaro"


class StreamHasNoOffersException(BaseAppException):
    status_code = status.HTTP_409_CONFLICT
    detail = "В этом потоке нет офферов, добавлять в него нельзя"


class OfferAlreadyInStreamException(BaseAppException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Этот оффер уже есть в потоке"


class OfferNotInStreamException(BaseAppException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Такого оффера в потоке нет"


class LastOfferException(BaseAppException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Нельзя удалить последний оффер потока"
