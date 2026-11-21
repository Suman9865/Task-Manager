
import logging

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.schemas import TaskCreate, TaskResponse, TaskUpdate, TaskPatch, TaskIPResponse
from app.database import get_db
from app.services.geolocation_service import get_ip_location
from app.services.task_service import (
    create_task as create_task_service,
    get_tasks as get_tasks_service,
    get_task as get_task_service,
    update_task as update_task_service,
    patch_task as patch_task_service,
    delete_task as delete_task_service,
)

from app.models.user import User
from app.core.dependencies import get_current_user
from app.core.rate_limit_dependencies import rate_limit_dependency

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Tasks"])


@router.post("/tasks", response_model=TaskIPResponse)
def create_task(task: TaskCreate, request: Request,db: Session = Depends(get_db)):

    logger.info("POST /tasks - Request received")
    client_ip = request.client.host if request.client else None

    logger.info("Client IP: %s", client_ip)

    # Get country and city using the geolocation service
    location = get_ip_location(client_ip) if client_ip else {
        "country": None,
        "city": None
    }

    logger.info(
        "Client location - Country: %s, City: %s",
        location["country"],
        location["city"]
    )

    created_task = create_task_service(db, task)

    return {
        "id": created_task.id,
        "title": created_task.title,
        "description": created_task.description,
        "status": created_task.status,
        "due_date": created_task.due_date,
        "country": location["country"],
        "city": location["city"]
    }


@router.get("/tasks", response_model=list[TaskResponse])
def get_tasks(
    status: str | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    rate_info: dict = Depends(rate_limit_dependency),
    db: Session = Depends(get_db)
):

    logger.info("GET /tasks - Request received")

    return get_tasks_service(db, status, limit, offset, current_user.id)


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):

    logger.info("GET /tasks/%s - Request received", task_id)

    return get_task_service(db, task_id)


@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db)
):

    logger.info("PUT /tasks/%s - Request received", task_id)

    return update_task_service(db, task_id, task_data)


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def patch_task(
    task_id: int,
    task_data: TaskPatch,
    db: Session = Depends(get_db)
):

    logger.info("PATCH /tasks/%s - Request received", task_id)

    return patch_task_service(db, task_id, task_data)


@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):

    logger.info("DELETE /tasks/%s - Request received", task_id)

    return delete_task_service(db, task_id)
