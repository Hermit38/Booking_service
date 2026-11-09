import pytest
from rest_framework import status
from rest_framework.test import APIClient

from api.models import Booking, Hotel, Room, User

# ============================================================
# Booking — невалидные данные (parametrize)
# ============================================================


@pytest.mark.parametrize(
    "data, expected_status",
    [
        # невалидные даты
        ({"date_start": "2026-05-05", "date_end": "2026-05-01"}, status.HTTP_400_BAD_REQUEST),
        ({"date_start": "2026-13-45", "date_end": "2026-05-05"}, status.HTTP_400_BAD_REQUEST),
        # отсутствие дат
        ({"date_start": None, "date_end": None}, status.HTTP_400_BAD_REQUEST),
        # несуществующий FK (перехватывается сериализатором)
        (
            {"date_start": "2026-05-01", "date_end": "2026-05-05", "room": 999999},
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            {"date_start": "2026-05-01", "date_end": "2026-05-05", "user": 999999},
            status.HTTP_400_BAD_REQUEST,
        ),
    ],
)
@pytest.mark.django_db
def test_booking_invalid(
    client: APIClient, user: User, room: Room, data: dict[str, object], expected_status: int
) -> None:
    payload = {
        "user": user.id,
        "room": room.id,
        "date_start": "2026-05-01",
        "date_end": "2026-05-05",
    }
    payload.update(data)

    response = client.post("/bookings", payload, format="json")
    assert response.status_code == expected_status


@pytest.mark.django_db
def test_booking_date_end_equals_start(client: APIClient, user: User, room: Room) -> None:
    response = client.post(
        "/bookings",
        data={
            "user": user.id,
            "room": room.id,
            "date_start": "2026-05-05",
            "date_end": "2026-05-05",
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED


# ============================================================
# Booking — пересечение (parametrize): существующая [20,25]
# ============================================================


@pytest.mark.parametrize(
    "new_start, new_end, expected_status",
    [
        ("2026-06-23", "2026-06-27", status.HTTP_400_BAD_REQUEST),  # внутри — пересекается
        ("2026-06-19", "2026-06-26", status.HTTP_400_BAD_REQUEST),  # покрывает — пересекается
        ("2026-06-21", "2026-06-22", status.HTTP_400_BAD_REQUEST),  # внутри — пересекается
        ("2026-06-10", "2026-06-15", status.HTTP_201_CREATED),  # до — не пересекается
        ("2026-06-26", "2026-06-28", status.HTTP_201_CREATED),  # после — не пересекается
        (
            "2026-06-25",
            "2026-06-27",
            status.HTTP_201_CREATED,
        ),  # заезд в день выезда — не пересекается
        (
            "2026-06-10",
            "2026-06-20",
            status.HTTP_201_CREATED,
        ),  # выезд в день заезда — не пересекается
    ],
)
@pytest.mark.django_db
def test_booking_overlap(
    client: APIClient, user: User, room: Room, new_start: str, new_end: str, expected_status: int
) -> None:
    Booking.objects.create(user=user, room=room, date_start="2026-06-20", date_end="2026-06-25")
    response = client.post(
        "/bookings",
        data={
            "user": user.id,
            "room": room.id,
            "date_start": new_start,
            "date_end": new_end,
        },
        format="json",
    )
    assert response.status_code == expected_status


@pytest.mark.django_db
def test_booking_overlap_different_room(client: APIClient, user: User, room: Room) -> None:
    other_hotel = Hotel.objects.create(name="Другой", address="г. X, ул. Y, 2")
    other_room = Room.objects.create(
        hotel=other_hotel,
        room_number="201",
        description="B",
        price="3000.00",
    )
    Booking.objects.create(user=user, room=room, date_start="2026-06-20", date_end="2026-06-25")
    response = client.post(
        "/bookings",
        data={
            "user": user.id,
            "room": other_room.id,
            "date_start": "2026-06-23",
            "date_end": "2026-06-27",
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED


# ============================================================
# User
# ============================================================


@pytest.mark.django_db
def test_user_serializer_duplicate(client: APIClient, user: User) -> None:
    response = client.post(
        "/users", data={"full_name": user.full_name, "phone": user.phone}, format="json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_user_serializer_same_phone_different_name(client: APIClient, user: User) -> None:
    response = client.post(
        "/users", data={"full_name": "Другое Имя", "phone": user.phone}, format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED


# ============================================================
# Hotel
# ============================================================


@pytest.mark.django_db
def test_hotel_serializer_duplicate_address(client: APIClient, hotel: Hotel) -> None:
    response = client.post(
        "/hotels", data={"name": "Другой", "address": hotel.address}, format="json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================
# Room
# ============================================================


@pytest.mark.django_db
def test_room_serializer_duplicate_number(client: APIClient, room: Room) -> None:
    response = client.post(
        "/rooms",
        data={
            "hotel": room.hotel.id,
            "room_number": room.room_number,
            "description": "Другой",
            "price": "6000.00",
        },
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
