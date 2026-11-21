import pytest

from app.exceptions.task_exceptions import (
    TaskAlreadyExistsError,
    TaskNotFoundError,
    TaskTitleChangeError,
)
from app.models import Task, User
from app.schemas import TaskCreate, TaskPatch, TaskUpdate
from app.services import task_service


@pytest.mark.asyncio
async def test_create_task_and_reject_duplicate_title(db):
    user = User(
        username="service-user",
        email="service-user@example.com",
        hashed_password="hash",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    created = await task_service.create_task(
        db, TaskCreate(title="Service task"), user.id
    )
    assert created.id is not None
    assert created.user_id == user.id

    with pytest.raises(TaskAlreadyExistsError):
        await task_service.create_task(
            db, TaskCreate(title="Service task"), user.id
        )


@pytest.mark.asyncio
async def test_get_tasks_uses_cache(db):
    user = User(
        username="cache-user",
        email="cache-user@example.com",
        hashed_password="hash",
    )
    db.add(user)
    await db.flush()
    db.add(Task(title="Cached task", user_id=user.id))
    await db.commit()

    first = await task_service.get_tasks(db, user.id)
    second = await task_service.get_tasks(db, user.id)

    assert len(first) == 1
    assert first[0].title == "Cached task"
    assert second[0].title == "Cached task"


@pytest.mark.asyncio
async def test_get_task_raises_when_not_owned_or_missing(db):
    with pytest.raises(TaskNotFoundError):
        await task_service.get_task(9999, db, user_id=9999)


@pytest.mark.asyncio
async def test_update_task_persists_changes(db):
    user = User(
        username="update-user",
        email="update-user@example.com",
        hashed_password="hash",
    )
    db.add(user)
    await db.flush()
    task = Task(title="Update me", description="before", user_id=user.id)
    db.add(task)
    await db.commit()

    updated = await task_service.update_task(
        db,
        task.id,
        TaskUpdate(
            title="Update me",
            description="after",
            status="done",
        ),
        user.id,
    )
    assert updated.description == "after"
    assert updated.status == "done"


@pytest.mark.asyncio
async def test_update_task_rejects_title_change(db):
    user = User(
        username="immutable-user",
        email="immutable-user@example.com",
        hashed_password="hash",
    )
    db.add(user)
    await db.flush()
    task = Task(title="Original", user_id=user.id)
    db.add(task)
    await db.commit()

    with pytest.raises(TaskTitleChangeError):
        await task_service.update_task(
            db,
            task.id,
            TaskUpdate(title="Changed", status="pending"),
            user.id,
        )


@pytest.mark.asyncio
async def test_patch_task_persists_partial_changes(db):
    user = User(
        username="patch-user",
        email="patch-user@example.com",
        hashed_password="hash",
    )
    db.add(user)
    await db.flush()
    task = Task(title="Patch me", description="before", user_id=user.id)
    db.add(task)
    await db.commit()

    updated = await task_service.patch_task(
        db, task.id, TaskPatch(description="after", status="done"), user.id
    )
    assert updated.title == "Patch me"
    assert updated.description == "after"
    assert updated.status == "done"


@pytest.mark.asyncio
async def test_patch_task_rejects_title_change(db):
    user = User(
        username="patch-immutable-user",
        email="patch-immutable-user@example.com",
        hashed_password="hash",
    )
    db.add(user)
    await db.flush()
    task = Task(title="Original patch", user_id=user.id)
    db.add(task)
    await db.commit()

    with pytest.raises(TaskTitleChangeError):
        await task_service.patch_task(
            db, task.id, TaskPatch(title="Changed"), user.id
        )


@pytest.mark.asyncio
async def test_delete_task_removes_record(db):
    user = User(
        username="delete-user",
        email="delete-user@example.com",
        hashed_password="hash",
    )
    db.add(user)
    await db.flush()
    task = Task(title="Delete me", user_id=user.id)
    db.add(task)
    await db.commit()
    task_id = task.id

    result = await task_service.delete_task(db, task_id, user.id)

    assert result == {"message": "Task deleted successfully"}
    assert await db.get(Task, task_id) is None


@pytest.mark.asyncio
async def test_delete_task_missing_record_raises(db):
    with pytest.raises(TaskNotFoundError):
        await task_service.delete_task(db, 9999, 9999)
