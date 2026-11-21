"""Backward-compatible imports for the SQLAlchemy model package.

New code should import from app.models or the specific app.models modules.
"""
from app.models import Task, User

__all__ = ["Task", "User"]
