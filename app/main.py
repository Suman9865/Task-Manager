from fastapi import FastAPI, Depends, HTTPException, Query
from app.schemas import TaskCreate, TaskResponse, TaskUpdate, TaskPatch
from app.database import engine, Base, get_db
from app.models import Task
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Manager API")

@app.get("/")
def home():
    return {"message": "Welcome to Task Manager API"}

@app.post("/tasks", response_model=TaskResponse)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):

    # Check whether task title already exists
    existing_task = db.query(Task).filter(
        Task.title == task.title
    ).first()

    if existing_task:
        raise HTTPException(
            status_code=409,
            detail="A task with this title already exists"
        )

    # Convert Pydantic schema into SQLAlchemy model
    db_task = Task(
        title=task.title,
        description=task.description,
        status=task.status,
        due_date=task.due_date
    )

    try:
        # Save task to database
        db.add(db_task)
        db.commit()

        # Get the newly generated database ID
        db.refresh(db_task)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="A task with this title already exists"
        )

    return db_task

@app.get("/tasks", response_model=list[TaskResponse])
def get_tasks(
    status: str | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(Task)

    # Filter by status
    if status:
        query = query.filter(Task.status == status)

    # Apply pagination
    tasks = query.order_by(Task.id).offset(offset).limit(limit).all()

    return tasks

@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):

    # Find task by ID
    task = db.query(Task).filter(Task.id == task_id).first()

    # Check whether task exists
    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return task

@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_data: TaskUpdate, db: Session = Depends(get_db)):

    # Find the existing task
    task = db.query(Task).filter(Task.id == task_id).first()

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    # Check if the user is trying to change the title
    if task_data.title != task.title:
        raise HTTPException(
            status_code=400,
            detail=f"The task title cannot be changed. Please use the correct title: '{task.title}'"
        )

    # Check whether another task already uses this title
    existing_task = db.query(Task).filter(
        Task.title == task_data.title,
        Task.id != task_id
    ).first()

    if existing_task:
        raise HTTPException(
            status_code=409,
            detail="A task with this title already exists"
        )

    # Update the task fields
    task.title = task_data.title
    task.description = task_data.description
    task.status = task_data.status
    task.due_date = task_data.due_date

    try:
        db.commit()
        db.refresh(task)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="A task with this title already exists"
        )

    return task

@app.patch("/tasks/{task_id}", response_model=TaskResponse)
def patch_task(task_id: int, task_data: TaskPatch, db: Session = Depends(get_db)):

    # Find the existing task using ID
    task = db.query(Task).filter(Task.id == task_id).first()

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    # Get only the fields provided by the user
    update_data = task_data.model_dump(exclude_unset=True)

    # If title is provided, it must match the existing title
    if "title" in update_data:

        if update_data["title"] != task.title:
            raise HTTPException(
                status_code=400,
                detail=f"The task title cannot be changed. Please use the correct title: '{task.title}'"
            )

    # Update only the provided fields
    for key, value in update_data.items():
        setattr(task, key, value)

    try:
        db.commit()
        db.refresh(task)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="A task with this title already exists"
        )

    return task


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):

    # Find the existing task using ID
    task = db.query(Task).filter(Task.id == task_id).first()

    # Check whether task exists
    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    try:
        # Delete the task
        db.delete(task)

        # Save changes to database
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Unable to delete task"
        )

    return {
        "message": "Task deleted successfully",
        "task": task
    }

@app.get("/health")
def health():
    return {"status": "healthy"}