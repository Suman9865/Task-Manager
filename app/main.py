from fastapi import FastAPI, Depends
from app.schemas import TaskCreate, TaskResponse
from app.database import engine, Base, get_db
from app.models import Task
from sqlalchemy.orm import Session

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Manager API")

@app.get("/")
def home():
    return {"message": "Welcome to Task Manager API"}

@app.post("/tasks", response_model=TaskResponse)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):

    # Convert Pydantic schema into SQLAlchemy model
    db_task = Task(
        title=task.title,
        description=task.description,
        status=task.status,
        due_date=task.due_date
    )

    # Save task to database
    db.add(db_task)
    db.commit()

    # Get the newly generated database ID
    db.refresh(db_task)

    return db_task

@app.get("/health")
def health():
    return {"status": "healthy"}