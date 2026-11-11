
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models import Task
from app.schemas import TaskCreate, TaskUpdate, TaskPatch
from app.repositories import task_repository
from app.exceptions.task_exceptions import (
    TaskAlreadyExistsError,
    TaskNotFoundError,
    TaskTitleChangeError,
    TaskDeletionError
)


def create_task(db: Session, task_data: TaskCreate):

    # Check whether task title already exists
    existing_task = task_repository.get_by_title(
        db, task_data.title
    )

    if existing_task:
        raise TaskAlreadyExistsError(
            "A task with this title already exists"
        )

    # Convert Pydantic schema into SQLAlchemy model
    db_task = Task(
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        due_date=task_data.due_date
    )

    try:
        # Save task using repository
        return task_repository.create(db, db_task)

    except IntegrityError as exc:
        raise TaskAlreadyExistsError(
            "A task with this title already exists"
        ) from exc


def get_tasks(
    db: Session,
    status: str | None = None,
    limit: int = 10,
    offset: int = 0
):
    return task_repository.get_all(
        db=db,
        status=status,
        limit=limit,
        offset=offset
    )


def get_task(task_id: int, db: Session):

    # Find task by ID
    task = task_repository.get_by_id(db, task_id)

    # Check whether task exists
    if task is None:
        raise TaskNotFoundError("Task not found")

    return task

def update_task(db: Session, task_id: int, task_data: TaskUpdate):

    # Find the existing task
    task = task_repository.get_by_id(db, task_id)

    if task is None:
        raise TaskNotFoundError("Task not found")

    # Prevent changing the task title
    if task_data.title != task.title:
        raise TaskTitleChangeError(
            f"The task title cannot be changed. "
            f"Please use the correct title: '{task.title}'"
        )

    # Update task fields
    task.title = task_data.title
    task.description = task_data.description
    task.status = task_data.status
    task.due_date = task_data.due_date

    try:
        return task_repository.save(db, task)

    except IntegrityError as exc:
        raise TaskAlreadyExistsError(
            "A task with this title already exists"
        ) from exc


def patch_task(db: Session, task_id: int, task_data: TaskPatch):

    # Find the existing task
    task = task_repository.get_by_id(db, task_id)

    if task is None:
        raise TaskNotFoundError("Task not found")

    # Get only the fields provided by the user
    update_data = task_data.model_dump(exclude_unset=True)

    # Prevent changing the task title
    if "title" in update_data:
        if update_data["title"] != task.title:
            raise TaskTitleChangeError(
                f"The task title cannot be changed. "
                f"Please use the correct title: '{task.title}'"
            )

    # Update only the provided fields
    for key, value in update_data.items():
        setattr(task, key, value)

    try:
        return task_repository.save(db, task)

    except IntegrityError as exc:
        raise TaskAlreadyExistsError(
            "A task with this title already exists"
        ) from exc

def delete_task(db: Session, task_id: int):

    # Find the existing task
    task = task_repository.get_by_id(db, task_id)

    if task is None:
        raise TaskNotFoundError("Task not found")

    try:
        # Delete the task
        return task_repository.delete(db, task)

    except IntegrityError as exc:
        db.rollback()

        raise TaskDeletionError(
            "Unable to delete task"
        ) from exc
