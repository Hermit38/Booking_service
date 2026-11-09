import threading

import pytest
from django.db import connections
from rest_framework.test import APIClient

from api.models import Booking, Hotel, Room, User


@pytest.mark.django_db
def test_create_booking(client: APIClient, user: User, room: Room) -> None:
    resp = client.post(
        "/bookings",
        {
            "user": user.id,
            "room": room.id,
            "date_start": "2026-05-01",
            "date_end": "2026-05-05",
        },
    )
    assert resp.status_code == 201
    assert "booking_id" in resp.json()


@pytest.mark.parametrize(
    "data, expected_status",
    [
        (
            {"date_start": "2026-05-05", "date_end": "2026-05-01"},
            400,
        ),  # даты наоборот
        (
            {"date_start": "2026-13-45", "date_end": "2026-05-05"},
            400,
        ),  # невалидная дата
        (
            {"room": 999999, "date_start": "2026-05-01", "date_end": "2026-05-05"},
            400,
        ),  # несуществующий номер
    ],
)
@pytest.mark.django_db
def test_create_booking_invalid(
    client: APIClient, user: User, room: Room, data: dict[str, object], expected_status: int
) -> None:
    payload = {
        "user": user.id,
        "room": room.id,
        "date_start": "2026-05-01",
        "date_end": "2026-05-05",
    }
    payload.update(data)

    resp = client.post("/bookings", payload)
    assert resp.status_code == expected_status
    assert "error" in resp.json()


@pytest.mark.parametrize(
    "new_start, new_end, expected_status",
    [
        ("2026-06-23", "2026-06-27", 400),  # пересекается (внутри)
        ("2026-06-26", "2026-06-28", 201),  # после выезда — ок
        ("2026-06-25", "2026-06-27", 201),  # заезд в день выезда — ок
        ("2026-06-10", "2026-06-20", 201),  # выезд в день заезда — ок
    ],
)
@pytest.mark.django_db
def test_create_booking_overlap_cases(
    client: APIClient, user: User, room: Room, new_start: str, new_end: str, expected_status: int
) -> None:
    Booking.objects.create(user=user, room=room, date_start="2026-06-20", date_end="2026-06-25")
    resp = client.post(
        "/bookings",
        {
            "user": user.id,
            "room": room.id,
            "date_start": new_start,
            "date_end": new_end,
        },
    )
    assert resp.status_code == expected_status


@pytest.mark.django_db(transaction=True)
def test_create_booking_race_condition(user: User, room: Room) -> None:
    # Два параллельных бронирования одного номера на пересекающиеся даты:
    # exclusion constraint в БД обязан пропустить ровно одно
    results: list[int] = []

    def book(date_start: str, date_end: str) -> None:
        try:
            client = APIClient()
            resp = client.post(
                "/bookings",
                {
                    "user": user.id,
                    "room": room.id,
                    "date_start": date_start,
                    "date_end": date_end,
                },
            )
            results.append(resp.status_code)
        finally:
            # Соединения Django thread-local: закрываем своё, иначе
            # pytest-django не сможет удалить test-БД на teardown
            connections["default"].close()

    threads = [
        threading.Thread(target=book, args=("2026-07-01", "2026-07-05")),
        threading.Thread(target=book, args=("2026-07-03", "2026-07-07")),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(results) == [201, 400]
    assert Booking.objects.filter(room=room).count() == 1

    # Закрываем соединения потоков, иначе pytest-django не сможет удалить test-БД
    connections.close_all()


@pytest.mark.django_db
def test_list_bookings_by_room(client: APIClient, user: User, room: Room) -> None:
    Booking.objects.create(user=user, room=room, date_start="2026-05-10", date_end="2026-05-12")
    Booking.objects.create(user=user, room=room, date_start="2026-05-01", date_end="2026-05-03")
    resp = client.get(f"/bookings?room_id={room.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    # сортировка по date_start: 05-01, 05-10
    assert data[0]["date_start"] == "2026-05-01"
    assert data[1]["date_start"] == "2026-05-10"


@pytest.mark.django_db
def test_list_bookings_by_user(client: APIClient, user: User, room: Room) -> None:
    hotel2 = Hotel.objects.create(name="Другой", address="г. X, ул. Y, 2")
    room2 = Room.objects.create(hotel=hotel2, room_number="201", description="B", price="3000.00")
    Booking.objects.create(user=user, room=room, date_start="2026-05-01", date_end="2026-05-03")
    Booking.objects.create(user=user, room=room2, date_start="2026-06-01", date_end="2026-06-03")
    resp = client.get(f"/bookings?user_id={user.id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.django_db
def test_get_booking(client: APIClient, user: User, room: Room) -> None:
    b = Booking.objects.create(user=user, room=room, date_start="2026-05-01", date_end="2026-05-03")
    resp = client.get(f"/bookings/{b.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == b.id


@pytest.mark.django_db
def test_delete_booking(client: APIClient, user: User, room: Room) -> None:
    b = Booking.objects.create(user=user, room=room, date_start="2026-05-01", date_end="2026-05-03")
    resp = client.delete(f"/bookings/{b.id}")
    assert resp.status_code == 204
    assert not Booking.objects.filter(id=b.id).exists()
