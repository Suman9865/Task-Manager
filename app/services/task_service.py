
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models import Task
from app.schemas import TaskCreate, TaskResponse, TaskUpdate, TaskPatch


class TaskAlreadyExistsError(Exception):
    pass

class TaskNotFoundError(Exception):
    pass

class TaskTitleChangeError(Exception):
    pass

class TaskDeletionError(Exception):
    pass

def create_task(db: Session, task_data: TaskCreate):

    # Check whether task title already exists
    existing_task = db.query(Task).filter(
        Task.title == task_data.title
    ).first()

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
        # Save task to database
        db.add(db_task)
        db.commit()
        db.refresh(db_task)

    except IntegrityError as exc:
        db.rollback()

        raise TaskAlreadyExistsError(
            "A task with this title already exists"
        ) from exc

    return db_task

def get_tasks(
    db: Session,
    status: str | None = None,
    limit: int = 10,
    offset: int = 0
):
    query = db.query(Task)

    # Filter by status
    if status:
        query = query.filter(Task.status == status)

    # Apply pagination
    tasks = query.order_by(Task.id).offset(offset).limit(limit).all()

    return tasks

def get_task(task_id: int, db: Session):

    # Find task by ID
    task = db.query(Task).filter(Task.id == task_id).first()

    # Check whether task exists
    if task is None:
        raise TaskNotFoundError("Task not found")

    return task

def update_task(db: Session, task_id: int, task_data: TaskUpdate):

    # Find the existing task
    task = db.query(Task).filter(Task.id == task_id).first()

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
        db.commit()
        db.refresh(task)

    except IntegrityError as exc:
        db.rollback()
        raise TaskAlreadyExistsError(
            "A task with this title already exists"
        ) from exc

    return task


def patch_task(db: Session, task_id: int, task_data: TaskPatch):

    # Find the existing task
    task = db.query(Task).filter(Task.id == task_id).first()

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
        db.commit()
        db.refresh(task)

    except IntegrityError as exc:
        db.rollback()
        raise TaskAlreadyExistsError(
            "A task with this title already exists"
        ) from exc

    return task

def delete_task(db: Session, task_id: int):

    # Find the existing task
    task = db.query(Task).filter(Task.id == task_id).first()

    if task is None:
        raise TaskNotFoundError("Task not found")

    try:
        # Delete the task
        db.delete(task)

        # Save changes to database
        db.commit()

    except IntegrityError as exc:
        db.rollback()

        raise TaskDeletionError(
            "Unable to delete task"
        ) from exc

    return {
        "message": "Task deleted successfully",
        "task": task
    }
