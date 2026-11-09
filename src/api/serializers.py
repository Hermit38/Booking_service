from rest_framework import serializers

from .models import Booking, Hotel, Room, User

# ------------------------------------------------------------
# Выходные данные (Ответы API / Чтение)
# ------------------------------------------------------------


class UserSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ["id", "full_name", "phone", "created_at"]


class HotelSerializer(serializers.ModelSerializer[Hotel]):
    class Meta:
        model = Hotel
        fields = ["id", "name", "address", "description", "created_at"]


class RoomSerializer(serializers.ModelSerializer[Room]):
    class Meta:
        model = Room
        fields = ["id", "hotel", "room_number", "description", "price", "created_at"]


class BookingSerializer(serializers.ModelSerializer[Booking]):
    class Meta:
        model = Booking
        fields = ["id", "user", "room", "date_start", "date_end", "created_at"]


# ------------------------------------------------------------
# Входные данные (Запросы API / Валидация)
# ------------------------------------------------------------


class UserCreateSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ["full_name", "phone"]


class HotelCreateSerializer(serializers.ModelSerializer[Hotel]):
    class Meta:
        model = Hotel
        fields = ["name", "address", "description"]


class RoomCreateSerializer(serializers.ModelSerializer[Room]):
    class Meta:
        model = Room
        fields = ["hotel", "room_number", "description", "price"]


class BookingCreateSerializer(serializers.ModelSerializer[Booking]):
    class Meta:
        model = Booking
        fields = ["user", "room", "date_start", "date_end"]
