"""Wspólne fixtures: baza SQLite in-memory + klient HTTP podpięty pod aplikację."""
import os

# Ustawienie przed importem aplikacji: config.Settings czyta SECRET_KEY przy imporcie.
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from main import app
from sql_app import models  # noqa: F401  (rejestruje tabele w Base.metadata)
from sql_app.database import Base, get_db


@pytest_asyncio.fixture
async def engine():
    # StaticPool: jedno połączenie, więc in-memory DB jest widoczna dla całego testu
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db(engine) -> AsyncSession:
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(engine):
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


TEST_USER = {"email": "jan@example.com", "password": "haslo-testowe-123"}


@pytest_asyncio.fixture
async def auth_client(client):
    """Klient z nagłówkiem Authorization dla zarejestrowanego i zalogowanego użytkownika."""
    await client.post("/auth/register", json=TEST_USER)
    response = await client.post(
        "/auth/login",
        data={"username": TEST_USER["email"], "password": TEST_USER["password"]},
    )
    client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
    return client
