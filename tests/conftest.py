import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import main as main_module
from app.core.dependencies import get_current_user
from app.core.rate_limit_dependencies import rate_limit_dependency
from app.database import Base, get_db
from app.main import app
from app.models.task import Task  # noqa: F401
from app.models.user import User  # noqa: F401

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_tasks_async.db"
test_engine = create_async_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine, expire_on_commit=False, autoflush=False
)


@pytest_asyncio.fixture
async def db():
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db, monkeypatch):
    monkeypatch.setattr(main_module, "engine", test_engine)

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with LifespanManager(app):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as test_client:
                yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def authenticated_client(client, db):
    user = User(
        username="test-user",
        email="test-user@example.com",
        hashed_password="test-hash",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    async def override_current_user():
        return user

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[rate_limit_dependency] = lambda: {
        "limit": 100,
        "remaining": 99,
        "reset": 0,
    }
    return client, user
