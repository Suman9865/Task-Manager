import json
import logging

from redis.exceptions import RedisError

from app.core.redis import redis_client

logger = logging.getLogger(__name__)


async def get_cache(key: str):
    try:
        cached_data = await redis_client.get(key)
        if cached_data is None:
            logger.debug("Cache miss: %s", key)
            return None
        logger.debug("Cache hit: %s", key)
        return json.loads(cached_data)
    except json.JSONDecodeError:
        logger.warning("Invalid cached JSON: %s", key)
        await delete_cache(key)
        return None
    except RedisError:
        logger.exception("Redis GET operation failed")
        return None


async def set_cache(key: str, value, ttl: int = 60):
    try:
        await redis_client.setex(key, ttl, json.dumps(value))
        logger.debug("Cache stored: %s", key)
        return True
    except (RedisError, TypeError, ValueError):
        logger.exception("Redis SET operation failed")
        return False


async def delete_cache(key: str):
    try:
        await redis_client.delete(key)
        logger.debug("Cache deleted: %s", key)
        return True
    except RedisError:
        logger.exception("Redis DELETE operation failed")
        return False


async def delete_cache_pattern(pattern: str):
    try:
        deleted_count = 0
        async for key in redis_client.scan_iter(match=pattern):
            deleted_count += await redis_client.delete(key)
        logger.info("Cache invalidation completed. Pattern: %s, Deleted: %s", pattern, deleted_count)
        return deleted_count
    except RedisError:
        logger.exception("Redis cache pattern deletion failed")
        return 0


async def invalidate_user_task_cache(user_id: int, task_id: int | None = None):
    await delete_cache_pattern(f"tasks:user:{user_id}:list:*")
    if task_id is not None:
        await delete_cache(f"tasks:user:{user_id}:task:{task_id}")
