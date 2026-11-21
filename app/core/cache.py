import json
import logging

from redis.exceptions import RedisError

from app.core.redis import get_redis

logger = logging.getLogger(__name__)


async def get_cache(key: str):
    try:
        cached_data = await get_redis().get(key)
        if cached_data is None:
            logger.debug("Cache miss")
            return None
        logger.debug("Cache hit")
        return json.loads(cached_data)
    except json.JSONDecodeError:
        logger.warning("Invalid cached JSON; deleting corrupt entry")
        await delete_cache(key)
        return None
    except RedisError:
        logger.exception("Redis GET operation failed")
        return None


async def set_cache(key: str, value, ttl: int = 60) -> bool:
    if ttl <= 0:
        raise ValueError("Cache TTL must be greater than zero")
    try:
        await get_redis().setex(key, ttl, json.dumps(value))
        logger.debug("Cache stored")
        return True
    except (RedisError, TypeError, ValueError):
        logger.exception("Redis SET operation failed")
        return False


async def delete_cache(key: str) -> bool:
    try:
        await get_redis().delete(key)
        logger.debug("Cache deleted")
        return True
    except RedisError:
        logger.exception("Redis DELETE operation failed")
        return False


async def delete_cache_pattern(pattern: str) -> int:
    try:
        deleted_count = 0
        async for key in get_redis().scan_iter(match=pattern, count=200):
            deleted_count += await get_redis().delete(key)
        logger.info("Cache invalidation completed; deleted %s keys", deleted_count)
        return deleted_count
    except RedisError:
        logger.exception("Redis cache pattern deletion failed")
        return 0


async def invalidate_user_task_cache(user_id: int, task_id: int | None = None) -> None:
    await delete_cache_pattern(f"tasks:user:{user_id}:list:*")
    if task_id is not None:
        await delete_cache(f"tasks:user:{user_id}:task:{task_id}")
