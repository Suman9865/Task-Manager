from datetime import datetime, timedelta, timezone

import jwt
import secrets
import hashlib
from app.config import settings

def create_access_token(
    user_id: int,
    expires_delta: timedelta | None = None
) -> str:

    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload = {
        "sub": str(user_id),
        "exp": expire
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt

def create_refresh_token() -> str:
    return secrets.token_urlsafe(64)

def hash_refresh_token(refresh_token: str) -> str:
    return hashlib.sha256(
        refresh_token.encode("utf-8")
    ).hexdigest()

def validate_refresh_token(redis_client, refresh_token: str) -> str | None:
    hashed_token = hash_refresh_token(refresh_token)

    user_id = redis_client.get(
        f"refresh_token:{hashed_token}"
    )

    if not user_id:
        return None

    return user_id