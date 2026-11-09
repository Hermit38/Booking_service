import pytest
from rest_framework.test import APIClient

from api.models import Hotel, Room


@pytest.mark.django_db
def test_create_room(client: APIClient, hotel: Hotel) -> None:
    resp = client.post(
        "/rooms",
        {
            "hotel": hotel.id,
            "room_number": "102",
            "description": "Deluxe",
            "price": "8500.00",
        },
    )
    assert resp.status_code == 201
    assert "room_id" in resp.json()


@pytest.mark.django_db
def test_create_room_duplicate_number(client: APIClient, room: Room) -> None:
    # room: hotel=..., room_number="101"
    resp = client.post(
        "/rooms",
        {
            "hotel": room.hotel.id,
            "room_number": room.room_number,
            "description": "Другой",
            "price": "6000.00",
        },
    )
    assert resp.status_code == 400
    assert "error" in resp.json()


@pytest.mark.django_db
def test_list_rooms_by_hotel(client: APIClient, hotel: Hotel) -> None:
    Room.objects.create(hotel=hotel, room_number="101", description="A", price="1000.00")
    Room.objects.create(hotel=hotel, room_number="102", description="B", price="2000.00")
    other = Hotel.objects.create(name="Другой", address="г. Другой, ул. X, 1")
    Room.objects.create(hotel=other, room_number="101", description="C", price="3000.00")

    resp = client.get(f"/rooms?hotel_id={hotel.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(r["hotel"] == hotel.id for r in data)


@pytest.mark.parametrize(
    "order, reverse",
    [
        ("asc", False),
        ("desc", True),
    ],
)
@pytest.mark.django_db
def test_list_rooms_sort_price(client: APIClient, hotel: Hotel, order: str, reverse: bool) -> None:
    Room.objects.create(hotel=hotel, room_number="101", description="A", price="5000.00")
    Room.objects.create(hotel=hotel, room_number="102", description="B", price="1000.00")
    Room.objects.create(hotel=hotel, room_number="103", description="C", price="3000.00")

    resp = client.get(f"/rooms?hotel_id={hotel.id}&sort=price&order={order}")
    prices = [r["price"] for r in resp.json()]
    assert prices == sorted(prices, reverse=reverse)


@pytest.mark.django_db
def test_list_rooms_invalid_sort(client: APIClient) -> None:
    resp = client.get("/rooms?sort=bad")
    assert resp.status_code == 400
    assert "error" in resp.json()


@pytest.mark.django_db
def test_get_room(client: APIClient, room: Room) -> None:
    resp = client.get(f"/rooms/{room.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == room.id


@pytest.mark.django_db
def test_delete_room(client: APIClient, room: Room) -> None:
    resp = client.delete(f"/rooms/{room.id}")
    assert resp.status_code == 204
    assert not Room.objects.filter(id=room.id).exists()
