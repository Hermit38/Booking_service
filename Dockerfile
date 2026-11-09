# ============================================================
# Stage 1: builder — Poetry ставит прод-зависимости в /app/.venv
# ============================================================
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=2.5.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_VIRTUALENVS_CREATE=true

WORKDIR /app


# Poetry (no-cache-dir — не тащим pip-кэш)
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

# сначала манифесты — кэш слоёв (меняешь код → poetry install не перезапускается)
COPY pyproject.toml poetry.lock ./

# прод-зависимости в /app/.venv, без .pyc (--no-compile), без root-проекта
RUN poetry install --only main --no-root \
    && rm -rf /root/.cache/pip /root/.cache/pypoetry

# ============================================================
# Stage 2: runtime — тонкий, только venv + код + libpq5
# ============================================================
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    VIRTUAL_ENV="/app/.venv" \
    PYTHONPATH="/app/src"

WORKDIR /app

# только runtime-lib (psycopg-binary несёт свою libpq, но libpq5 — страховка, ~1MB)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# venv из builder (со всеми прод-пакетами, без .pyc)
COPY --from=builder /app/.venv /app/.venv

# код (без .venv/.env/кэшей/tests — .dockerignore)
COPY . .

EXPOSE 9000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:9000", "--workers", "4", "--timeout", "120", "--log-level", "info"]