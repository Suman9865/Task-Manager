import pytest
from unittest.mock import AsyncMock

from app.core.redis import close_redis, get_redis


@pytest.mark.asyncio
async def test_redis_client_is_async():
    client = get_redis()
    assert hasattr(client, "get")
    assert hasattr(client, "aclose")
