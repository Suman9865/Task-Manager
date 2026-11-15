
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


def create_session(user_id: int) -> str:

    redis_client = get_redis()

    # Generate a unique session ID
    session_id = uuid4().hex

    # Calculate session expiration
    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    created_at = datetime.now(timezone.utc)
    expires_at = created_at + timedelta(seconds=ttl)

    # Prepare session data
    session_data = {
        "session_id": session_id,
        "user_id": user_id,
        "created_at": created_at.isoformat(),
        "expires_at": expires_at.isoformat()
    }

    session_key = get_session_key(session_id)
    user_sessions_key = get_user_sessions_key(user_id)

    # Execute Redis operations together
    pipeline = redis_client.pipeline()

    pipeline.setex(
        session_key,
        ttl,
        json.dumps(session_data)
    )

    pipeline.zadd(
        user_sessions_key,
        {session_id: expires_at.timestamp()}
    )

    pipeline.expire(user_sessions_key, ttl)

    pipeline.execute()

    logger.info(
        "Session created for user ID: %s",
        user_id
    )

    return session_id


def get_session(session_id: str) -> dict | None:

    redis_client = get_redis()

    session_key = get_session_key(session_id)

    session_data = redis_client.get(session_key)

    if not session_data:
        return None

    return json.loads(session_data)


def revoke_session(
    session_id: str,
    user_id: int
) -> bool:

    redis_client = get_redis()

    session_key = get_session_key(session_id)
    user_sessions_key = get_user_sessions_key(user_id)

    pipeline = redis_client.pipeline()

    pipeline.delete(session_key)
    pipeline.zrem(user_sessions_key, session_id)

    results = pipeline.execute()

    revoked = results[0] > 0

    if revoked:
        logger.info(
            "Session revoked for user ID: %s",
            user_id
        )

    return revoked
