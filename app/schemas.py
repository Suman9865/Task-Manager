from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import date
from typing import Optional
from enum import Enum

class TaskValidation(BaseModel):
    
    @field_validator("title", check_fields=False)
    @classmethod
    def validate_title(cls, value):
        if not value.strip():
            raise ValueError("Title cannot be empty")
        return value.strip()

    @field_validator("due_date", check_fields=False)
    @classmethod
    def validate_due_date(cls, value):
        if value is not None and value < date.today():
            raise ValueError("Due date cannot be in the past")
        return value
        
class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"
    
class TaskCreate(BaseModel):
    title: str = Field(min_length=1)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.pending
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value):
        if not value.strip():
            raise ValueError("Title cannot be empty")
        return value.strip()

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, value):
        if value is not None and value < date.today():
            raise ValueError("Due date cannot be in the past")
        return value


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    due_date: Optional[date]

    model_config = ConfigDict(from_attributes=True)

class TaskUpdate(BaseModel):
    title: str = Field(min_length=1)
    description: Optional[str] = None
    status: str
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value):
        if not value.strip():
            raise ValueError("Title cannot be empty")
        return value.strip()

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, value):
        if value is not None and value < date.today():
            raise ValueError("Due date cannot be in the past")
        return value


class TaskPatch(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value):
        if not value.strip():
            raise ValueError("Title cannot be empty")
        return value.strip()

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, value):
        if value is not None and value < date.today():
            raise ValueError("Due date cannot be in the past")
        return value