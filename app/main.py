
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base
from app.exceptions import (
    TaskAlreadyExistsError,
    TaskNotFoundError,
    TaskTitleChangeError,
    TaskDeletionError,
)
from app.logging_config import setup_logging
from app.routes.tasks import router as task_router


# Initialize logging
setup_logging()

logger = logging.getLogger(__name__)


# Create database tables
Base.metadata.create_all(bind=engine)


# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG
)

logger.info("Task Manager API application initialized")


# Register task routes
app.include_router(task_router)


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


# ----------------------------------------
# Application Endpoints
# ----------------------------------------

@app.get("/")
def home():
    return {"message": "Welcome to Task Manager API"}


@app.get("/health")
def health():
    return {"status": "healthy"}
