
import logging

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

logger = logging.getLogger(__name__)


def create_task(db: Session, task_data: TaskCreate):

    logger.info("Processing task creation request")

    # Check whether task title already exists
    existing_task = task_repository.get_by_title(
        db, task_data.title
    )

    if existing_task:
        logger.warning(
            "Task creation rejected: title already exists - %s",
            task_data.title
        )
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
        created_task = task_repository.create(db, db_task)

        logger.info(
            "Task creation completed with ID: %s",
            created_task.id
        )

        return created_task

    except IntegrityError as exc:
        logger.warning(
            "Task creation failed due to a database integrity constraint"
        )
        raise TaskAlreadyExistsError(
            "A task with this title already exists"
        ) from exc


def get_tasks(
    db: Session,
    status: str | None = None,
    limit: int = 10,
    offset: int = 0
):

    logger.info(
        "Processing task list request - status: %s, limit: %s, offset: %s",
        status,
        limit,
        offset
    )

    return task_repository.get_all(
        db=db,
        status=status,
        limit=limit,
        offset=offset
    )


def get_task(task_id: int, db: Session):

    logger.info(
        "Processing request to fetch task with ID: %s",
        task_id
    )

    # Find task by ID
    task = task_repository.get_by_id(db, task_id)

    # Check whether task exists
    if task is None:
        logger.warning("Task not found with ID: %s", task_id)
        raise TaskNotFoundError("Task not found")

    return task


def update_task(db: Session, task_id: int, task_data: TaskUpdate):

    logger.info("Processing update request for task ID: %s", task_id)

    # Find the existing task
    task = task_repository.get_by_id(db, task_id)

    if task is None:
        logger.warning("Task update failed: task ID %s not found", task_id)
        raise TaskNotFoundError("Task not found")

    # Prevent changing the task title
    if task_data.title != task.title:
        logger.warning(
            "Task update rejected: title change attempted for task ID %s",
            task_id
        )
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
        updated_task = task_repository.save(db, task)

        logger.info("Task updated successfully with ID: %s", task_id)

        return updated_task

    except IntegrityError as exc:
        raise TaskAlreadyExistsError(
            "A task with this title already exists"
        ) from exc


def patch_task(db: Session, task_id: int, task_data: TaskPatch):

    logger.info("Processing partial update request for task ID: %s", task_id)

    # Find the existing task
    task = task_repository.get_by_id(db, task_id)

    if task is None:
        logger.warning("Task patch failed: task ID %s not found", task_id)
        raise TaskNotFoundError("Task not found")

    # Get only the fields provided by the user
    update_data = task_data.model_dump(exclude_unset=True)

    # Prevent changing the task title
    if "title" in update_data:
        if update_data["title"] != task.title:
            logger.warning(
                "Task patch rejected: title change attempted for task ID %s",
                task_id
            )
            raise TaskTitleChangeError(
                f"The task title cannot be changed. "
                f"Please use the correct title: '{task.title}'"
            )

    # Update only the provided fields
    for key, value in update_data.items():
        setattr(task, key, value)

    try:
        updated_task = task_repository.save(db, task)

        logger.info("Task patched successfully with ID: %s", task_id)

        return updated_task

    except IntegrityError as exc:
        raise TaskAlreadyExistsError(
            "A task with this title already exists"
        ) from exc


def delete_task(db: Session, task_id: int):

    logger.info("Processing deletion request for task ID: %s", task_id)

    # Find the existing task
    task = task_repository.get_by_id(db, task_id)

    if task is None:
        logger.warning("Task deletion failed: task ID %s not found", task_id)
        raise TaskNotFoundError("Task not found")

    try:
        # Delete the task
        result = task_repository.delete(db, task)

        logger.info("Task deleted successfully with ID: %s", task_id)

        return result

    except IntegrityError as exc:
        db.rollback()

        logger.error(
            "Task deletion failed due to database integrity error. ID: %s",
            task_id
        )

        raise TaskDeletionError(
            "Unable to delete task"
        ) from exc
