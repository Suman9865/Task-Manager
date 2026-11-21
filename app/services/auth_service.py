import logging

import anyio
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import UserCreate, LoginEmail
from app.repositories import user_repository
from app.core.security import hash_password, verify_password
from app.exceptions.user_exceptions import (
    InvalidEmailFormatError, UserAlreadyExistsError, InvalidCredentialsError,
)
from app.models.user import User
from app.core.token import create_access_token, create_refresh_token
from app.services.refresh_token_service import (
    store_refresh_token, validate_refresh_token, rotate_refresh_token, revoke_refresh_token,
)
from app.services.session_service import create_session, get_session, revoke_session

logger = logging.getLogger(__name__)

async def register_user(db: AsyncSession, user_data: UserCreate):
    if await user_repository.get_by_email(db, user_data.email):
        raise UserAlreadyExistsError("Email already registered")
    hashed_password = await anyio.to_thread.run_sync(hash_password, user_data.password)
    db_user = User(username=user_data.username, email=user_data.email, hashed_password=hashed_password)
    try:
        created_user = await user_repository.create(db, db_user)
        await db.commit()
        await db.refresh(created_user)
        logger.info("User registered successfully. ID: %s", created_user.id)
        return created_user
    except IntegrityError as exc:
        await db.rollback()
        raise UserAlreadyExistsError("A user with this email already exists") from exc
    except Exception:
        await db.rollback()
        logger.exception("User registration failed")
        raise

async def login_user(db: AsyncSession, email: str, password: str):
    try:
        email = LoginEmail(email=email).email
    except ValidationError as exc:
        raise InvalidEmailFormatError("Invalid email format") from exc
    user = await user_repository.get_by_email(db, email)
    if not user or not user.is_active:
        raise InvalidCredentialsError("Invalid email or password")
    valid_password = await anyio.to_thread.run_sync(verify_password, password, user.hashed_password)
    if not valid_password:
        raise InvalidCredentialsError("Invalid email or password")
    session_id = await create_session(user.id)
    access_token = create_access_token(user_id=user.id, session_id=session_id)
    refresh_token = create_refresh_token()
    await store_refresh_token(user.id, session_id, refresh_token)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

async def refresh_user_tokens(db: AsyncSession, old_refresh_token: str):
    token_data = await validate_refresh_token(old_refresh_token)
    if not token_data:
        raise InvalidCredentialsError("Invalid or expired refresh token")
    user_id = int(token_data["user_id"])
    session_id = token_data["session_id"]
    if token_data.get("reused"):
        # Reuse of a consumed token is evidence of replay: revoke the whole session.
        await revoke_session(session_id=session_id, user_id=user_id)
        raise InvalidCredentialsError("Refresh-token reuse detected; session revoked")
    session_data = await get_session(session_id)
    if not session_data or int(session_data["user_id"]) != user_id:
        raise InvalidCredentialsError("Invalid or expired session")
    user = await user_repository.get_by_id(db, user_id)
    if not user or not user.is_active:
        raise InvalidCredentialsError("Invalid refresh token")
    new_refresh_token = create_refresh_token()
    rotated_data = await rotate_refresh_token(old_refresh_token, new_refresh_token, session_id)
    if not rotated_data:
        # A concurrent refresh/logout may have consumed the token or revoked the session.
        replay_data = await validate_refresh_token(old_refresh_token)
        if replay_data and replay_data.get("reused"):
            await revoke_session(session_id=session_id, user_id=user_id)
            raise InvalidCredentialsError("Refresh-token reuse detected; session revoked")
        raise InvalidCredentialsError("Invalid or expired refresh token")
    access_token = create_access_token(
        user_id=int(rotated_data["user_id"]), session_id=rotated_data["session_id"]
    )
    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}

async def logout_user(refresh_token: str):
    token_data = await validate_refresh_token(refresh_token)
    if not token_data or token_data.get("reused"):
        raise InvalidCredentialsError("Invalid or expired refresh token")
    user_id = int(token_data["user_id"])
    session_id = token_data["session_id"]
    # Revoke the session first. Atomic Redis operations ensure a later refresh
    # sees no session and cannot mint another valid token.
    await revoke_session(session_id=session_id, user_id=user_id)
    await revoke_refresh_token(refresh_token)
    return {"message": "Logged out successfully"}
