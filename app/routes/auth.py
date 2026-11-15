
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.database import get_db
from app.schemas import UserCreate, UserResponse, UserLogin, LoginEmail, RefreshTokenRequest
from app.services.auth_service import (register_user, login_user, refresh_user_tokens, logout_user)
from app.core.rate_limit_dependencies import ip_rate_limit_dependency

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, dependencies=[Depends(ip_rate_limit_dependency)])
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    logger.info("POST /auth/register - Request received")
    return register_user(db, user_data)


@router.post("/login", dependencies=[Depends(ip_rate_limit_dependency)])
def login(user_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info("POST /auth/login - Request received")
    return login_user(db,user_data.username,user_data.password)


@router.post("/refresh", dependencies=[Depends(ip_rate_limit_dependency)])
def refresh(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    logger.info("POST /auth/refresh - Request received")

    return refresh_user_tokens(
        db,
        token_data.refresh_token
    )

@router.post("/logout", dependencies=[Depends(ip_rate_limit_dependency)])
def logout(token_data: RefreshTokenRequest):
    logger.info("POST /auth/logout - Request received")

    return logout_user(token_data.refresh_token)
