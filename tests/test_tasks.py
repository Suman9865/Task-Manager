from datetime import date, timedelta

import pytest

from app.models.task import Task


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
        ("put", "/tasks/1", {"json": {
            "title": "Private task", "description": "updated",
            "status": "pending",
        }}),
        ("patch", "/tasks/1", {"json": {"description": "updated"}}),
        ("delete", "/tasks/1", {}),
    ],
)
async def test_all_task_endpoints_require_authentication(
    client, method, path, kwargs
):
    response = await getattr(client, method)(path, **kwargs)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_task_assigns_owner_and_list_is_user_scoped(
    authenticated_client, db
):
    client, user = authenticated_client
    response = await client.post(
        "/tasks",
        json={"title": "My private task", "status": "pending"},
    )
    assert response.status_code == 201
    created = response.json()

    stored_task = await db.get(Task, created["id"])
    assert stored_task is not None
    assert stored_task.user_id == user.id

    other_user_task = Task(
        title="Another user's task",
        status="pending",
        user_id=user.id + 100,
    )
    db.add(other_user_task)
    await db.commit()

    response = await client.get("/tasks")
    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["My private task"]


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path,kwargs", [
    ("get", "/tasks/{task_id}", {}),
    ("put", "/tasks/{task_id}", {"json": {
        "title": "Someone else's task", "description": "tamper",
        "status": "done",
    }}),
    ("patch", "/tasks/{task_id}", {"json": {"description": "tamper"}}),
    ("delete", "/tasks/{task_id}", {}),
])
async def test_user_cannot_read_or_mutate_another_users_task(
    authenticated_client, db, method, path, kwargs
):
    client, user = authenticated_client
    other_user_task = Task(
        title="Someone else's task",
        description="original",
        status="pending",
        user_id=user.id + 100,
    )
    db.add(other_user_task)
    await db.commit()
    await db.refresh(other_user_task)

    response = await getattr(client, method)(
        path.format(task_id=other_user_task.id), **kwargs
    )
    assert response.status_code == 404

    await db.refresh(other_user_task)
    assert other_user_task.description == "original"
    assert await db.get(Task, other_user_task.id) is not None


@pytest.mark.asyncio
async def test_task_status_and_due_date_validation(authenticated_client):
    client, _ = authenticated_client

    invalid_status = await client.post(
        "/tasks", json={"title": "Invalid status", "status": "blocked"}
    )
    assert invalid_status.status_code == 422

    past_due_date = await client.post(
        "/tasks",
        json={
            "title": "Past due task",
            "due_date": (date.today() - timedelta(days=1)).isoformat(),
        },
    )
    assert past_due_date.status_code == 422


@pytest.mark.asyncio
async def test_patch_does_not_allow_blank_title(authenticated_client):
    client, _ = authenticated_client
    created = await client.post("/tasks", json={"title": "Keep this title"})
    task_id = created.json()["id"]

    response = await client.patch(
        f"/tasks/{task_id}", json={"title": "   "}
    )
    assert response.status_code == 422
