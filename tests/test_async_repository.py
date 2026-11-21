import pytest

from app.models import Task, User
from app.repositories import task_repository


@pytest.mark.asyncio
async def test_async_task_repository_create_and_read(db):
    user = User(
        username="repository-user",
        email="repository-user@example.com",
        hashed_password="test-hash",
    )
    db.add(user)
    await db.flush()

    task = Task(
        title="Async repository test",
        description="created through AsyncSession",
        user_id=user.id,
    )
    created = await task_repository.create(db, task)
    await db.commit()
    await db.refresh(created)

    fetched = await task_repository.get_by_id(db, created.id, user.id)
    assert fetched is not None
    assert fetched.title == "Async repository test"


@pytest.mark.asyncio
async def test_async_task_repository_list_by_user_and_status(db):
    first_user = User(
        username="first",
        email="first@example.com",
        hashed_password="hash",
    )
    second_user = User(
        username="second",
        email="second@example.com",
        hashed_password="hash",
    )
    db.add_all([first_user, second_user])
    await db.flush()

    db.add_all([
        Task(title="Pending task", status="pending", user_id=first_user.id),
        Task(title="Done task", status="done", user_id=first_user.id),
        Task(title="Other user's task", status="pending", user_id=second_user.id),
    ])
    await db.commit()

    tasks = await task_repository.get_all(
        db, user_id=first_user.id, status="pending"
    )
    assert [task.title for task in tasks] == ["Pending task"]


@pytest.mark.asyncio
async def test_repository_does_not_return_another_users_task(db):
    owner = User(username="owner", email="owner@example.com", hashed_password="hash")
    other = User(username="other", email="other@example.com", hashed_password="hash")
    db.add_all([owner, other])
    await db.flush()

    task = Task(title="Private task", user_id=owner.id)
    db.add(task)
    await db.commit()

    assert await task_repository.get_by_id(db, task.id, other.id) is None


@pytest.mark.asyncio
async def test_same_task_title_is_allowed_for_different_users(db):
    first = User(username="first", email="first-title@example.com", hashed_password="hash")
    second = User(username="second", email="second-title@example.com", hashed_password="hash")
    db.add_all([first, second])
    await db.flush()

    db.add_all([
        Task(title="Shared title", user_id=first.id),
        Task(title="Shared title", user_id=second.id),
    ])
    await db.commit()

    tasks = await task_repository.get_all(db, user_id=first.id)
    assert [task.title for task in tasks] == ["Shared title"]
