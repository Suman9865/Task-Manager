import pytest

from app.models import Task, User
from app.repositories import task_repository


@pytest.mark.asyncio
async def test_async_task_repository_create_and_read(db):
    user = User(username="repo-user", email="repo-user@example.com", hashed_password="hash")
    db.add(user)
    await db.flush()
    task = Task(title="Async repository test", user_id=user.id)
    created = await task_repository.create(db, task)
    await db.commit()
    await db.refresh(created)

    fetched = await task_repository.get_by_id(db, created.id, user.id)
    assert fetched is not None
    assert fetched.title == "Async repository test"


@pytest.mark.asyncio
async def test_repository_list_is_scoped_by_user_and_status(db):
    owner = User(username="owner", email="owner@example.com", hashed_password="hash")
    other = User(username="other", email="other@example.com", hashed_password="hash")
    db.add_all([owner, other])
    await db.flush()
    db.add_all([
        Task(title="Pending", status="pending", user_id=owner.id),
        Task(title="Done", status="done", user_id=owner.id),
        Task(title="Other user's task", status="pending", user_id=other.id),
    ])
    await db.commit()

    result = await task_repository.get_all(db, owner.id, status="pending")
    assert [item.title for item in result] == ["Pending"]


@pytest.mark.asyncio
async def test_repository_hides_other_users_task(db):
    owner = User(username="owner", email="owner@example.com", hashed_password="hash")
    other = User(username="other", email="other@example.com", hashed_password="hash")
    db.add_all([owner, other])
    await db.flush()
    task = Task(title="Private", user_id=owner.id)
    db.add(task)
    await db.commit()

    assert await task_repository.get_by_id(db, task.id, other.id) is None


@pytest.mark.asyncio
async def test_title_uniqueness_is_per_user(db):
    first = User(username="first", email="first@example.com", hashed_password="hash")
    second = User(username="second", email="second@example.com", hashed_password="hash")
    db.add_all([first, second])
    await db.flush()
    db.add_all([
        Task(title="Same title", user_id=first.id),
        Task(title="Same title", user_id=second.id),
    ])
    await db.commit()
    assert len(await task_repository.get_all(db, first.id)) == 1
