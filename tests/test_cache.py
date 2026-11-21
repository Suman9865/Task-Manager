import json
from unittest.mock import AsyncMock

import pytest

from app.core import cache


@pytest.mark.asyncio
async def test_cache_round_trip(monkeypatch):
    redis_mock = AsyncMock()
    redis_mock.get.return_value = json.dumps({"id": 1, "title": "Learn Redis"})
    monkeypatch.setattr(cache, "redis_client", redis_mock)

    value = await cache.get_cache("test:cache")
    assert value == {"id": 1, "title": "Learn Redis"}

    assert await cache.set_cache("test:cache", value, ttl=60) is True
    redis_mock.setex.assert_awaited_once()
    assert await cache.delete_cache("test:cache") is True
    redis_mock.delete.assert_awaited_once()
