from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Konfiguracja aplikacji. Wartości można nadpisać zmiennymi środowiskowymi lub plikiem .env."""

    database_url: str = "sqlite+aiosqlite:///./sql_app.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
