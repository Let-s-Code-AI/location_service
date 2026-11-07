"""
Skrypt do inicjalizacji bazy danych SQLite.
Uruchom ten skrypt, aby utworzyć wszystkie tabele.
"""
import asyncio
from sql_app.database import Base, engine
from sql_app import models


async def init_db():
    """Tworzy wszystkie tabele w bazie danych."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    print("✅ Baza danych została zainicjalizowana!")


if __name__ == "__main__":
    asyncio.run(init_db())

