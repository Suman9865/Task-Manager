import json
import logging

from redis.exceptions import RedisError

from app.core.redis import redis_client

logger = logging.getLogger(__name__)


def get_cache(key: str):
    try:
        cached_data = redis_client.get(key)

        if cached_data is None:
            logger.debug("Cache miss: %s", key)
            return None

        logger.debug("Cache hit: %s", key)

        return json.loads(cached_data)

    except json.JSONDecodeError:
        logger.warning("Invalid cached JSON: %s", key)
        delete_cache(key)
        return None

    except RedisError:
        logger.exception("Redis GET operation failed")
        return None

def set_cache(key: str, value, ttl: int = 60):

    try:
        serialized_data = json.dumps(value)

        redis_client.setex(
            key,
            ttl,
            serialized_data
        )

        logger.debug("Cache stored: %s", key)

        return True

    except (RedisError, TypeError, ValueError):
        logger.exception("Redis SET operation failed")
        return False

def delete_cache(key: str):

    try:
        redis_client.delete(key)

        logger.debug("Cache deleted: %s", key)

        return True

    except RedisError:
        logger.exception("Redis DELETE operation failed")
        return False


def delete_cache_pattern(pattern: str):

    try:
        deleted_count = 0

        for key in redis_client.scan_iter(match=pattern):
            deleted_count += redis_client.delete(key)

        logger.info(
            "Cache invalidation completed. Pattern: %s, Deleted: %s",
            pattern,
            deleted_count
        )

        return deleted_count

    except RedisError:
        logger.exception("Redis cache pattern deletion failed")
        return 0

def invalidate_user_task_cache(user_id: int, task_id: int | None = None):

    # Invalidate all cached task lists for this user
    delete_cache_pattern(
        f"tasks:user:{user_id}:list:*"
    )

    # Invalidate individual task cache if applicable
    if task_id is not None:
        delete_cache(
            f"tasks:user:{user_id}:task:{task_id}"
        )