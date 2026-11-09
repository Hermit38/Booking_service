# Booking Service

REST API сервис для управления номерами отелей и бронированиями. HTTP JSON API без авторизации: пользователи, отели, номера, брони. При бронировании проверяется, свободен ли номер на запрошенные даты (защита от двойного бронирования — в том числе от гонки параллельных запросов — на уровне базы данных).

## Стек технологий

- Python 3.13, Django 6.1, Django REST Framework 3.18
- PostgreSQL 17 (psycopg 3)
- Poetry 2.x, pydantic-settings
- Gunicorn (prod), Docker / Docker Compose
- pytest + pytest-django, ruff, mypy (strict), pre-commit, GitHub Actions

## Быстрый старт

```bash
cp .env-example .env     # заполнить DJANGO_SECRET_KEY и пароль БД
docker-compose up --build
```

API доступен на `http://localhost:9000`. При первом старте PostgreSQL автоматически выполняет `schema.sql` — создаются таблицы, индексы, ограничения и тестовые данные.

Остановка: `docker-compose down`. Полный сброс БД: `docker-compose down -v`.

## Переменные окружения

Все переменные описаны в `.env-example` и валидируются при старте (`src/config/config_env.py`, pydantic-settings):

| Переменная | Обязательна | По умолчанию | Назначение |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | да | — | секретный ключ Django |
| `DJANGO_DEBUG` | нет | `True` | режим отладки |
| `DJANGO_ALLOWED_HOSTS` | нет | `localhost,127.0.0.1` | разрешённые хосты |
| `POSTGRES_DB` | нет | `booking_db` | имя базы |
| `POSTGRES_USER` | нет | `postgres` | пользователь БД |
| `POSTGRES_PASSWORD` | нет | `postgres` | пароль БД |
| `POSTGRES_HOST` | нет | `localhost` | хост БД (в compose переопределяется на `db`) |
| `POSTGRES_PORT` | нет | `5432` | порт БД |
| `DJANGO_LOG_LEVEL` | нет | `INFO` | уровень логирования |

## Установка (без Docker, для разработки)

```bash
poetry install --no-root --with dev   # зависимости
cp .env-example .env                  # заполнить значения
# поднять PostgreSQL 17 (например: docker-compose up db)
python manage.py runserver            # http://localhost:8000
```

Миграций в проекте нет: схемой БД владеет `schema.sql` (модели Django объявлены с `managed = False`). Для локальной БД накатите схему вручную: `psql -d booking_db -f schema.sql`.

## Тесты

```bash
make test          # или: poetry run pytest -v
```

Тестам нужна доступная PostgreSQL (например, `docker-compose up db`): pytest-django создаёт отдельную тестовую БД и строит её из `schema.sql` (не из миграций). 53 теста: CRUD всех сущностей, валидация дат, пересечения броней, каскадное удаление, гонка параллельных бронирований.

Линт и типизация:

```bash
make lint          # ruff check src + mypy src (strict)
```

## API

Без префикса и без завершающего слэша. Все ответы — JSON; ошибки — `{"error": "..."}` с соответствующим статусом.

### Пользователи

- `GET /users` — список
- `POST /users` — создать: `{"full_name": "...", "phone": "..."}` → `201 {"user_id": N}`
- `GET /users/<id>` — один пользователь
- `DELETE /users/<id>` — удалить (нельзя, если есть брони → `400`)

### Отели

- `GET /hotels` — список
- `POST /hotels` — создать: `{"name": "...", "address": "...", "description": "..."}` → `201 {"hotel_id": N}`
- `GET /hotels/<id>` — один отель
- `DELETE /hotels/<id>` — удалить (каскадно удаляет номера и их брони)

### Номера

- `GET /rooms` — список; параметры: `?hotel_id=N`, `?sort=price|created_at`, `?order=asc|desc`
- `POST /rooms` — создать: `{"hotel": N, "room_number": "101", "description": "...", "price": "5000.00"}` → `201 {"room_id": N}`
- `GET /rooms/<id>` — один номер
- `DELETE /rooms/<id>` — удалить (каскадно удаляет брони этого номера)

### Брони

- `GET /bookings` — список, отсортирован по `date_start`; параметры: `?room_id=N`, `?user_id=N`
- `POST /bookings` — создать: `{"user": N, "room": N, "date_start": "2026-05-01", "date_end": "2026-05-05"}` → `201 {"booking_id": N}`
- `GET /bookings/<id>` — одна бронь
- `DELETE /bookings/<id>` — удалить → `204`

Примеры:

```bash
# создать бронь
curl -X POST http://localhost:9000/bookings \
  -H "Content-Type: application/json" \
  -d '{"user": 1, "room": 1, "date_start": "2026-05-01", "date_end": "2026-05-05"}'
# → {"booking_id": 1}

# список броней номера
curl "http://localhost:9000/bookings?room_id=1"
# → [{"id": 1, "user": 1, "room": 1, "date_start": "2026-05-01", "date_end": "2026-05-05", ...}]

# номера отеля по цене (по убыванию)
curl "http://localhost:9000/rooms?hotel_id=1&sort=price&order=desc"
```

## Принятые решения (по вопросам из ТЗ)

- **REST вместо RPC-путей.** Вместо `/bookings/create` и `/bookings/list` используются стандартные ресурсы: `POST /bookings`, `GET /bookings?room_id=N`. Функционал ТЗ сохранён.
- **Ответ при создании** — `{"booking_id": N}` (в примере ТЗ опечатка `cbooking_id`).
- **Заезд в день выезда разрешён**: интервалы броней полуоткрытые `[date_start, date_end)`. Бронь 20–25 июня не мешает брони с 25 июня.
- **Проверка занятости номера** (усложнение из ТЗ) реализована двухуровнево: быстрая проверка в `BookingService` даёт понятную ошибку, а exclusion constraint `bookings_no_overlap_excl` в PostgreSQL (`daterange` + `btree_gist`) гарантирует запрет двойного бронирования даже при параллельных запросах (гонке).
- **Миграции не используются** — по ТЗ достаточно файла со схемой: `schema.sql` — единственный владелец DDL (таблицы, индексы, ограничения, seed-данные). Модели Django объявлены с `managed = False`; тестовая БД также строится из `schema.sql`.
- **Удаление**: отель/номер удаляются каскадно вместе с бронями (требование ТЗ); пользователя с бронями удалить нельзя (`RESTRICT` → `400`).
- **Бронь привязана к пользователю** (`user_id` обязателен) — каталог пользователей и отелей ведётся административно, авторизации нет по требованию ТЗ.

## Структура проекта

```
src/
├── config/         # настройки Django, config_env.py (pydantic-settings), urls, wsgi
└── api/            # models → services → views (трёхслойная архитектура), serializers, exceptions
tests/              # pytest (conftest.py строит тестовую БД из schema.sql)
schema.sql          # схема БД + тестовые данные (владелец DDL)
docker-compose.yml  # db (postgres:17) + app (gunicorn, порт 9000)
```
