import pytest
from rest_framework.test import APIClient

from api.models import Booking, Hotel, Room, User


@pytest.mark.django_db
def test_delete_hotel_cascades_rooms_and_bookings(
    client: APIClient, user: User, hotel: Hotel, room: Room
) -> None:
    Booking.objects.create(user=user, room=room, date_start="2026-05-01", date_end="2026-05-03")
    resp = client.delete(f"/hotels/{hotel.id}")
    assert resp.status_code == 204
    assert not Room.objects.filter(hotel_id=hotel.id).exists()
    assert not Booking.objects.filter(room_id=room.id).exists()


@pytest.mark.django_db
def test_delete_room_cascades_bookings(client: APIClient, user: User, room: Room) -> None:
    Booking.objects.create(user=user, room=room, date_start="2026-05-01", date_end="2026-05-03")
    resp = client.delete(f"/rooms/{room.id}")
    assert resp.status_code == 204
    assert not Booking.objects.filter(room_id=room.id).exists()


@pytest.mark.django_db
def test_delete_user_with_bookings_restrict(client: APIClient, user: User, room: Room) -> None:
    Booking.objects.create(user=user, room=room, date_start="2026-05-01", date_end="2026-05-03")
    resp = client.delete(f"/users/{user.id}")
    assert resp.status_code == 400
    assert "error" in resp.json()
    assert User.objects.filter(id=user.id).exists()  # не удалён
