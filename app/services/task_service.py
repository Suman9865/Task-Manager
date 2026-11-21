import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import (
    get_cache,
    invalidate_user_task_cache,
    set_cache,
)
from app.exceptions.task_exceptions import (
    TaskAlreadyExistsError,
    TaskDeletionError,
    TaskNotFoundError,
    TaskTitleChangeError,
)
from app.models.task import Task
from app.repositories import task_repository
from app.schemas import TaskCreate, TaskPatch, TaskResponse, TaskUpdate

logger = logging.getLogger(__name__)


async def create_task(
    db: AsyncSession, task_data: TaskCreate, user_id: int
):
    logger.info("Creating task for user ID %s", user_id)
    try:
        if await task_repository.get_by_title(db, task_data.title):
            raise TaskAlreadyExistsError(
                "A task with this title already exists"
            )

        db_task = Task(
            title=task_data.title,
            description=task_data.description,
            status=task_data.status,
            due_date=task_data.due_date,
            user_id=user_id,
        )
        created_task = await task_repository.create(db, db_task)
        await db.commit()
        await db.refresh(created_task)
    except IntegrityError as exc:
        await db.rollback()
        raise TaskAlreadyExistsError(
            "A task with this title already exists"
        ) from exc
    except Exception:
        await db.rollback()
        logger.exception("Task creation failed for user ID %s", user_id)
        raise

    await invalidate_user_task_cache(user_id)
    logger.info(
        "Task %s created successfully for user ID %s",
        created_task.id,
        user_id,
    )
    return created_task


async def get_tasks(
    db: AsyncSession,
    user_id: int,
    status: str | None = None,
    limit: int = 10,
    offset: int = 0,
):
    cache_key = f"tasks:user:{user_id}:list:{status}:{limit}:{offset}"
    cached_tasks = await get_cache(cache_key)
    if cached_tasks is not None:
        return [TaskResponse.model_validate(task) for task in cached_tasks]

    tasks = await task_repository.get_all(
        db=db,
        user_id=user_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    response = [TaskResponse.model_validate(task) for task in tasks]
    await set_cache(
        key=cache_key,
        value=[task.model_dump(mode="json") for task in response],
        ttl=60,
    )
    return response


async def get_task(task_id: int, db: AsyncSession, user_id: int):
    task = await task_repository.get_by_id(db, task_id, user_id)
    if task is None:
        raise TaskNotFoundError("Task not found")
    return task


async def update_task(
    db: AsyncSession, task_id: int, task_data: TaskUpdate, user_id: int
):
    task = await task_repository.get_by_id(db, task_id, user_id)
    if task is None:
        raise TaskNotFoundError("Task not found")
    if task_data.title != task.title:
        raise TaskTitleChangeError(
            f"The task title cannot be changed. Please use the correct title: '{task.title}'"
        )

    task.description = task_data.description
    task.status = task_data.status
    task.due_date = task_data.due_date
    try:
        await task_repository.save(db, task)
        await db.commit()
        await db.refresh(task)
    except IntegrityError as exc:
        await db.rollback()
        raise TaskAlreadyExistsError(
            "A task with this title already exists"
        ) from exc
    except Exception:
        await db.rollback()
        logger.exception("Task update failed: task_id=%s user_id=%s", task_id, user_id)
        raise

    await invalidate_user_task_cache(user_id, task_id)
    return task


async def patch_task(
    db: AsyncSession, task_id: int, task_data: TaskPatch, user_id: int
):
    task = await task_repository.get_by_id(db, task_id, user_id)
    if task is None:
        raise TaskNotFoundError("Task not found")

    update_data = task_data.model_dump(exclude_unset=True)
    if "title" in update_data and update_data["title"] != task.title:
        raise TaskTitleChangeError(
            f"The task title cannot be changed. Please use the correct title: '{task.title}'"
        )

    for key, value in update_data.items():
        setattr(task, key, value)

    try:
        await task_repository.save(db, task)
        await db.commit()
        await db.refresh(task)
    except IntegrityError as exc:
        await db.rollback()
        raise TaskAlreadyExistsError(
            "A task with this title already exists"
        ) from exc
    except Exception:
        await db.rollback()
        logger.exception("Task patch failed: task_id=%s user_id=%s", task_id, user_id)
        raise

    await invalidate_user_task_cache(user_id, task_id)
    return task


async def delete_task(db: AsyncSession, task_id: int, user_id: int):
    task = await task_repository.get_by_id(db, task_id, user_id)
    if task is None:
        raise TaskNotFoundError("Task not found")

    try:
        await task_repository.delete(db, task)
        await db.commit()
    except Exception as exc:
        await db.rollback()
        logger.exception("Task deletion failed: task_id=%s user_id=%s", task_id, user_id)
        raise TaskDeletionError("Unable to delete task") from exc

    await invalidate_user_task_cache(user_id, task_id)
    return {"message": "Task deleted successfully"}
