from collections.abc import Generator
from pathlib import Path

import pytest
from django.db import connection
from pytest_django.plugin import DjangoDbBlocker
from rest_framework.test import APIClient

from api.models import Hotel, Room, User

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema.sql"


@pytest.fixture(scope="session")
def django_db_use_migrations() -> bool:
    # Тестовая БД строится из schema.sql, а не из миграций
    return False


@pytest.fixture(scope="session")
def django_db_setup(
    django_db_setup: None,
    django_db_blocker: DjangoDbBlocker,
) -> Generator[None]:
    # Оригинальная фикстура pytest-django уже создала test-БД — докатываем schema.sql
    # (идемпотентно: IF NOT EXISTS / ON CONFLICT DO NOTHING / проверка pg_constraint)
    with django_db_blocker.unblock(), connection.cursor() as cur:
        cur.execute(SCHEMA_PATH.read_text(encoding="utf-8"))
    yield


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db: None) -> User:
    return User.objects.create(full_name="Тест Тестов", phone="+70001112233")


@pytest.fixture
def hotel(db: None) -> Hotel:
    return Hotel.objects.create(
        name="Тест Отель",
        address="г. Тест, ул. Тестовая, 1",
    )


@pytest.fixture
def room(db: None, hotel: Hotel) -> Room:
    return Room.objects.create(
        hotel=hotel,
        room_number="101",
        description="Standard",
        price="5000.00",
    )
