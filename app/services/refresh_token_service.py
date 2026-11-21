import json

from app.core.config import settings
from app.core.redis import redis_client
from app.core.token import hash_refresh_token

# A single Redis script makes token consumption, replay-marker creation, and
# replacement-token creation atomic. The session key is checked in the same
# operation so a concurrent logout cannot be bypassed by a refresh.
ROTATE_REFRESH_TOKEN_SCRIPT = """
local token_data = redis.call("GET", KEYS[1])
if not token_data then
    return nil
end
if redis.call("EXISTS", KEYS[3]) == 0 then
    return false
end
redis.call("DEL", KEYS[1])
redis.call("SET", KEYS[2], token_data, "EX", ARGV[1])
redis.call("SET", KEYS[4], token_data, "EX", ARGV[1])
return token_data
"""

async def store_refresh_token(user_id: int, session_id: str, refresh_token: str) -> None:
    token_hash = hash_refresh_token(refresh_token)
    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    await redis_client.setex(
        f"refresh_token:{token_hash}", ttl,
        json.dumps({"user_id": user_id, "session_id": session_id}),
    )

async def validate_refresh_token(refresh_token: str) -> dict | None:
    token_hash = hash_refresh_token(refresh_token)
    token_data = await redis_client.get(f"refresh_token:{token_hash}")
    if token_data:
        return json.loads(token_data)
    # A marker distinguishes a consumed token (replay) from an unknown/expired token.
    consumed = await redis_client.get(f"refresh_token_used:{token_hash}")
    if consumed:
        data = json.loads(consumed)
        data["reused"] = True
        return data
    return None

async def rotate_refresh_token(
    old_refresh_token: str, new_refresh_token: str, session_id: str
) -> dict | None:
    old_hash = hash_refresh_token(old_refresh_token)
    old_key = f"refresh_token:{old_hash}"
    new_key = f"refresh_token:{hash_refresh_token(new_refresh_token)}"
    used_key = f"refresh_token_used:{old_hash}"
    session_key = f"session:{session_id}"
    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    token_data = await redis_client.eval(
        ROTATE_REFRESH_TOKEN_SCRIPT, 4, old_key, used_key, session_key, new_key, ttl
    )
    return json.loads(token_data) if token_data else None

async def revoke_refresh_token(refresh_token: str) -> bool:
    token_hash = hash_refresh_token(refresh_token)
    deleted = await redis_client.delete(f"refresh_token:{token_hash}")
    return deleted > 0
