import logging
import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)

redis_client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=3,
    socket_timeout=3,
)


def get_redis():
    return redis_client


async def close_redis() -> None:
    await redis_client.aclose()
    logger.info("Redis connection pool closed")
