import json

from app.core.config import settings
from app.core.redis import redis_client
from app.core.token import hash_refresh_token

ROTATE_REFRESH_TOKEN_SCRIPT = """
local token_data = redis.call("GET", KEYS[1])
if not token_data then
    return nil
end
redis.call("DEL", KEYS[1])
redis.call("SET", KEYS[2], token_data, "EX", ARGV[1])
return token_data
"""


async def store_refresh_token(user_id: int, session_id: str, refresh_token: str) -> None:
    token_hash = hash_refresh_token(refresh_token)
    redis_key = f"refresh_token:{token_hash}"
    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    await redis_client.setex(
        redis_key, ttl, json.dumps({"user_id": user_id, "session_id": session_id})
    )


async def validate_refresh_token(refresh_token: str) -> dict | None:
    token_hash = hash_refresh_token(refresh_token)
    token_data = await redis_client.get(f"refresh_token:{token_hash}")
    return json.loads(token_data) if token_data else None


async def rotate_refresh_token(old_refresh_token: str, new_refresh_token: str) -> dict | None:
    old_key = f"refresh_token:{hash_refresh_token(old_refresh_token)}"
    new_key = f"refresh_token:{hash_refresh_token(new_refresh_token)}"
    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    token_data = await redis_client.eval(
        ROTATE_REFRESH_TOKEN_SCRIPT, 2, old_key, new_key, ttl
    )
    return json.loads(token_data) if token_data else None


async def revoke_refresh_token(refresh_token: str) -> bool:
    token_hash = hash_refresh_token(refresh_token)
    deleted = await redis_client.delete(f"refresh_token:{token_hash}")
    return deleted > 0
