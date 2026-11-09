import os
from pathlib import Path

from config.config_env import settings

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = settings.django_secret_key

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = settings.django_debug

ALLOWED_HOSTS = settings.django_allowed_hosts


# Application definition

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "rest_framework",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": settings.postgres_db,
        "USER": settings.postgres_user,
        "PASSWORD": settings.postgres_password,
        "HOST": settings.postgres_host,
        "PORT": str(settings.postgres_port),
    }
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "EXCEPTION_HANDLER": "api.exceptions.custom_exception_handler",
    "UNAUTHENTICATED_USER": None,
}


# Internationalization
# https://docs.djangoproject.com/en/6.1/topics/i18n/

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = "static/"


LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} [{levelname}] {name} (line {lineno}): {message}",
            "style": "{",
        },
    },
    "handlers": {
        # 1. По-прежнему выводим в консоль (для Docker/терминала)
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        # 2. Пишем в файл с ротацией по размеру
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "app.log",  # Файл будет лежать в /logs/app.log
            "maxBytes": 5 * 1024 * 1024,  # Максимальный размер файла — 5 МБ
            "backupCount": 5,  # Хранить до 5 старых файлов (app.log.1, app.log.2)
            "formatter": "verbose",
            "encoding": "utf-8",  # Чтобы кириллица не превращалась в кракозябры
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],  # Отправляем и в консоль, и в файл
            "level": LOG_LEVEL,
        },
        "api": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
