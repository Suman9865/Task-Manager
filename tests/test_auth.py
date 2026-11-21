import pytest

from app.core.security import hash_password
from app.models import User
from app.services import auth_service
from app.exceptions.user_exceptions import InvalidCredentialsError


@pytest.mark.asyncio
async def test_registration_and_login(client, db):
    registration = await client.post("/auth/register", json={
        "username": "auth-user", "email": "auth-user@example.com", "password": "StrongPassword123!"
    })
    assert registration.status_code == 200
    login = await client.post("/auth/login", data={
        "username": "auth-user@example.com", "password": "StrongPassword123!"
    })
    assert login.status_code == 200
    assert login.json()["access_token"]
    assert login.json()["refresh_token"]


@pytest.mark.asyncio
async def test_refresh_rotates_token_and_old_token_replay_revokes_session(client):
    registered = await client.post("/auth/register", json={
        "username": "replay-user", "email": "replay-user@example.com", "password": "StrongPassword123!"
    })
    assert registered.status_code == 200
    login = await client.post("/auth/login", data={
        "username": "replay-user@example.com", "password": "StrongPassword123!"
    })
    original = login.json()["refresh_token"]
    rotated = await client.post("/auth/refresh", json={"refresh_token": original})
    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != original

    replay = await client.post("/auth/refresh", json={"refresh_token": original})
    assert replay.status_code == 401
    assert "reuse detected" in replay.json()["detail"].lower()

    after_replay = await client.post("/auth/refresh", json={
        "refresh_token": rotated.json()["refresh_token"]
    })
    assert after_replay.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_session_and_refresh_token(client):
    await client.post("/auth/register", json={
        "username": "logout-user", "email": "logout-user@example.com", "password": "StrongPassword123!"
    })
    login = await client.post("/auth/login", data={
        "username": "logout-user@example.com", "password": "StrongPassword123!"
    })
    refresh_token = login.json()["refresh_token"]
    logout = await client.post("/auth/logout", json={"refresh_token": refresh_token})
    assert logout.status_code == 200
    assert logout.json()["message"] == "Logged out successfully"
    refreshed = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert refreshed.status_code == 401


@pytest.mark.asyncio
async def test_invalid_login_is_rejected(client):
    response = await client.post("/auth/login", data={
        "username": "missing@example.com", "password": "wrong"
    })
    assert response.status_code == 401
