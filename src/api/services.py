import logging
from datetime import date

from django.db.models import QuerySet
from rest_framework.exceptions import ValidationError

from .models import Booking, Hotel, Room, User

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    def list_users() -> QuerySet[User]:
        return User.objects.all().order_by("id")

    @staticmethod
    def get_user(user_id: int) -> User:
        # DoesNotExist отловится в custom_exception_handler → 404
        return User.objects.get(id=user_id)

    @staticmethod
    def create_user(full_name: str, phone: str) -> User:
        user = User.objects.create(full_name=full_name, phone=phone)
        logger.info(f"Пользователь успешно создан: ID {user.id} (Имя: {user.full_name})")
        return user

    @staticmethod
    def delete_user(user_id: int) -> None:
        user = User.objects.get(id=user_id)
        user.delete()
        logger.info(f"Пользователь успешно удален: ID {user_id}")


class HotelService:
    @staticmethod
    def list_hotels() -> QuerySet[Hotel]:
        return Hotel.objects.all().order_by("id")

    @staticmethod
    def get_hotel(hotel_id: int) -> Hotel:
        return Hotel.objects.get(id=hotel_id)

    @staticmethod
    def create_hotel(name: str, address: str, description: str = "") -> Hotel:
        hotel = Hotel.objects.create(name=name, address=address, description=description)
        logger.info(f"Отель успешно создан: ID {hotel.id} (Название: {hotel.name})")
        return hotel

    @staticmethod
    def delete_hotel(hotel_id: int) -> None:
        hotel = Hotel.objects.get(id=hotel_id)
        hotel.delete()
        logger.info(f"Отель успешно удален: ID {hotel_id}")


class RoomService:
    @staticmethod
    def list_rooms(hotel_id: str | None, sort: str, order: str) -> QuerySet[Room]:
        # sort/order уже проверены по белому списку во view — подстановка в order_by безопасна
        qs = Room.objects.all()
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
        return qs.order_by(sort if order == "asc" else f"-{sort}")

    @staticmethod
    def get_room(room_id: int) -> Room:
        return Room.objects.get(id=room_id)

    @staticmethod
    def create_room(hotel_id: int, room_number: str, description: str, price: float) -> Room:
        room = Room.objects.create(
            hotel_id=hotel_id, room_number=room_number, description=description, price=price
        )
        logger.info(f"Номер успешно создан: ID {room.id} (Отель: {hotel_id}, Номер: {room_number})")
        return room

    @staticmethod
    def delete_room(room_id: int) -> None:
        room = Room.objects.get(id=room_id)
        room.delete()
        logger.info(f"Номер успешно удален: ID {room_id}")


class BookingService:
    @staticmethod
    def list_bookings(room_id: str | None, user_id: str | None) -> QuerySet[Booking]:
        qs = Booking.objects.all()
        if room_id:
            qs = qs.filter(room_id=room_id)
        if user_id:
            qs = qs.filter(user_id=user_id)
        return qs.order_by("date_start")

    @staticmethod
    def get_booking(booking_id: int) -> Booking:
        return Booking.objects.get(id=booking_id)

    @staticmethod
    def create_booking(user_id: int, room_id: int, date_start: date, date_end: date) -> Booking:
        if date_end < date_start:
            logger.warning(
                f"Ошибка бронирования: date_end ({date_end}) "
                f"раньше date_start ({date_start}) для пользователя {user_id}"
            )
            raise ValidationError({"date_end": "date_end должен быть больше date_start"})

        # Быстрый путь с понятной ошибкой; страховка от гонки параллельных запросов —
        # exclusion constraint bookings_no_overlap_excl в schema.sql. Оба уровня нужны.
        overlapping = Booking.objects.filter(
            room_id=room_id,
            date_start__lt=date_end,
            date_end__gt=date_start,
        )
        if overlapping.exists():
            logger.warning(
                f"Ошибка бронирования: Номер {room_id} уже занят на даты {date_start} - {date_end}"
            )
            raise ValidationError({"error": "Номер недоступен на выбранные даты"})

        booking = Booking.objects.create(
            user_id=user_id, room_id=room_id, date_start=date_start, date_end=date_end
        )
        logger.info(
            f"Бронирование успешно создано: ID {booking.id} "
            f"(Пользователь: {user_id}, Номер: {room_id}, Даты: {date_start} - {date_end})"
        )
        return booking

    @staticmethod
    def delete_booking(booking_id: int) -> None:
        booking = Booking.objects.get(id=booking_id)
        booking.delete()
        logger.info(f"Бронирование успешно удалено: ID {booking_id}")
