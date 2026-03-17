import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.pool import NullPool

from backend.main import app
import backend.database.session as db_session
from backend.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def _test_engine():
    """Session-scoped engine using NullPool to avoid cross-loop connection issues."""
    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
        echo=False,
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def client(_test_engine):
    """Session-scoped HTTP client; patches the DB session factory to use NullPool engine."""
    factory = async_sessionmaker(
        _test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def _get_db_override():
        async with factory() as session:
            try:
                yield session
            finally:
                await session.close()

    from backend.database.session import get_db
    app.dependency_overrides[get_db] = _get_db_override

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def auth_client(client: AsyncClient):
    """返回已注册并登录的 (client, token, user_data) 三元组"""
    unique = uuid.uuid4().hex[:8]
    user_data = {
        "email": f"test_{unique}@example.com",
        "username": f"testuser_{unique}",
        "password": "Test1234!",
    }
    reg = await client.post("/api/v1/auth/register", json=user_data)
    assert reg.status_code == 201, reg.text

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": user_data["email"], "password": user_data["password"]},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return client, headers, user_data

