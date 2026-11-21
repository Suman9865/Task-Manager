import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm

from app.database import get_db
from app.schemas import UserCreate, UserResponse, RefreshTokenRequest
from app.services.auth_service import register_user, login_user, refresh_user_tokens, logout_user
from app.core.rate_limit_dependencies import ip_rate_limit_dependency

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, dependencies=[Depends(ip_rate_limit_dependency)])
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    return await register_user(db, user_data)


@router.post("/login", dependencies=[Depends(ip_rate_limit_dependency)])
async def login(user_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    return await login_user(db, user_data.username, user_data.password)


@router.post("/refresh", dependencies=[Depends(ip_rate_limit_dependency)])
async def refresh(token_data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    return await refresh_user_tokens(db, token_data.refresh_token)


@router.post("/logout", dependencies=[Depends(ip_rate_limit_dependency)])
async def logout(token_data: RefreshTokenRequest):
    return await logout_user(token_data.refresh_token)
