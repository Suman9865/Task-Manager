import time
import math

from app.core.config import settings
from app.core.redis import get_redis
from app.exceptions.user_exceptions import RateLimitExceededError

redis_client = get_redis()


RATE_LIMIT_SCRIPT = """
local current_count = redis.call('INCR', KEYS[1])

if current_count == 1 then
    redis.call('PEXPIREAT', KEYS[1], ARGV[1])
end

return current_count
"""


def generate_rate_limit_key(user_id: int) -> tuple[str, int]:
    current_time = int(time.time())

    window_id = current_time // settings.RATE_LIMIT_WINDOW_SECONDS

    window_start = window_id * settings.RATE_LIMIT_WINDOW_SECONDS
    window_end = window_start + settings.RATE_LIMIT_WINDOW_SECONDS

    key = f"rate_limit:user:{user_id}:window:{window_id}"

    return key, window_end


def increment_request_count(key: str, window_end: int) -> int:
    window_end_ms = window_end * 1000

    count = redis_client.eval(
        RATE_LIMIT_SCRIPT,
        1,
        key,
        window_end_ms
    )

    return int(count)


def check_rate_limit(user_id: int) -> dict[str, int]:

    key, window_end = generate_rate_limit_key(user_id)

    count = increment_request_count(key, window_end)

    remaining = max(
        0,
        settings.RATE_LIMIT_MAX_REQUESTS - count
    )

    if count > settings.RATE_LIMIT_MAX_REQUESTS:
        retry_after = max(1, window_end - int(time.time()))

        raise RateLimitExceededError(
            message="Rate limit exceeded. Try again later.",
            retry_after=retry_after,
            limit=settings.RATE_LIMIT_MAX_REQUESTS
        )

    return {
    "limit": settings.RATE_LIMIT_MAX_REQUESTS,
    "remaining": remaining,
    "reset": window_end
}

def generate_ip_rate_limit_key(
    client_ip: str
) -> tuple[str, int]:

    current_time = int(time.time())

    window_id = current_time // settings.RATE_LIMIT_WINDOW_SECONDS

    window_start = window_id * settings.RATE_LIMIT_WINDOW_SECONDS
    window_end = window_start + settings.RATE_LIMIT_WINDOW_SECONDS

    key = f"rate_limit:ip:{client_ip}:window:{window_id}"

    return key, window_end

def check_ip_rate_limit(client_ip: str) -> dict[str, int]:

    key, window_end = generate_ip_rate_limit_key(client_ip)

    count = increment_request_count(key, window_end)

    remaining = max(
        0,
        settings.RATE_LIMIT_MAX_REQUESTS - count
    )

    if count > settings.RATE_LIMIT_MAX_REQUESTS:

        retry_after = max(
            1,
            window_end - int(time.time())
        )

        raise RateLimitExceededError(
            message="IP rate limit exceeded. Try again later.",
            retry_after=retry_after,
            limit=settings.RATE_LIMIT_MAX_REQUESTS
        )

    return {
        "limit": settings.RATE_LIMIT_MAX_REQUESTS,
        "remaining": remaining,
        "reset": window_end
    }

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

def generate_sliding_window_keys(
    user_id: int
) -> tuple[str, str, int, int, int]:

    current_time = time.time()

    window_size = settings.RATE_LIMIT_WINDOW_SECONDS

    window_id = int(current_time // window_size)

    window_start = window_id * window_size
    window_end = window_start + window_size

    current_key = f"rate_limit:user:{user_id}:window:{window_id}"

    previous_key = f"rate_limit:user:{user_id}:window:{window_id - 1}"

    now_ms = int(current_time * 1000)

    return current_key, previous_key, window_start, window_end, now_ms

def increment_sliding_window_count(
    current_key: str,
    previous_key: str,
    window_start: int,
    window_end: int,
    now_ms: int
) -> tuple[bool, float]:

    window_ms = settings.RATE_LIMIT_WINDOW_SECONDS * 1000

    result = redis_client.eval(
        SLIDING_WINDOW_SCRIPT,
        2,
        current_key,
        previous_key,
        now_ms,
        window_start * 1000,
        window_end * 1000,
        window_ms,
        settings.RATE_LIMIT_MAX_REQUESTS
    )

    allowed = bool(int(result[0]))
    estimated_count = float(result[1])

    return allowed, estimated_count

def check_sliding_window_rate_limit(user_id: int) -> dict[str, int]:

    (
        current_key,
        previous_key,
        window_start,
        window_end,
        now_ms
    ) = generate_sliding_window_keys(user_id)

    allowed, estimated_count = increment_sliding_window_count(
        current_key,
        previous_key,
        window_start,
        window_end,
        now_ms
    )

    if not allowed:

        window_size = settings.RATE_LIMIT_WINDOW_SECONDS

        retry_after = max(
            1,
            window_end + window_size - math.floor(now_ms / 1000)
        )

        raise RateLimitExceededError(
            message="Rate limit exceeded. Try again later.",
            retry_after=retry_after,
            limit=settings.RATE_LIMIT_MAX_REQUESTS
        )

    remaining = max(
        0,
        settings.RATE_LIMIT_MAX_REQUESTS - math.ceil(estimated_count)
    )

    return {
        "limit": settings.RATE_LIMIT_MAX_REQUESTS,
        "remaining": remaining,
        "reset": window_end
    }