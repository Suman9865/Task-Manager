
from app.config import settings
from app.core.redis import redis_client
from app.core.token import hash_refresh_token


ROTATE_REFRESH_TOKEN_SCRIPT = """
local user_id = redis.call("GET", KEYS[1])

if not user_id then
    return nil
end

redis.call("DEL", KEYS[1])

redis.call(
    "SET",
    KEYS[2],
    user_id,
    "EX",
    ARGV[1]
)

return user_id
"""

def store_refresh_token(user_id: int, refresh_token: str) -> None:

    token_hash = hash_refresh_token(refresh_token)

    redis_key = f"refresh_token:{token_hash}"

    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    redis_client.setex(
        redis_key,
        ttl,
        str(user_id)
    )


def rotate_refresh_token(
    old_refresh_token: str,
    new_refresh_token: str
) -> str | None:

    old_token_hash = hash_refresh_token(old_refresh_token)
    new_token_hash = hash_refresh_token(new_refresh_token)

    old_redis_key = f"refresh_token:{old_token_hash}"
    new_redis_key = f"refresh_token:{new_token_hash}"

    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    user_id = redis_client.eval(
        ROTATE_REFRESH_TOKEN_SCRIPT,
        2,
        old_redis_key,
        new_redis_key,
        ttl
    )

    return user_id

