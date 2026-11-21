from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.external_apis import geolocation_api


@pytest.mark.asyncio
async def test_fetch_ip_location_success(monkeypatch):
    monkeypatch.setattr(geolocation_api.settings, "GEOLOCATION_API_URL", "https://example.com/json")
    expected = {"ip": "8.8.8.8", "country": "United States"}
    response = MagicMock()
    response.json.return_value = expected
    client = MagicMock()
    client.get = AsyncMock(return_value=response)
    monkeypatch.setattr(geolocation_api, "get_http_client", lambda: client)

    assert await geolocation_api.fetch_ip_location("8.8.8.8") == expected
    client.get.assert_awaited_once_with(
        "https://example.com/json/8.8.8.8",
        timeout=geolocation_api.settings.GEOLOCATION_TIMEOUT,
    )
    response.raise_for_status.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_ip_location_retries_timeout(monkeypatch):
    monkeypatch.setattr(geolocation_api.settings, "GEOLOCATION_MAX_RETRIES", 1)
    monkeypatch.setattr(geolocation_api.settings, "GEOLOCATION_BACKOFF_BASE", 0)
    response = MagicMock()
    response.json.return_value = {"country": "India"}
    client = MagicMock()
    client.get = AsyncMock(side_effect=[httpx.TimeoutException("timeout"), response])
    monkeypatch.setattr(geolocation_api, "get_http_client", lambda: client)

    result = await geolocation_api.fetch_ip_location("8.8.8.8")
    assert result == {"country": "India"}
    assert client.get.await_count == 2


@pytest.mark.asyncio
async def test_fetch_ip_location_permanent_http_error(monkeypatch):
    request = httpx.Request("GET", "https://example.com/8.8.8.8")
    response = httpx.Response(404, request=request)
    client = MagicMock()
    client.get = AsyncMock(return_value=response)
    monkeypatch.setattr(geolocation_api, "get_http_client", lambda: client)

    assert await geolocation_api.fetch_ip_location("8.8.8.8") is None
    client.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_fetch_ip_location_invalid_json(monkeypatch):
    response = MagicMock()
    response.json.side_effect = ValueError("invalid json")
    client = MagicMock()
    client.get = AsyncMock(return_value=response)
    monkeypatch.setattr(geolocation_api, "get_http_client", lambda: client)

    assert await geolocation_api.fetch_ip_location("8.8.8.8") is None


@pytest.mark.asyncio
async def test_fetch_ip_location_exhausted_retries(monkeypatch):
    monkeypatch.setattr(geolocation_api.settings, "GEOLOCATION_MAX_RETRIES", 2)
    monkeypatch.setattr(geolocation_api.settings, "GEOLOCATION_BACKOFF_BASE", 0)
    client = MagicMock()
    client.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
    monkeypatch.setattr(geolocation_api, "get_http_client", lambda: client)

    assert await geolocation_api.fetch_ip_location("8.8.8.8") is None
    assert client.get.await_count == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_data", [["India"], "India", 123, None])
async def test_fetch_ip_location_invalid_response_format(monkeypatch, invalid_data):
    response = MagicMock()
    response.json.return_value = invalid_data
    client = MagicMock()
    client.get = AsyncMock(return_value=response)
    monkeypatch.setattr(geolocation_api, "get_http_client", lambda: client)

    assert await geolocation_api.fetch_ip_location("8.8.8.8") is None
