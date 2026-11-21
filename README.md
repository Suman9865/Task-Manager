# Task Manager API

Asynchronous REST API built with FastAPI, SQLAlchemy async sessions, Pydantic, Redis, and HTTPX.

## Architecture

- `app/routes`: HTTP endpoints and dependency wiring.
- `app/services`: business workflows.
- `app/repositories`: async database queries.
- `app/models`: SQLAlchemy ORM entities.
- `app/core`: configuration, security, Redis, cache, rate limiting, HTTP client.
- `app/external_apis`: external HTTP integrations.
- `app/schemas.py`: Pydantic request and response schemas.
- `tests`: async unit and API tests.

## Features

Async CRUD, per-user task ownership, JWT access and refresh tokens, Redis sessions/caching/rate limiting, geolocation and weather integrations, request IDs, centralized exception handling, health and readiness endpoints.

## Local setup

Python 3.13 and Redis are required. SQLite can be used locally; PostgreSQL is recommended for deployment.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Set a unique `SECRET_KEY` of at least 32 characters and configure `WEATHER_API_KEY`, `DATABASE_URL`, and `REDIS_URL`.

Run with `uvicorn app.main:app --reload`. API docs: `/docs`. Liveness: `/health`. Dependency readiness: `/ready`.

Run tests with `pytest -v --cov=app --cov-report=term-missing`.

## Proxy and client IP configuration

The application currently reads the direct ASGI peer address (`request.client.host`) for IP geolocation and IP-based authentication rate limiting. It does not trust `X-Forwarded-For` or other forwarded headers itself.

When deployed behind a reverse proxy, configure the ASGI server's proxy-header support and its trusted-proxy allowlist (for example, Uvicorn's `--proxy-headers` and `--forwarded-allow-ips`) to include only known proxy addresses or networks. Never trust forwarded headers from arbitrary clients or use `*` unless the network boundary guarantees that only trusted proxies can connect to the application. No deployment behavior is changed by this documentation.

Production database migration and deployment hardening remain in progress; this branch is not yet production-certified.
