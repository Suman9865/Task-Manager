# app/models/task.py
from sqlalchemy import Column, Integer, String, Date, Index, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    status = Column(String, default="pending")
    due_date = Column(Date, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # String reference "User" avoids circular imports
    owner = relationship("User", back_populates="tasks")

    __table_args__ = (
        Index("ix_tasks_status_due_date", "status", "due_date"),
        Index("ix_tasks_user_id", "user_id"),
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'done')",
            name="check_task_status"
        ),
    )