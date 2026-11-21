import pytest

from app.models.task import Task
from app.repositories import task_repository


@pytest.mark.asyncio
async def test_async_task_repository_create_and_read(db):
    task = Task(title="Async repository test", description="created through AsyncSession")
    created = await task_repository.create(db, task)
    await db.commit()
    await db.refresh(created)

    fetched = await task_repository.get_by_id(db, created.id)
    assert fetched is not None
    assert fetched.title == "Async repository test"


@pytest.mark.asyncio
async def test_async_task_repository_list_by_user_and_status(db):
    first = Task(title="Pending task", status="pending", user_id=7)
    second = Task(title="Done task", status="done", user_id=7)
    third = Task(title="Other user's task", status="pending", user_id=8)
    db.add_all([first, second, third])
    await db.commit()

    tasks = await task_repository.get_all(db, user_id=7, status="pending")
    assert [task.title for task in tasks] == ["Pending task"]
