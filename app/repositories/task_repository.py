
import logging

from sqlalchemy.orm import Session

from app.models import Task

logger = logging.getLogger(__name__)


def get_by_title(db: Session, title: str):
    logger.info("Fetching task by title: %s", title)

    task = db.query(Task).filter(
        Task.title == title
    ).first()

    if task:
        logger.info("Task found with title: %s", title)
    else:
        logger.info("No task found with title: %s", title)

    return task


def create(db: Session, task: Task):
    logger.info("Creating new task: %s", task.title)

    try:
        db.add(task)
        db.commit()
        db.refresh(task)

        logger.info("Task created successfully with ID: %s", task.id)

        return task

    except Exception:
        db.rollback()
        logger.exception("Failed to create task")
        raise


def get_all(
    db: Session,
    status: str | None = None,
    limit: int = 10,
    offset: int = 0
):
    logger.info(
        "Fetching tasks - status: %s, limit: %s, offset: %s",
        status,
        limit,
        offset
    )

    query = db.query(Task)

    if status:
        query = query.filter(Task.status == status)

    try:
        tasks = query.order_by(Task.id).offset(offset).limit(limit).all()

        logger.info("Successfully fetched %s tasks", len(tasks))

        return tasks

    except Exception:
        logger.exception("Failed to fetch tasks")
        raise


def get_by_id(db: Session, task_id: int):
    logger.info("Fetching task by ID: %s", task_id)

    task = db.query(Task).filter(
        Task.id == task_id
    ).first()

    if task:
        logger.info("Task found with ID: %s", task_id)
    else:
        logger.info("No task found with ID: %s", task_id)

    return task


def save(db: Session, task: Task):
    logger.info("Saving task with ID: %s", task.id)

    try:
        db.commit()
        db.refresh(task)

        logger.info("Task updated successfully with ID: %s", task.id)

        return task

    except Exception:
        db.rollback()
        logger.exception("Failed to update task with ID: %s", task.id)
        raise


def delete(db: Session, task: Task):
    logger.info("Deleting task with ID: %s", task.id)

    try:
        task_id = task.id

        db.delete(task)
        db.commit()

        logger.info("Task deleted successfully with ID: %s", task_id)

        return {
            "message": "Task deleted successfully",
            "task": task
        }

    except Exception:
        db.rollback()
        logger.exception("Failed to delete task with ID: %s", task.id)
        raise
