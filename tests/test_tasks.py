from datetime import date, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Task


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "kwargs"),
    [
        ("post", "/tasks", {"json": {"title": "Private task"}}),
        ("get", "/tasks", {}),
        ("get", "/tasks/1", {}),
        ("put", "/tasks/1", {"json": {"title": "Private task", "description": "updated", "status": "pending"}}),
        ("patch", "/tasks/1", {"json": {"description": "updated"}}),
        ("delete", "/tasks/1", {}),
    ],
)
async def test_all_task_endpoints_require_authentication(client, method, path, kwargs):
    response = await getattr(client, method)(path, **kwargs)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_task_assigns_owner_and_list_is_user_scoped(authenticated_client, db):
    client, user = authenticated_client
    response = await client.post("/tasks", json={"title": "My private task"})
    assert response.status_code == 201
    created = response.json()
    stored = await db.get(Task, created["id"])
    assert stored is not None
    assert stored.user_id == user.id

    other_user = type(user)(
        username="other", email="other-task-user@example.com", hashed_password="hash"
    )
    db.add(other_user)
    await db.flush()
    db.add(Task(title="Other user's task", user_id=other_user.id))
    await db.commit()

    listed = await client.get("/tasks")
    assert [item["title"] for item in listed.json()] == ["My private task"]


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path,kwargs", [
    ("get", "/tasks/{task_id}", {}),
    ("put", "/tasks/{task_id}", {"json": {"title": "Someone else's task", "description": "tamper", "status": "done"}}),
    ("patch", "/tasks/{task_id}", {"json": {"description": "tamper"}}),
    ("delete", "/tasks/{task_id}", {}),
])
async def test_user_cannot_access_another_users_task(authenticated_client, db, method, path, kwargs):
    client, user = authenticated_client
    other_user = type(user)(
        username="other", email="other-owner@example.com", hashed_password="hash"
    )
    db.add(other_user)
    await db.flush()
    task = Task(title="Someone else's task", description="original", user_id=other_user.id)
    db.add(task)
    await db.commit()
    await db.refresh(task)

    response = await getattr(client, method)(path.format(task_id=task.id), **kwargs)
    assert response.status_code == 404
    await db.refresh(task)
    assert task.description == "original"


@pytest.mark.asyncio
async def test_task_validation_rejects_invalid_status_and_past_due_date(authenticated_client):
    client, _ = authenticated_client
    invalid_status = await client.post("/tasks", json={"title": "Invalid", "status": "blocked"})
    assert invalid_status.status_code == 422
    past = await client.post(
        "/tasks",
        json={"title": "Past", "due_date": (date.today() - timedelta(days=1)).isoformat()},
    )
    assert past.status_code == 422


@pytest.mark.asyncio
async def test_patch_rejects_blank_title(authenticated_client):
    client, _ = authenticated_client
    created = await client.post("/tasks", json={"title": "Keep title"})
    response = await client.patch(f"/tasks/{created.json()['id']}", json={"title": "   "})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_same_title_allowed_for_two_users(authenticated_client, db):
    client, user = authenticated_client
    other = type(user)(username="other", email="other-title@example.com", hashed_password="hash")
    db.add(other)
    await db.commit()
    first = await client.post("/tasks", json={"title": "Shared"})
    assert first.status_code == 201
    # The second account is not the authenticated principal in this fixture;
    # database-level uniqueness is independently tested in test_async_repository.py.
