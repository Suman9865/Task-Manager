import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task

logger = logging.getLogger(__name__)


async def get_by_title(db: AsyncSession, title: str):
    result = await db.execute(select(Task).where(Task.title == title))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, task: Task):
    db.add(task)
    await db.flush()
    return task


async def get_all(db: AsyncSession, user_id: int, status: str | None = None, limit: int = 10, offset: int = 0):
    query = select(Task).where(Task.user_id == user_id)
    if status:
        query = query.where(Task.status == status)
    result = await db.execute(query.order_by(Task.id).offset(offset).limit(limit))
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, task_id: int):
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()


async def save(db: AsyncSession, task: Task):
    try:
        await db.commit()
        await db.refresh(task)
        return task
    except Exception:
        await db.rollback()
        logger.exception("Failed to save task ID %s", task.id)
        raise


async def delete(db: AsyncSession, task: Task):
    try:
        await db.delete(task)
        await db.commit()
        return {"message": "Task deleted successfully", "task": task}
    except Exception:
        await db.rollback()
        logger.exception("Failed to delete task ID %s", task.id)
        raise
