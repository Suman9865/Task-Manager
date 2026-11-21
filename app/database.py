import logging
from collections.abc import AsyncGenerator

from sqlalchemy.exc import DBAPIError, OperationalError, TimeoutError as SQLAlchemyTimeoutError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings
from app.exceptions.user_exceptions import ServiceUnavailableError

logger = logging.getLogger(__name__)

DATABASE_URL = settings.DATABASE_URL
if DATABASE_URL.startswith("sqlite:///"):
    DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

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

Base = declarative_base()


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
