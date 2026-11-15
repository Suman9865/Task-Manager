from pydantic import BaseModel, ConfigDict, Field, field_validator, EmailStr
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

class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    email: EmailStr = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Username cannot be empty")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        value = value.strip().lower()
        if not value:
            raise ValueError("Email cannot be empty")
        return value


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    email: EmailStr = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8)

class LoginEmail(BaseModel):
    email: EmailStr

class RefreshTokenRequest(BaseModel):
    refresh_token: str