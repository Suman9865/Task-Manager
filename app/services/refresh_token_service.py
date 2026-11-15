
from app.config import settings
from app.core.redis import redis_client
from app.core.token import hash_refresh_token


def store_refresh_token(user_id: int, refresh_token: str) -> None:

    token_hash = hash_refresh_token(refresh_token)

    redis_key = f"refresh_token:{token_hash}"

    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    redis_client.setex(
        redis_key,
        ttl,
        str(user_id)
    )
