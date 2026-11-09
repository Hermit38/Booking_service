from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    # Pydantic автоматически ищет эти переменные в .env (регистр не важен)
    django_secret_key: str = Field(alias="DJANGO_SECRET_KEY")

    django_debug: bool = Field(default=True, alias="DJANGO_DEBUG")
    django_allowed_hosts: list[str] = Field(
        default=["localhost", "127.0.0.1"],
        alias="DJANGO_ALLOWED_HOSTS",
    )

    postgres_db: str = Field(default="booking_db", alias="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")

    # Автоматически читать файл .env в корне проекта
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # игнорировать другие переменные в .env
    )


# Создаем экземпляр, который выполнит валидацию при импорте
settings = AppSettings()
