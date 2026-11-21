import logging
from collections.abc import AsyncGenerator

from sqlalchemy.exc import DBAPIError, OperationalError, TimeoutError as SQLAlchemyTimeoutError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.exceptions.user_exceptions import ServiceUnavailableError

logger = logging.getLogger(__name__)


def _normalize_database_url(url: str) -> str:
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


DATABASE_URL = _normalize_database_url(settings.DATABASE_URL)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite+") else {}

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as db:
        try:
            yield db
        except (OperationalError, SQLAlchemyTimeoutError) as exc:
            await db.rollback()
            logger.exception("Database is unavailable")
            raise ServiceUnavailableError("Database temporarily unavailable") from exc
        except DBAPIError as exc:
            await db.rollback()
            if exc.connection_invalidated:
                logger.exception("Database connection was lost")
                raise ServiceUnavailableError("Database temporarily unavailable") from exc
            raise
        except Exception:
            await db.rollback()
            raise
