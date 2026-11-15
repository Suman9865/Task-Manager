
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.database import engine, Base
from app.exceptions.task_exceptions import (
    TaskAlreadyExistsError,
    TaskNotFoundError,
    TaskTitleChangeError,
    TaskDeletionError,
)
from app.exceptions.user_exceptions import InvalidCredentialsError, UserAlreadyExistsError, InvalidEmailFormatError, RateLimitExceededError, AuthenticationError
from app.logging_config import setup_logging
from app.routes.tasks import router as task_router
from app.middleware.request_id import RequestIDMiddleware
from app.routes.auth import router as auth_routes

# Initialize logging
setup_logging()

logger = logging.getLogger(__name__)


# ----------------------------------------
# Lifespan Management
# ----------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    # Startup
    logger.info("Starting Task Manager API application")

    Base.metadata.create_all(bind=engine)

    logger.info("Database tables initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down Task Manager API application")

    engine.dispose()

    logger.info("Database connections closed successfully")


# ----------------------------------------
# Initialize FastAPI Application
# ----------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan
)


# Register middleware
app.add_middleware(RequestIDMiddleware)


# Register task routes
app.include_router(task_router)

# Register authentication routes
app.include_router(auth_routes)

# ----------------------------------------
# Global Exception Handlers
# ----------------------------------------

@app.exception_handler(TaskAlreadyExistsError)
async def task_already_exists_handler(
    request: Request,
    exc: TaskAlreadyExistsError
):
    logger.warning("Duplicate task creation attempted: %s", exc)

    return JSONResponse(
        status_code=409,
        content={"detail": str(exc)}
    )


@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(
    request: Request,
    exc: TaskNotFoundError
):
    logger.warning("Task not found: %s", exc)

    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)}
    )


@app.exception_handler(TaskTitleChangeError)
async def task_title_change_handler(
    request: Request,
    exc: TaskTitleChangeError
):
    logger.warning("Task title change failed: %s", exc)

    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )


@app.exception_handler(TaskDeletionError)
async def task_deletion_handler(
    request: Request,
    exc: TaskDeletionError
):
    logger.exception("Task deletion failed: %s", exc)

    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )


# Handle unexpected exceptions
@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception
):
    logger.exception("Unexpected application error: %s", exc)

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsError):
    logger.warning("Invalid login attempt: %s", exc)
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)}
    )


@app.exception_handler(UserAlreadyExistsError)
async def user_already_exists_handler(
    request: Request,
    exc: UserAlreadyExistsError
):
    logger.warning("Duplicate user registration attempted: %s", exc)

    return JSONResponse(
        status_code=409,
        content={"detail": str(exc)}
    )

@app.exception_handler(InvalidEmailFormatError)
async def invalid_email_format_handler(
    request: Request,
    exc: InvalidEmailFormatError
):
    logger.warning("Invalid email format: %s", exc)

    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)}
    )

@app.exception_handler(RateLimitExceededError)
async def rate_limit_exception_handler(
    request: Request,
    exc: RateLimitExceededError
):
    return JSONResponse(
        status_code=429,
        content={
            "detail": exc.message
        },
        headers={
            "Retry-After": str(exc.retry_after),
            "X-RateLimit-Limit": str(exc.limit),
            "X-RateLimit-Remaining": "0"
        }
    )

@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=401,
        content={"detail": exc.message},
        headers={"WWW-Authenticate": "Bearer"}
    )


# ----------------------------------------
# Application Endpoints
# ----------------------------------------

@app.get("/")
def home():
    return {"message": "Welcome to Task Manager API"}


@app.get("/health")
def health():
    return {"status": "healthy"}
