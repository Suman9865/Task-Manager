from unittest.mock import AsyncMock

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core import rate_limiter
from app.exceptions.user_exceptions import ServiceUnavailableError


@pytest.mark.asyncio
async def test_fixed_window_returns_remaining_quota(monkeypatch):
    monkeypatch.setattr(rate_limiter, "_fixed_window_key", lambda prefix, identity: ("key", 200))
    monkeypatch.setattr(rate_limiter, "_increment", AsyncMock(return_value=2))
    monkeypatch.setattr(rate_limiter.settings, "RATE_LIMIT_MAX_REQUESTS", 5)
    assert await rate_limiter.check_rate_limit(10) == {
        "limit": 5, "remaining": 3, "reset": 200
    }


@pytest.mark.asyncio
async def test_fixed_window_raises_when_limit_exceeded(monkeypatch):
    monkeypatch.setattr(rate_limiter, "_fixed_window_key", lambda prefix, identity: ("key", 200))
    monkeypatch.setattr(rate_limiter, "_increment", AsyncMock(return_value=6))
    monkeypatch.setattr(rate_limiter.settings, "RATE_LIMIT_MAX_REQUESTS", 5)
    with pytest.raises(rate_limiter.RateLimitExceededError):
        await rate_limiter.check_rate_limit(10)


@pytest.mark.asyncio
async def test_redis_failure_fails_closed(monkeypatch):
    redis = AsyncMock()
    redis.eval.side_effect = RedisConnectionError("Redis unavailable")
    monkeypatch.setattr(rate_limiter, "get_redis", lambda: redis)
    with pytest.raises(ServiceUnavailableError):
        await rate_limiter._increment("key", 200)
