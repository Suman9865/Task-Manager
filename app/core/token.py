from datetime import datetime, timedelta, timezone

import jwt

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