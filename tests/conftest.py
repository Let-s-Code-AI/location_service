import pytest
import tempfile
import os
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from sql_app.database import Base, get_db
from main import app


@pytest.fixture(scope="function")
async def client():
    """
    Fixture tworząca testowego klienta FastAPI (async).
    Override dependency get_db, aby używać testowej bazy danych.
    """
    # Utwórz tymczasowy plik bazy danych
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    # Test database URL - użyj tymczasowego pliku
    TEST_DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"
    
    # Create test engine
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
        echo=False,  # Wyłącz echo dla testów
    )
    
    # Create test session factory
    TestAsyncSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    # Tworzenie tabel przed każdym testem
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async def override_get_db():
        async with TestAsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://testserver") as test_client:
        yield test_client
    
    # Czyszczenie po teście
    await test_engine.dispose()
    
    # Usuń plik bazy danych
    if os.path.exists(db_path):
        os.unlink(db_path)
    
    # Usuń override po teście
    app.dependency_overrides.clear()

