from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Konfiguracja aplikacji. Wartości można nadpisać zmiennymi środowiskowymi lub plikiem .env."""

    database_url: str = "sqlite+aiosqlite:///./sql_app.db"

    # Klucz do podpisywania tokenów JWT. Brak domyślnej wartości celowo:
    # aplikacja nie wystartuje bez ustawionego SECRET_KEY w .env lub środowisku.
    secret_key: str
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
