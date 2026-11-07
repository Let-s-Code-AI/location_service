"""
Skrypt do inicjalizacji bazy danych SQLite.
Uruchom ten skrypt, aby utworzyć wszystkie tabele.
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sql_app.database import Base
from sql_app import models 

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./sql_app.db"


async def init_db():
    """Tworzy wszystkie tabele w bazie danych."""
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=True
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("✅ Baza danych została zainicjalizowana!")


if __name__ == "__main__":
    asyncio.run(init_db())

