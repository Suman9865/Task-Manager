
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    APP_NAME: str = "Task Manager API"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./tasks.db"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REDIS_URL: str = "redis://localhost:6379/0"
    RATE_LIMIT_MAX_REQUESTS: int = 5
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    GEOLOCATION_API_URL: str = "https://ipwho.is"
    GEOLOCATION_TIMEOUT: float = 3.0
    GEOLOCATION_MAX_RETRIES: int = 3
    GEOLOCATION_BACKOFF_BASE: float = 0.5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
