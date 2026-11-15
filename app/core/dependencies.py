import logging

import jwt
from jwt.exceptions import InvalidTokenError

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.user import User
from app.repositories import user_repository
from app.services.session_service import get_session
from app.exceptions.user_exceptions import AuthenticationError

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:

    try:
        # 1. Decode and verify JWT
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # 2. Extract user ID and session ID
        user_id = payload.get("sub")
        session_id = payload.get("sid")

        if not user_id or not session_id:
            raise AuthenticationError()

        user_id = int(user_id)

    except (InvalidTokenError, ValueError, TypeError):
        logger.warning("JWT validation failed")
        raise AuthenticationError()

    # 3. Validate Redis session
    session_data = get_session(session_id)

    if not session_data:
        raise AuthenticationError("Session expired or invalid")

    # 4. Verify session ownership
    if int(session_data["user_id"]) != user_id:
        raise AuthenticationError("Invalid session")

    # 5. Retrieve user
    user = user_repository.get_by_id(db, user_id)

    if not user or not user.is_active:
        raise AuthenticationError("Invalid user or inactive account")

    return user