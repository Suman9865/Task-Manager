
import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.schemas import TaskCreate, TaskResponse, TaskUpdate, TaskPatch
from app.database import get_db

from app.services.task_service import (
    create_task as create_task_service,
    get_tasks as get_tasks_service,
    get_task as get_task_service,
    update_task as update_task_service,
    patch_task as patch_task_service,
    delete_task as delete_task_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/tasks", response_model=TaskResponse)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):

    logger.info("POST /tasks - Request received")

    return create_task_service(db, task)


@router.get("/tasks", response_model=list[TaskResponse])
def get_tasks(
    status: str | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):

    logger.info("GET /tasks - Request received")

    return get_tasks_service(db, status, limit, offset)


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
