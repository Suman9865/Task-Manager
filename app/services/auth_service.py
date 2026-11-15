
import logging

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.schemas import UserCreate, LoginEmail
from app.repositories import user_repository
from app.core.security import hash_password, verify_password
from app.exceptions.user_exceptions import InvalidEmailFormatError, UserAlreadyExistsError, InvalidCredentialsError
from app.models.user import User
from app.core.token import create_access_token, create_refresh_token, validate_refresh_token
from pydantic import ValidationError
from app.core.redis import redis_client
from app.services.refresh_token_service import store_refresh_token, rotate_refresh_token, revoke_refresh_token

logger = logging.getLogger(__name__)

def register_user(db: Session, user_data: UserCreate):

    logger.info("Starting user registration")

    # 1. Check whether email already exists
    existing_user = user_repository.get_by_email(db, user_data.email)

    if existing_user:
        logger.warning("Registration failed: email already exists")
        raise UserAlreadyExistsError("Email already registered")

    # 2. Hash the password
    hashed_password = hash_password(user_data.password)

    # 3. Create user in database
    try:
        db_user = User(
    username=user_data.username,
    email=user_data.email,
    hashed_password=hashed_password
    )

        created_user = user_repository.create(db, db_user)

        # Commit transaction
        db.commit()
        
        # Refresh task
        db.refresh(created_user)

        logger.info("User registered successfully. ID: %s", created_user.id)

        return created_user

    except IntegrityError as exc:
        db.rollback()
    
        logger.warning("User registration failed due to integrity error")
    
        raise UserAlreadyExistsError("A user with this email already exists") from exc
    
    except Exception:
        db.rollback()
        logger.exception("User registration failed")
        raise


def login_user(db: Session, email: str, password: str):

    logger.info("User login attempt")

    try:
        validated_email = LoginEmail(email=email)
    except ValidationError as exc:
        raise InvalidEmailFormatError("Invalid email format") from exc

    email = validated_email.email


    # 1. Find user by email
    user = user_repository.get_by_email(db, email)

    # 2. Verify user exists
    if not user:
        logger.warning("Login failed: user not found")
        raise InvalidCredentialsError("Invalid email or password")

    # 3. Check whether account is active
    if not user.is_active:
        logger.warning("Login failed: account is inactive")
        raise InvalidCredentialsError("Invalid email or password")

    # 4. Verify password
    if not verify_password(password, user.hashed_password):
        logger.warning("Login failed: incorrect password")
        raise InvalidCredentialsError("Invalid email or password")

    # 5. Generate JWT access token
    access_token = create_access_token(user_id=user.id)

    # Generate refresh token
    refresh_token = create_refresh_token()

    # Store refresh token in Redis
    store_refresh_token(user_id=user.id, refresh_token=refresh_token)

    logger.info("User login successful. User ID: %s", user.id)

    # 6. Return token
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


def refresh_user_tokens(db: Session, old_refresh_token: str):

    logger.info("Refresh token request received")

    # 1. Check whether the refresh token exists in Redis
    user_id = validate_refresh_token(
        redis_client,
        old_refresh_token
    )

    if not user_id:
        logger.warning("Invalid or expired refresh token")
        raise InvalidCredentialsError("Invalid or expired refresh token")

    # 2. Find the user in the database
    user = user_repository.get_by_id(db, int(user_id))

    if not user or not user.is_active:
        logger.warning("Refresh failed: user not found or inactive")
        raise InvalidCredentialsError("Invalid refresh token")

    # 3. Generate a new refresh token
    new_refresh_token = create_refresh_token()

    # 4. Atomically replace the old refresh token in Redis
    rotated_user_id = rotate_refresh_token(
        old_refresh_token,
        new_refresh_token
    )

    if not rotated_user_id:
        logger.warning("Refresh token already used or expired")
        raise InvalidCredentialsError("Invalid or expired refresh token")

    # 5. Generate a new access token
    access_token = create_access_token(
        user_id=int(rotated_user_id)
    )

    logger.info("Tokens refreshed successfully for user ID: %s", user.id)

    # 6. Return the new token pair
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

def logout_user(refresh_token: str):
    logger.info("Logout request received")

    revoked = revoke_refresh_token(refresh_token)

    if not revoked:
        logger.warning("Logout failed: invalid or already revoked refresh token")
        raise InvalidCredentialsError("Invalid or expired refresh token")

    logger.info("User logged out successfully")

    return {
        "message": "Logged out successfully"
    }


