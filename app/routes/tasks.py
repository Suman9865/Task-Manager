from fastapi import APIRouter, Depends, HTTPException, Query
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
from app.exceptions.task_exceptions import (
    TaskAlreadyExistsError,
    TaskNotFoundError,
    TaskTitleChangeError,
    TaskDeletionError
)


router = APIRouter()

@router.post("/tasks", response_model=TaskResponse)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):

    try:
        return create_task_service(db, task)

    except TaskAlreadyExistsError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc)
        )

@router.get("/tasks", response_model=list[TaskResponse])
def get_tasks(
    status: str | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)):
    
    return get_tasks_service(db, status, limit, offset)

@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):

    try:
        return get_task_service(db, task_id)

    except TaskNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )

@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db)):
    try:
        return update_task_service(db, task_id, task_data)

    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    except TaskTitleChangeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except TaskAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def patch_task(task_id: int, task_data: TaskPatch, db: Session = Depends(get_db)):
    try:
        return patch_task_service(db, task_id, task_data)

    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    except TaskTitleChangeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except TaskAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):

    try:
        return delete_task_service(db, task_id)

    except TaskNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )

    except TaskDeletionError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc)
        )
