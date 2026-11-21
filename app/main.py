import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.http_client import set_http_client
from app.core.redis import close_redis, get_redis
from app.database import engine, Base
from app.exceptions.task_exceptions import (
    TaskAlreadyExistsError, TaskNotFoundError, TaskTitleChangeError, TaskDeletionError,
)
from app.exceptions.user_exceptions import (
    InvalidCredentialsError, UserAlreadyExistsError, InvalidEmailFormatError,
    RateLimitExceededError, AuthenticationError, ServiceUnavailableError,
)
from app.logging_config import setup_logging
from app.routes.tasks import router as task_router
from app.middleware.request_id import RequestIDMiddleware
from app.routes.auth import router as auth_routes
from app.routes.weather import router as weather_routes

from app.models import Task, User  # noqa: F401

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Task Manager API application")
    try:
        if settings.AUTO_CREATE_SCHEMA:
            logger.warning(
                "AUTO_CREATE_SCHEMA is enabled; use Alembic migrations in production"
            )
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        ) as client:
            set_http_client(client)
            try:
                yield
            finally:
                set_http_client(None)
    finally:
        set_http_client(None)
        await close_redis()
        await engine.dispose()
        logger.info("Application resources closed")


app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, lifespan=lifespan)
app.add_middleware(RequestIDMiddleware)
app.include_router(task_router)
app.include_router(auth_routes)
app.include_router(weather_routes)


@app.exception_handler(TaskAlreadyExistsError)
async def task_already_exists_handler(request: Request, exc: TaskAlreadyExistsError):
    logger.warning("Duplicate task creation attempted: %s", exc)
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(request: Request, exc: TaskNotFoundError):
    logger.warning("Task not found: %s", exc)
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(TaskTitleChangeError)
async def task_title_change_handler(request: Request, exc: TaskTitleChangeError):
    logger.warning("Task title change failed: %s", exc)
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(TaskDeletionError)
async def task_deletion_handler(request: Request, exc: TaskDeletionError):
    logger.exception("Task deletion failed: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Unable to delete task"})


@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsError):
    logger.warning("Invalid credentials")
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(UserAlreadyExistsError)
async def user_already_exists_handler(request: Request, exc: UserAlreadyExistsError):
    logger.warning("Duplicate user registration attempted")
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(InvalidEmailFormatError)
async def invalid_email_format_handler(request: Request, exc: InvalidEmailFormatError):
    logger.warning("Invalid email format")
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(RateLimitExceededError)
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceededError):
    return JSONResponse(
        status_code=429,
        content={"detail": exc.message},
        headers={
            "Retry-After": str(exc.retry_after),
            "X-RateLimit-Limit": str(exc.limit),
            "X-RateLimit-Remaining": "0",
        },
    )


@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=401,
        content={"detail": exc.message},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(ServiceUnavailableError)
async def service_unavailable_handler(request: Request, exc: ServiceUnavailableError):
    logger.error("Service unavailable: %s", exc.message)
    return JSONResponse(
        status_code=503,
        content={"detail": exc.message},
        headers={"Retry-After": str(exc.retry_after)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unexpected application error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/")
async def home():
    return {"message": "Welcome to Task Manager API"}


@app.get("/health", tags=["Health"])
async def health():
    """Liveness probe: confirms the ASGI process is responsive."""
    return {"status": "healthy"}


@app.get("/ready", tags=["Health"])
async def readiness():
    """Readiness probe: checks the database and Redis dependencies."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        await get_redis().ping()
    except (SQLAlchemyError, RedisError) as exc:
        logger.warning("Readiness check failed: %s", type(exc).__name__)
        raise ServiceUnavailableError("Application dependencies are unavailable") from exc
    return {"status": "ready"}
