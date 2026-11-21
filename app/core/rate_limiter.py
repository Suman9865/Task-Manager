import math
import time

from redis.exceptions import RedisError

from app.core.config import settings
from app.core.redis import get_redis
from app.exceptions.user_exceptions import RateLimitExceededError, ServiceUnavailableError

RATE_LIMIT_SCRIPT = """
local current_count = redis.call('INCR', KEYS[1])
if current_count == 1 then
    redis.call('PEXPIREAT', KEYS[1], ARGV[1])
end
return current_count
"""

SLIDING_WINDOW_SCRIPT = """
local current_count = tonumber(redis.call('GET', KEYS[1]) or '0')
local previous_count = tonumber(redis.call('GET', KEYS[2]) or '0')
local now_ms = tonumber(ARGV[1])
local window_start_ms = tonumber(ARGV[2])
local window_end_ms = tonumber(ARGV[3])
local window_ms = tonumber(ARGV[4])
local limit = tonumber(ARGV[5])
local elapsed = now_ms - window_start_ms
local previous_weight = (window_ms - elapsed) / window_ms
local estimated_count = current_count + (previous_count * previous_weight)
if estimated_count + 1 > limit then
    return {0, estimated_count}
end
current_count = redis.call('INCR', KEYS[1])
redis.call('PEXPIREAT', KEYS[1], window_end_ms + window_ms)
estimated_count = estimated_count + 1
return {1, estimated_count}
"""


def _fixed_window_key(prefix: str, identity: str | int) -> tuple[str, int]:
    now = int(time.time())
    window_id = now // settings.RATE_LIMIT_WINDOW_SECONDS
    window_end = (window_id + 1) * settings.RATE_LIMIT_WINDOW_SECONDS
    return f"rate_limit:{prefix}:{identity}:window:{window_id}", window_end


async def _increment(key: str, window_end: int) -> int:
    try:
        count = await get_redis().eval(RATE_LIMIT_SCRIPT, 1, key, window_end * 1000)
        return int(count)
    except RedisError as exc:
        raise ServiceUnavailableError(
            "Rate limiting service temporarily unavailable"
        ) from exc


def _result_or_raise(count: int, window_end: int, message: str) -> dict[str, int]:
    remaining = max(0, settings.RATE_LIMIT_MAX_REQUESTS - count)
    if count > settings.RATE_LIMIT_MAX_REQUESTS:
        raise RateLimitExceededError(
            message=message,
            retry_after=max(1, window_end - int(time.time())),
            limit=settings.RATE_LIMIT_MAX_REQUESTS,
        )
    return {
        "limit": settings.RATE_LIMIT_MAX_REQUESTS,
        "remaining": remaining,
        "reset": window_end,
    }


async def check_rate_limit(user_id: int) -> dict[str, int]:
    key, window_end = _fixed_window_key("user", user_id)
    return _result_or_raise(
        await _increment(key, window_end), window_end,
        "Rate limit exceeded. Try again later.",
    )


async def check_ip_rate_limit(client_ip: str) -> dict[str, int]:
    key, window_end = _fixed_window_key("ip", client_ip)
    return _result_or_raise(
        await _increment(key, window_end), window_end,
        "IP rate limit exceeded. Try again later.",
    )


def generate_sliding_window_keys(user_id: int) -> tuple[str, str, int, int, int]:
    now = time.time()
    size = settings.RATE_LIMIT_WINDOW_SECONDS
    window_id = int(now // size)
    start = window_id * size
    end = start + size
    return (
        f"rate_limit:user:{user_id}:window:{window_id}",
        f"rate_limit:user:{user_id}:window:{window_id - 1}",
        start, end, int(now * 1000),
    )


async def check_sliding_window_rate_limit(user_id: int) -> dict[str, int]:
    current_key, previous_key, start, end, now_ms = generate_sliding_window_keys(user_id)
    window_ms = settings.RATE_LIMIT_WINDOW_SECONDS * 1000
    try:
        result = await get_redis().eval(
            SLIDING_WINDOW_SCRIPT, 2, current_key, previous_key,
            now_ms, start * 1000, end * 1000, window_ms,
            settings.RATE_LIMIT_MAX_REQUESTS,
        )
    except RedisError as exc:
        raise ServiceUnavailableError(
            "Rate limiting service temporarily unavailable"
        ) from exc

    allowed, estimated_count = bool(int(result[0])), float(result[1])
    if not allowed:
        raise RateLimitExceededError(
            message="Rate limit exceeded. Try again later.",
            retry_after=max(1, end + settings.RATE_LIMIT_WINDOW_SECONDS - math.floor(now_ms / 1000)),
            limit=settings.RATE_LIMIT_MAX_REQUESTS,
        )
    return {
        "limit": settings.RATE_LIMIT_MAX_REQUESTS,
        "remaining": max(0, settings.RATE_LIMIT_MAX_REQUESTS - math.ceil(estimated_count)),
        "reset": end,
    }
