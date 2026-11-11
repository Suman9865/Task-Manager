
from sqlalchemy.orm import Session

from app.models import Task


def get_by_title(db: Session, title: str):
    return db.query(Task).filter(
        Task.title == title
    ).first()


def create(db: Session, task: Task):
    try:
        db.add(task)
        db.commit()
        db.refresh(task)

        return task

    except Exception:
        db.rollback()
        raise


def get_all(
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

def get_by_id(db: Session, task_id: int):
    return db.query(Task).filter(
        Task.id == task_id
    ).first()

def save(db: Session, task: Task):
    try:
        db.commit()
        db.refresh(task)

        return task

    except Exception:
        db.rollback()
        raise

def delete(db: Session, task: Task):
    try:
        db.delete(task)
        db.commit()

        return {
            "message": "Task deleted successfully",
            "task": task
        }

    except Exception:
        db.rollback()
        raise

