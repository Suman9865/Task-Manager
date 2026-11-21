import json
import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.core.config import settings
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

def get_session_key(session_id: str) -> str:
    return f"session:{session_id}"

def get_user_sessions_key(user_id: int) -> str:
    return f"user_sessions:{user_id}"

async def create_session(user_id: int) -> str:
    redis_client = get_redis()
    session_id = uuid4().hex
    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    created_at = datetime.now(timezone.utc)
    expires_at = created_at + timedelta(seconds=ttl)
    session_data = {
        "session_id": session_id, "user_id": user_id,
        "created_at": created_at.isoformat(), "expires_at": expires_at.isoformat(),
    }
    async with redis_client.pipeline(transaction=True) as pipeline:
        pipeline.setex(get_session_key(session_id), ttl, json.dumps(session_data))
        pipeline.zadd(get_user_sessions_key(user_id), {session_id: expires_at.timestamp()})
        pipeline.expire(get_user_sessions_key(user_id), ttl)
        await pipeline.execute()
    logger.info("Session created for user ID: %s", user_id)
    return session_id

async def get_session(session_id: str) -> dict | None:
    session_data = await get_redis().get(get_session_key(session_id))
    return json.loads(session_data) if session_data else None

async def revoke_session(session_id: str, user_id: int) -> bool:
    # Redis transactions serialize revocation with the Lua refresh operation:
    # whichever executes first determines whether rotation can proceed.
    redis_client = get_redis()
    async with redis_client.pipeline(transaction=True) as pipeline:
        pipeline.delete(get_session_key(session_id))
        pipeline.zrem(get_user_sessions_key(user_id), session_id)
        results = await pipeline.execute()
    revoked = results[0] > 0
    if revoked:
        logger.info("Session revoked for user ID: %s", user_id)
    return revoked
