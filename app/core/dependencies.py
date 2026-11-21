import logging

import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.config import settings
from app.models.user import User
from app.repositories import user_repository
from app.services.session_service import get_session
from app.exceptions.user_exceptions import AuthenticationError, ServiceUnavailableError

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        session_id = payload.get("sid")
        if not user_id or not session_id:
            raise AuthenticationError()
        user_id = int(user_id)
    except (InvalidTokenError, ValueError, TypeError):
        logger.warning("JWT validation failed")
        raise AuthenticationError()

    try:
        session_data = await get_session(session_id)
    except RedisError as exc:
        logger.exception("Redis unavailable during session validation")
        raise ServiceUnavailableError("Authentication service temporarily unavailable") from exc

    if not session_data:
        raise AuthenticationError("Session expired or invalid")
    if int(session_data["user_id"]) != user_id:
        raise AuthenticationError("Invalid session")

    user = await user_repository.get_by_id(db, user_id)
    if not user or not user.is_active:
        raise AuthenticationError("Invalid user or inactive account")
    return user
