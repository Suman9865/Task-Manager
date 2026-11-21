import json
from unittest.mock import AsyncMock

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core import cache


@pytest.mark.asyncio
async def test_cache_round_trip(monkeypatch):
    redis_mock = AsyncMock()
    redis_mock.get.return_value = json.dumps({"id": 1, "title": "Learn Redis"})
    monkeypatch.setattr(cache, "get_redis", lambda: redis_mock)
    value = await cache.get_cache("test:cache")
    assert value == {"id": 1, "title": "Learn Redis"}
    assert await cache.set_cache("test:cache", value, ttl=60) is True
    redis_mock.setex.assert_awaited_once()
    assert await cache.delete_cache("test:cache") is True
    redis_mock.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_cache_fails_open_when_redis_is_unavailable(monkeypatch):
    redis_mock = AsyncMock()
    redis_mock.get.side_effect = RedisConnectionError("Redis unavailable")
    redis_mock.setex.side_effect = RedisConnectionError("Redis unavailable")
    monkeypatch.setattr(cache, "get_redis", lambda: redis_mock)
    assert await cache.get_cache("cache:key") is None
    assert await cache.set_cache("cache:key", {"ok": True}) is False


@pytest.mark.asyncio
async def test_corrupt_cache_entry_is_deleted(monkeypatch):
    redis_mock = AsyncMock()
    redis_mock.get.return_value = "{invalid-json"
    monkeypatch.setattr(cache, "get_redis", lambda: redis_mock)
    assert await cache.get_cache("cache:key") is None
    redis_mock.delete.assert_awaited_once_with("cache:key")


@pytest.mark.asyncio
async def test_cache_rejects_non_positive_ttl():
    with pytest.raises(ValueError):
        await cache.set_cache("cache:key", {}, ttl=0)
