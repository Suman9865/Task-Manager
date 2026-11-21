from unittest.mock import AsyncMock

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app import main


@pytest.mark.asyncio
async def test_liveness_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_readiness_endpoint_success(client, monkeypatch):
    redis_mock = AsyncMock()
    redis_mock.ping.return_value = True
    monkeypatch.setattr(main, "get_redis", lambda: redis_mock)
    response = await client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@pytest.mark.asyncio
async def test_readiness_endpoint_redis_failure(client, monkeypatch):
    redis_mock = AsyncMock()
    redis_mock.ping.side_effect = RedisConnectionError("Redis unavailable")
    monkeypatch.setattr(main, "get_redis", lambda: redis_mock)
    response = await client.get("/ready")
    assert response.status_code == 503
