from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

# SQLite connection string
# Użyj "sqlite+aiosqlite:///" dla bazy w pamięci lub "sqlite+aiosqlite:///./sql_app.db" dla pliku
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./sql_app.db"

# Create async engine with optimized settings for SQLite
# SQLite używa NullPool, ponieważ nie obsługuje puli połączeń w tradycyjnym sensie
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False,  # Wymagane dla SQLite w środowisku asynchronicznym
        # Opcjonalne: ustawienia PRAGMA dla lepszej wydajności
        "timeout": 20.0,  # Timeout dla operacji na bazie danych
    },
    poolclass=NullPool,  # SQLite nie używa puli połączeń, użyj NullPool
    echo=True,  # Set to False in production - pokazuje SQL queries w logach
    future=True,  # Użyj SQLAlchemy 2.0 API
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Obiekty nie wygasają po commit
    autocommit=False,
    autoflush=False,
)

# Base class for models (SQLAlchemy 2.0 style)
class Base(DeclarativeBase):
    pass


# Dependency for FastAPI
async def get_db() -> AsyncSession:
    """
    Dependency injection dla sesji bazy danych.
    Automatycznie zarządza otwieraniem i zamykaniem sesji.
    
    Uwaga: Commit powinien być wykonywany ręcznie w endpointach.
    Dependency automatycznie wykonuje rollback w przypadku błędu.
    
    Usage:
        @app.post("/items/")
        async def create_item(db: Annotated[AsyncSession, Depends(get_db)]):
            db_item = models.Item(...)
            db.add(db_item)
            await db.commit()  # Ręczny commit
            return db_item
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()  # Rollback w przypadku błędu
            raise
        finally:
            await session.close()  # Zawsze zamykaj sesję

