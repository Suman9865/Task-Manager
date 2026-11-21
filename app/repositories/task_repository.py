from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task


async def get_by_title(db: AsyncSession, title: str, user_id: int) -> Task | None:
    result = await db.execute(
        select(Task).where(Task.title == title, Task.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create(db: AsyncSession, task: Task) -> Task:
    db.add(task)
    await db.flush()
    return task


async def get_all(
    db: AsyncSession,
    user_id: int,
    status: str | None = None,
    limit: int = 10,
    offset: int = 0,
) -> list[Task]:
    query = select(Task).where(Task.user_id == user_id)
    if status is not None:
        query = query.where(Task.status == status)
    result = await db.execute(
        query.order_by(Task.id).offset(offset).limit(limit)
    )
    return list(result.scalars().all())


async def get_by_id(
    db: AsyncSession, task_id: int, user_id: int
) -> Task | None:
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def save(db: AsyncSession, task: Task) -> Task:
    await db.flush()
    return task


async def delete(db: AsyncSession, task: Task) -> None:
    await db.delete(task)
    await db.flush()
