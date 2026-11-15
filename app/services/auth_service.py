
import logging

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.schemas import UserCreate, LoginEmail
from app.repositories import user_repository
from app.core.security import hash_password, verify_password
from app.exceptions.user_exceptions import InvalidEmailFormatError, UserAlreadyExistsError, InvalidCredentialsError
from app.models.user import User
from app.core.token import create_access_token, create_refresh_token
from pydantic import ValidationError
from app.services.refresh_token_service import store_refresh_token

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

