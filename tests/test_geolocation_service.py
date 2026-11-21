
from unittest.mock import patch

from app.services.geolocation_service import get_ip_location


def test_get_ip_location_success():

    expected_data = {
        "success": True,
        "country": "United States",
        "city": "Mountain View"
    }

    with patch(
        "app.services.geolocation_service.fetch_ip_location",
        return_value=expected_data
    ) as mock_fetch:

        result = get_ip_location("8.8.8.8")

    assert result == {
        "country": "United States",
        "city": "Mountain View"
    }

    mock_fetch.assert_called_once_with("8.8.8.8")


import pytest


@pytest.mark.parametrize(
    "ip_address",
    [
        "invalid-ip",
        "999.999.999.999",
        "abc.def.ghi.jkl",
        ""
    ]
)
def test_get_ip_location_invalid_ip(ip_address):

    with patch(
        "app.services.geolocation_service.fetch_ip_location"
    ) as mock_fetch:

        result = get_ip_location(ip_address)

    assert result == {
        "country": None,
        "city": None
    }

    # External API must never be called.
    mock_fetch.assert_not_called()


@pytest.mark.parametrize(
    "ip_address",
    [
        "192.168.1.1",   # Private IPv4
        "10.0.0.1",      # Private IPv4
        "127.0.0.1",     # Loopback IPv4
        "172.16.0.1",    # Private IPv4
        "169.254.1.1",   # Link-local IPv4
        "::1",           # Loopback IPv6
        "fc00::1",       # Private IPv6
    ]
)
def test_get_ip_location_non_public_ip(ip_address):

    with patch(
        "app.services.geolocation_service.fetch_ip_location"
    ) as mock_fetch:

        result = get_ip_location(ip_address)

    assert result == {
        "country": None,
        "city": None
    }

    mock_fetch.assert_not_called()


def test_get_ip_location_external_api_failure():

    with patch(
        "app.services.geolocation_service.fetch_ip_location",
        return_value=None
    ) as mock_fetch:

        result = get_ip_location("8.8.8.8")

    assert result == {
        "country": None,
        "city": None
    }

    mock_fetch.assert_called_once_with("8.8.8.8")


def test_get_ip_location_provider_unsuccessful():

    api_response = {
        "success": False,
        "message": "Location not found"
    }

    with patch(
        "app.services.geolocation_service.fetch_ip_location",
        return_value=api_response
    ) as mock_fetch:

        result = get_ip_location("8.8.8.8")

    assert result == {
        "country": None,
        "city": None
    }

    mock_fetch.assert_called_once_with("8.8.8.8")


@pytest.mark.parametrize(
    "api_response, expected_result",
    [
        (
            {"success": True, "country": "India"},
            {"country": "India", "city": None}
        ),
        (
            {"success": True, "city": "Patna"},
            {"country": None, "city": "Patna"}
        ),
        (
            {"success": True},
            {"country": None, "city": None}
        )
    ]
)
def test_get_ip_location_missing_fields(
    api_response,
    expected_result
):

    with patch(
        "app.services.geolocation_service.fetch_ip_location",
        return_value=api_response
    ):

        result = get_ip_location("8.8.8.8")

    assert result == expected_result
