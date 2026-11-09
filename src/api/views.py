import logging

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    BookingCreateSerializer,
    BookingSerializer,
    HotelCreateSerializer,
    HotelSerializer,
    RoomCreateSerializer,
    RoomSerializer,
    UserCreateSerializer,
    UserSerializer,
)
from .services import BookingService, HotelService, RoomService, UserService

logger = logging.getLogger(__name__)

# ============================================================
# USERS
# ============================================================


class UserListCreateView(APIView):
    """GET /users — список; POST /users — создать через сервис."""

    def get(self, request: Request) -> Response:
        users = UserService.list_users()
        return Response(UserSerializer(instance=users, many=True).data)

    def post(self, request: Request) -> Response:
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = UserService.create_user(
            full_name=serializer.validated_data["full_name"],
            phone=serializer.validated_data["phone"],
        )
        return Response({"user_id": user.id}, status=status.HTTP_201_CREATED)


class UserDetailView(APIView):
    """GET /users/{id} — один; DELETE /users/{id} — удалить через сервис."""

    def get(self, request: Request, user_id: int) -> Response:
        user = UserService.get_user(user_id=user_id)
        return Response(UserSerializer(instance=user).data)

    def delete(self, request: Request, user_id: int) -> Response:
        UserService.delete_user(user_id=user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================
# HOTELS
# ============================================================


class HotelListCreateView(APIView):
    """GET /hotels — список; POST /hotels — создать через сервис."""

    def get(self, request: Request) -> Response:
        hotels = HotelService.list_hotels()
        return Response(HotelSerializer(instance=hotels, many=True).data)

    def post(self, request: Request) -> Response:
        serializer = HotelCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        hotel = HotelService.create_hotel(
            name=serializer.validated_data["name"],
            address=serializer.validated_data["address"],
            description=serializer.validated_data.get("description", ""),
        )
        return Response({"hotel_id": hotel.id}, status=status.HTTP_201_CREATED)


class HotelDetailView(APIView):
    """GET /hotels/{id}; DELETE /hotels/{id} через сервис."""

    def get(self, request: Request, hotel_id: int) -> Response:
        hotel = HotelService.get_hotel(hotel_id=hotel_id)
        return Response(HotelSerializer(instance=hotel).data)

    def delete(self, request: Request, hotel_id: int) -> Response:
        HotelService.delete_hotel(hotel_id=hotel_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================
# ROOMS
# ============================================================


class RoomListCreateView(APIView):
    """GET /rooms с фильтрацией; POST /rooms — создать через сервис."""

    def get(self, request: Request) -> Response:
        hotel_id = request.query_params.get("hotel_id")
        sort = request.query_params.get("sort", "created_at")
        order = request.query_params.get("order", "asc")

        if sort not in {"price", "created_at"}:
            logger.warning(f"Некорректный параметр сортировки передан в /rooms: '{sort}'")
            return Response(
                {"error": "sort должен быть 'price' или 'created_at'"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if order not in {"asc", "desc"}:
            logger.warning(f"Некорректный параметр порядка передан в /rooms: '{order}'")
            return Response(
                {"error": "order должен быть 'asc' или 'desc'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rooms = RoomService.list_rooms(hotel_id=hotel_id, sort=sort, order=order)
        return Response(RoomSerializer(instance=rooms, many=True).data)

    def post(self, request: Request) -> Response:
        serializer = RoomCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        room = RoomService.create_room(
            hotel_id=serializer.validated_data["hotel"].id,
            room_number=serializer.validated_data["room_number"],
            description=serializer.validated_data["description"],
            price=serializer.validated_data["price"],
        )
        return Response({"room_id": room.id}, status=status.HTTP_201_CREATED)


class RoomDetailView(APIView):
    """GET /rooms/{id}; DELETE /rooms/{id} через сервис."""

    def get(self, request: Request, room_id: int) -> Response:
        room = RoomService.get_room(room_id=room_id)
        return Response(RoomSerializer(instance=room).data)

    def delete(self, request: Request, room_id: int) -> Response:
        RoomService.delete_room(room_id=room_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================
# BOOKINGS
# ============================================================


class BookingListCreateView(APIView):
    """GET /bookings; POST /bookings — забронировать через сервис."""

    def get(self, request: Request) -> Response:
        bookings = BookingService.list_bookings(
            room_id=request.query_params.get("room_id"),
            user_id=request.query_params.get("user_id"),
        )
        return Response(BookingSerializer(instance=bookings, many=True).data)

    def post(self, request: Request) -> Response:
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking = BookingService.create_booking(
            user_id=serializer.validated_data["user"].id,
            room_id=serializer.validated_data["room"].id,
            date_start=serializer.validated_data["date_start"],
            date_end=serializer.validated_data["date_end"],
        )
        return Response({"booking_id": booking.id}, status=status.HTTP_201_CREATED)


class BookingDetailView(APIView):
    """GET /bookings/{id}; DELETE /bookings/{id} через сервис."""

    def get(self, request: Request, booking_id: int) -> Response:
        booking = BookingService.get_booking(booking_id=booking_id)
        return Response(BookingSerializer(instance=booking).data)

    def delete(self, request: Request, booking_id: int) -> Response:
        BookingService.delete_booking(booking_id=booking_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
