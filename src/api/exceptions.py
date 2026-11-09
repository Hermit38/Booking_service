import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def _flatten_errors(data: object) -> str:
    """Сводит тело ошибки DRF (dict/list/str) в одну строку для поля "error"."""
    if isinstance(data, dict):
        if "detail" in data and len(data) == 1:
            return str(data["detail"])
        parts = []
        for field, value in data.items():
            if isinstance(value, (list, tuple)):
                parts.append(f"{field}: {', '.join(str(v) for v in value)}")
            else:
                parts.append(f"{field}: {value}")
        return "; ".join(parts)
    if isinstance(data, (list, tuple)):
        return "; ".join(str(v) for v in data)
    return str(data)


def custom_exception_handler(exc: Exception, context: dict[str, object]) -> Response:
    """Единая точка обработки ошибок API: любой ответ об ошибке — {"error": "..."}.

    Зарегистрирован в REST_FRAMEWORK["EXCEPTION_HANDLER"] (config/settings.py).
    """
    response = exception_handler(exc, context)
    if response is not None:
        return Response(
            {"error": _flatten_errors(response.data)},
            status=response.status_code,
            headers=response.headers,
        )

    if isinstance(exc, ObjectDoesNotExist):
        model_name = getattr(exc, "model_name", "Объект")
        return Response({"error": f"{model_name} не найден"}, status=status.HTTP_404_NOT_FOUND)

    if isinstance(exc, IntegrityError):
        error_msg = str(exc).lower()

        if "bookings_no_overlap" in error_msg or "exclusion constraint" in error_msg:
            logger.warning(f"Бронирование отклонено ограничением БД: {exc}")
            return Response(
                {"error": "Номер недоступен на выбранные даты (пересечение броней)"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        logger.warning(f"Нарушено ограничение целостности БД: {exc}")
        return Response(
            {"error": "Нарушено ограничение базы данных (например, дубликат или запрет удаления)"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    logger.exception("Необработанное исключение: %s", exc)
    return Response(
        {"error": "Внутренняя ошибка сервера"},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
