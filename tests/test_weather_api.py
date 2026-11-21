from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.external_apis import weather_api
from app.exceptions.weather_exceptions import (
    WeatherAPIError,
    WeatherAPIResponseError,
    WeatherAPITimeoutError,
)
from app.services import weather_service


def make_response(payload, status_code=200):
    request = httpx.Request("GET", "https://weather.example/current.json")
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status = MagicMock()
    if status_code >= 400:
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "upstream error",
            request=request,
            response=httpx.Response(status_code, request=request),
        )
    return response


@pytest.mark.asyncio
async def test_weather_api_success(monkeypatch):
    response = make_response({"current": {"temp_c": 22}})
    client = MagicMock()
    client.get = AsyncMock(return_value=response)
    monkeypatch.setattr(weather_api, "get_http_client", lambda: client)

    result = await weather_api.get_weather("Patna")

    assert result == {"current": {"temp_c": 22}}
    client.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_weather_api_retries_timeout_then_succeeds(monkeypatch):
    monkeypatch.setattr(weather_api.settings, "WEATHER_API_MAX_RETRIES", 1)
    monkeypatch.setattr(weather_api.settings, "WEATHER_API_BACKOFF_BASE", 0)
    response = make_response({"current": {"temp_c": 25}})
    client = MagicMock()
    client.get = AsyncMock(
        side_effect=[httpx.TimeoutException("timeout"), response]
    )
    monkeypatch.setattr(weather_api, "get_http_client", lambda: client)

    assert await weather_api.get_weather("Patna") == {"current": {"temp_c": 25}}
    assert client.get.await_count == 2


@pytest.mark.asyncio
async def test_weather_api_does_not_retry_client_error(monkeypatch):
    response = make_response({}, status_code=400)
    client = MagicMock()
    client.get = AsyncMock(return_value=response)
    monkeypatch.setattr(weather_api, "get_http_client", lambda: client)

    with pytest.raises(WeatherAPIError):
        await weather_api.get_weather("invalid")

    client.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_weather_api_retries_server_error_then_raises(monkeypatch):
    monkeypatch.setattr(weather_api.settings, "WEATHER_API_MAX_RETRIES", 1)
    monkeypatch.setattr(weather_api.settings, "WEATHER_API_BACKOFF_BASE", 0)
    response = make_response({}, status_code=503)
    client = MagicMock()
    client.get = AsyncMock(return_value=response)
    monkeypatch.setattr(weather_api, "get_http_client", lambda: client)

    with pytest.raises(WeatherAPIError):
        await weather_api.get_weather("Patna")

    assert client.get.await_count == 2


@pytest.mark.asyncio
async def test_weather_api_invalid_json_raises(monkeypatch):
    response = make_response({})
    response.json.side_effect = ValueError("invalid json")
    client = MagicMock()
    client.get = AsyncMock(return_value=response)
    monkeypatch.setattr(weather_api, "get_http_client", lambda: client)

    with pytest.raises(WeatherAPIResponseError):
        await weather_api.get_weather("Patna")


@pytest.mark.asyncio
async def test_weather_api_rejects_non_object_payload(monkeypatch):
    response = make_response(["not", "an", "object"])
    client = MagicMock()
    client.get = AsyncMock(return_value=response)
    monkeypatch.setattr(weather_api, "get_http_client", lambda: client)

    with pytest.raises(WeatherAPIResponseError):
        await weather_api.get_weather("Patna")


@pytest.mark.asyncio
async def test_weather_service_returns_safe_fallback(monkeypatch):
    async def fail(_location):
        raise WeatherAPIError("provider down")

    monkeypatch.setattr(weather_service, "get_weather", fail)
    result = await weather_service.get_weather_service("Patna")

    assert result["available"] is False
    assert result["weather"] is None
    assert result["message"] == "Weather information is currently unavailable."
