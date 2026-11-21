from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Task Manager API"
    DEBUG: bool = False
    AUTO_CREATE_SCHEMA: bool = False
    DATABASE_URL: str = "sqlite+aiosqlite:///./tasks.db"
    DB_POOL_SIZE: int = Field(default=5, ge=1)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0)
    DB_POOL_TIMEOUT: float = Field(default=30.0, gt=0)
    DB_POOL_RECYCLE: int = Field(default=1800, gt=0)
    SECRET_KEY: str = Field(min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, gt=0)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, gt=0)
    REDIS_URL: str = "redis://localhost:6379/0"
    RATE_LIMIT_MAX_REQUESTS: int = Field(default=5, gt=0)
    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=60, gt=0)
    GEOLOCATION_API_URL: str = "https://ipwho.is"
    GEOLOCATION_TIMEOUT: float = Field(default=3.0, gt=0)
    GEOLOCATION_MAX_RETRIES: int = Field(default=3, ge=0)
    GEOLOCATION_BACKOFF_BASE: float = Field(default=0.5, ge=0)
    WEATHER_API_KEY: str = Field(min_length=1)
    WEATHER_API_BASE_URL: str = "https://api.weatherapi.com/v1"
    WEATHER_API_TIMEOUT: float = Field(default=5.0, gt=0)
    WEATHER_API_MAX_RETRIES: int = Field(default=3, ge=0)
    WEATHER_API_BACKOFF_BASE: float = Field(default=0.5, ge=0)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=True
    )

settings = Settings()
