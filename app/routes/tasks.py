import asyncio
import logging

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.rate_limit_dependencies import rate_limit_dependency
from app.database import get_db
from app.models.user import User
from app.schemas import (
    TaskCreate,
    TaskIPResponse,
    TaskPatch,
    TaskResponse,
    TaskStatus,
    TaskUpdate,
)
from app.services.geolocation_service import get_ip_location
from app.services.task_service import (
    create_task as create_task_service,
    delete_task as delete_task_service,
    get_task as get_task_service,
    get_tasks as get_tasks_service,
    patch_task as patch_task_service,
    update_task as update_task_service,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Tasks"])


@router.post("/tasks", response_model=TaskIPResponse, status_code=201)
async def create_task(
    task: TaskCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else None
    if client_ip:
        location, created_task = await asyncio.gather(
            get_ip_location(client_ip),
            create_task_service(db, task, current_user.id),
        )
    else:
        location = {"country": None, "city": None}
        created_task = await create_task_service(db, task, current_user.id)

    return {
        "id": created_task.id,
        "title": created_task.title,
        "description": created_task.description,
        "status": created_task.status,
        "due_date": created_task.due_date,
        "country": location["country"],
        "city": location["city"],
    }


@router.get("/tasks", response_model=list[TaskResponse])
async def get_tasks(
    status: TaskStatus | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    rate_info: dict = Depends(rate_limit_dependency),
    db: AsyncSession = Depends(get_db),
):
    return await get_tasks_service(
        db, current_user.id, status, limit, offset
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_task_service(task_id, db, current_user.id)


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await update_task_service(db, task_id, task_data, current_user.id)


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def patch_task(
    task_id: int,
    task_data: TaskPatch,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await patch_task_service(db, task_id, task_data, current_user.id)


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await delete_task_service(db, task_id, current_user.id)
