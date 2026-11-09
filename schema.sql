-- ============================================================
-- Hotel booking service (CRM-style) schema
-- PostgreSQL 17
-- Таблицы: users, hotels, rooms, bookings
-- Пользователей создаёт админ. Cookie-сессий нет.
-- ============================================================

BEGIN;

-- Нужен для EXCLUDE CONSTRAINT по bigint (room_id)
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- ------------------------------------------------------------
-- Пользователи (создаёт админ; без пароля)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id          BIGSERIAL PRIMARY KEY,
    full_name   VARCHAR(255)  NOT NULL,
    phone       VARCHAR(32)   NOT NULL,
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT users_name_phone_uniq UNIQUE (full_name, phone)
);

CREATE INDEX IF NOT EXISTS users_phone_idx
    ON users (phone);

-- ------------------------------------------------------------
-- Отели
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hotels (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(255)  NOT NULL,
    address     VARCHAR(500)  NOT NULL,          -- новый столбец
    description TEXT          NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT hotels_address_uniq UNIQUE (address)
);

CREATE INDEX IF NOT EXISTS hotels_name_idx
    ON hotels (name);

-- ------------------------------------------------------------
-- Номера отеля
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rooms (
    id          BIGSERIAL PRIMARY KEY,
    hotel_id    BIGINT        NOT NULL,
    room_number VARCHAR(20)   NOT NULL,          -- новый столбец (101, 202, "A-1")
    description TEXT          NOT NULL,
    price       NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT rooms_hotel_fk
        FOREIGN KEY (hotel_id) REFERENCES hotels (id)
        ON DELETE CASCADE,

    CONSTRAINT rooms_hotel_number_uniq UNIQUE (hotel_id, room_number)
);

CREATE INDEX IF NOT EXISTS rooms_hotel_price_idx
    ON rooms (hotel_id, price);

CREATE INDEX IF NOT EXISTS rooms_hotel_created_at_idx
    ON rooms (hotel_id, created_at);

-- ------------------------------------------------------------
-- Брони
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bookings (
    id           BIGSERIAL PRIMARY KEY,
    user_id      BIGINT       NOT NULL,
    room_id      BIGINT       NOT NULL,
    date_start   DATE         NOT NULL,
    date_end     DATE         NOT NULL,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT bookings_user_fk
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE RESTRICT,

    CONSTRAINT bookings_room_fk
        FOREIGN KEY (room_id) REFERENCES rooms (id)
        ON DELETE CASCADE,

    CONSTRAINT bookings_dates_check
        CHECK (date_end >= date_start),

    CONSTRAINT bookings_user_room_dates_uniq UNIQUE (user_id, room_id, date_start, date_end)
);

CREATE INDEX IF NOT EXISTS bookings_room_start_idx
    ON bookings (room_id, date_start);

CREATE INDEX IF NOT EXISTS bookings_user_start_idx
    ON bookings (user_id, date_start);

-- Запрет пересекающихся броней на один номер (защита от гонки на уровне БД).
-- '[)': заезд в день выезда разрешён, пересечение интервалов — нет.
-- Отдельным идемпотентным блоком, т.к. CREATE TABLE IF NOT EXISTS пропустится,
-- если таблица уже существует (например, создана Django в тестовой БД).
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'bookings_no_overlap_excl'
    ) THEN
        ALTER TABLE bookings
            ADD CONSTRAINT bookings_no_overlap_excl
            EXCLUDE USING gist (
                room_id WITH =,
                daterange(date_start, date_end, '[)') WITH &&
            );
    END IF;
END $$;

-- ============================================================
-- Тестовые данные (seed)
-- ============================================================

-- ------------------------------------------------------------
-- Пользователи (5). Телефон НЕ уникален: Иванов и Иванова
-- делят один номер — проверяем, что UNIQUE нет.
-- ------------------------------------------------------------
INSERT INTO users (full_name, phone) VALUES
    ('Иванов Иван Иванович',    '+79990000001'),
    ('Иванова Мария Петровна',  '+79990000001'),
    ('Петров Пётр Сергеевич',   '+79990000002'),
    ('Сидорова Анна Викторовна','+79990000003'),
    ('Козлов Дмитрий Олегович', '+79990000004')
ON CONFLICT (full_name, phone) DO NOTHING;

-- Отели: ключ (address)
INSERT INTO hotels (name, address, description) VALUES
    ('Гранд Отель', 'г. Москва, ул. Тверская, д. 1', 'Пятизвёздочный отель в центре города, рядом с метро'),
    ('Приморский',  'г. Сочи, ул. Приморская, д. 10', 'Курортный отель на берегу моря, собственный пляж')
ON CONFLICT (address) DO NOTHING;

-- Номера: ключ (hotel_id, room_number); hotel_id — по адресу отеля
INSERT INTO rooms (hotel_id, room_number, description, price)
SELECT h.id, v.room_number, v.description, v.price
FROM (VALUES
    ('г. Москва, ул. Тверская, д. 1', '101', 'Standard: двуспальная кровать, 20 м², вид на двор',       5000.00),
    ('г. Москва, ул. Тверская, д. 1', '102', 'Deluxe: king-size, 35 м², вид на город',                  8500.00),
    ('г. Москва, ул. Тверская, д. 1', '103', 'Suite: гостиная + спальня, 60 м², панорамный вид',       15000.00),
    ('г. Сочи, ул. Приморская, д. 10', '201', 'Standard: две односпальные кровати, 18 м², вид на море',  4000.00),
    ('г. Сочи, ул. Приморская, д. 10', '202', 'Family: две комнаты, 45 м², подходит для семьи',          7000.00),
    ('г. Сочи, ул. Приморская, д. 10', '203', 'Penthouse: терраса, джакузи, 90 м², первая линия',       20000.00)
) AS v(hotel_address, room_number, description, price)
JOIN hotels h ON h.address = v.hotel_address
ON CONFLICT (hotel_id, room_number) DO NOTHING;

-- Брони: ключ (user_id, room_id, date_start, date_end)
INSERT INTO bookings (user_id, room_id, date_start, date_end)
SELECT u.id, r.id, v.ds::date, v.de::date
FROM (VALUES
    ('Иванов Иван Иванович',    '+79990000001', 'г. Москва, ул. Тверская, д. 1', '102', '2026-01-15', '2026-01-20'),
    ('Иванова Мария Петровна',  '+79990000001', 'г. Сочи, ул. Приморская, д. 10', '201', '2026-02-10', '2026-02-14'),
    ('Петров Пётр Сергеевич',   '+79990000002', 'г. Москва, ул. Тверская, д. 1', '103', '2026-03-01', '2026-03-05'),
    ('Сидорова Анна Викторовна','+79990000003', 'г. Сочи, ул. Приморская, д. 10', '202', '2026-04-20', '2026-04-27')
) AS v(full_name, phone, hotel_address, room_number, ds, de)
JOIN users u   ON u.full_name = v.full_name AND u.phone = v.phone
JOIN hotels h  ON h.address = v.hotel_address
JOIN rooms r   ON r.hotel_id = h.id AND r.room_number = v.room_number
ON CONFLICT (user_id, room_id, date_start, date_end) DO NOTHING;


COMMIT;