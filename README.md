# Task Manager API

A RESTful Task Manager API built with **FastAPI, SQLAlchemy, and SQLite**, demonstrating REST fundamentals, clean architecture, dependency injection, validation, centralized exception handling, and automated testing.

## Tech Stack

- **Backend:** FastAPI
- **Database:** SQLite
- **ORM:** SQLAlchemy
- **Validation:** Pydantic
- **Configuration:** Pydantic Settings
- **Testing:** Pytest, FastAPI TestClient
- **Language:** Python

## Features

### Core Features
- Create, read, update, and delete tasks (CRUD).
- Filter tasks by status.
- Pagination using `limit` and `offset`.
- Input validation for task titles and due dates.
- Proper HTTP status codes and API responses.
- Centralized exception handling.
- Basic application logging.
- Automated API testing with pytest.

### Advanced Features
- **Layered Architecture:** Separate routes, services, repositories, database models, and schemas.
- **Domain Exceptions:** Custom exceptions such as `TaskNotFound` and `InvalidDueDate`.
- **Global Exception Handling:** Centralized error responses with request IDs.
- **Dependency Injection:** Manage database sessions and services using FastAPI `Depends`.
- **Application Settings:** Environment-based configuration using Pydantic Settings.
- **Request ID Middleware:** Track requests across application logs using `ContextVar`.
- **Health Check:** Dedicated `/health` endpoint.
- **Unit Testing:** Test business logic using a fake repository without requiring a database.
- **Integration Testing:** Test API endpoints using `TestClient` and dependency overrides.

## Project Architecture

```text
task-manager-api/
│
├── app/
│   ├── routes/
│   │   └── task_routes.py
│   ├── services/
│   │   └── task_service.py
│   ├── repositories/
│   │   └── task_repository.py
│   ├── models/
│   │   └── task.py
│   ├── db_models/
│   │   └── task.py
│   ├── exceptions/
│   │   └── domain_exceptions.py
│   ├── middleware/
│   │   └── request_id.py
│   ├── config/
│   │   └── settings.py
│   ├── database.py
│   └── main.py
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/tasks` | Create a task |
| GET | `/tasks` | Get all tasks |
| GET | `/tasks/{id}` | Get a task by ID |
| PUT | `/tasks/{id}` | Update a task |
| DELETE | `/tasks/{id}` | Delete a task |
| GET | `/health` | Check application health |

### Filtering and Pagination

```http
GET /tasks?status=done&limit=10&offset=0
```

## HTTP Status Codes

| Status Code | Description |
|---|---|
| 200 | Successful request |
| 201 | Resource created |
| 204 | Resource deleted |
| 404 | Resource not found |
| 422 | Validation error |
| 500 | Internal server error |

## Setup and Installation

**1. Clone the repository**

```bash
git clone <repository-url>
cd task-manager-api
```

**2. Create a virtual environment**

```bash
python -m venv venv
```

Activate it:

```bash
# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

Create a `.env` file using `.env.example` as a reference.

**5. Run the application**

```bash
uvicorn app.main:app --reload
```

## API Documentation

Once the application is running, access:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Health Check: `http://127.0.0.1:8000/health`

## Running Tests

Run all tests:

```bash
pytest -v
```

Run unit tests:

```bash
pytest tests/unit -v
```

Run integration tests:

```bash
pytest tests/integration -v
```

## Learning Objectives

This project focuses on building a strong foundation in backend development:

- REST API design and HTTP fundamentals.
- Clean and layered application architecture.
- Separation of business logic and database operations.
- Dependency injection and configuration management.
- Exception handling and structured logging.
- Database integration using SQLAlchemy.
- Unit and integration testing.
- Writing maintainable and scalable backend code.

## Project Completion Criteria

- All unit and integration tests pass.
- CRUD operations work correctly.
- API validation and exception handling work as expected.
- Every request has a traceable request ID.
- Business logic remains independent of FastAPI and the database.
- Swagger documentation clearly describes all endpoints.
