"""SQLAlchemy ORM model registry."""

from app.models.task import Task
from app.models.user import User

__all__ = ["Task", "User"]
