from sqlalchemy import Column, Integer, String, Date, Index, Boolean, ForeignKey, CheckConstraint
from app.database import Base
from sqlalchemy.orm import relationship

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    status = Column(String, default="pending")
    due_date = Column(Date, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    owner = relationship("User", back_populates="tasks")

    __table_args__ = (
        Index("ix_tasks_status_due_date", "status", "due_date"),
        Index("ix_tasks_user_id", "user_id"),
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'done')",
            name="check_task_status"
        ),
    )

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")

    tasks = relationship("Task", back_populates="owner")