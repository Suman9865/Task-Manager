from unittest.mock import AsyncMock

import pytest

from app.services import geolocation_service


@pytest.mark.asyncio
async def test_get_ip_location_success(monkeypatch):
    fetch = AsyncMock(return_value={
        "success": True, "country": "United States", "city": "Mountain View"
    })
    monkeypatch.setattr(geolocation_service, "fetch_ip_location", fetch)

    assert await geolocation_service.get_ip_location("8.8.8.8") == {
        "country": "United States", "city": "Mountain View"
    }
    fetch.assert_awaited_once_with("8.8.8.8")


@pytest.mark.asyncio
@pytest.mark.parametrize("ip", ["invalid-ip", "999.999.999.999", "", "192.168.1.1", "127.0.0.1", "::1", "fc00::1"])
async def test_get_ip_location_invalid_or_non_public_ip(monkeypatch, ip):
    fetch = AsyncMock()
    monkeypatch.setattr(geolocation_service, "fetch_ip_location", fetch)

    assert await geolocation_service.get_ip_location(ip) == {"country": None, "city": None}
    fetch.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("response", [
    None,
    {"success": False, "message": "Location not found"},
])
async def test_get_ip_location_fallback(monkeypatch, response):
    fetch = AsyncMock(return_value=response)
    monkeypatch.setattr(geolocation_service, "fetch_ip_location", fetch)

    assert await geolocation_service.get_ip_location("8.8.8.8") == {
        "country": None, "city": None
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response, expected",
    [
        ({"success": True, "country": "India"}, {"country": "India", "city": None}),
        ({"success": True, "city": "Patna"}, {"country": None, "city": "Patna"}),
        ({"success": True}, {"country": None, "city": None}),
    ],
)
async def test_get_ip_location_missing_fields(monkeypatch, response, expected):
    monkeypatch.setattr(
        geolocation_service, "fetch_ip_location", AsyncMock(return_value=response)
    )
    assert await geolocation_service.get_ip_location("8.8.8.8") == expected
