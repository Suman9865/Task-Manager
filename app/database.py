from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

import logging

from sqlalchemy.exc import (
    OperationalError,
    DBAPIError,
    TimeoutError as SQLAlchemyTimeoutError
)

from app.exceptions.user_exceptions import ServiceUnavailableError

logger = logging.getLogger(__name__)

# Database URL
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Create database engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create database session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for database models
Base = declarative_base()

def get_db():
    db = SessionLocal()

    try:
        yield db

    except (OperationalError, SQLAlchemyTimeoutError) as exc:
        db.rollback()

        logger.exception("Database is unavailable")

        raise ServiceUnavailableError(
            "Database temporarily unavailable"
        ) from exc

    except DBAPIError as exc:
        db.rollback()

        if exc.connection_invalidated:
            logger.exception("Database connection was lost")

            raise ServiceUnavailableError(
                "Database temporarily unavailable"
            ) from exc

        raise

    finally:
        db.close()