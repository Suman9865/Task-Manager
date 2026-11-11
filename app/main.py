from fastapi import FastAPI

from app.database import engine, Base
from app.routes.tasks import router as task_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Manager API")

# Register task routes
app.include_router(task_router)


@app.get("/")
def home():
    return {"message": "Welcome to Task Manager API"}


@app.get("/health")
def health():
    return {"status": "healthy"}