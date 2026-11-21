
from unittest.mock import MagicMock, patch

from app.external_apis.geolocation_api import fetch_ip_location


def test_fetch_ip_location_success(monkeypatch):

    # Arrange: Configure API settings
    monkeypatch.setattr(
        "app.external_apis.geolocation_api.settings.GEOLOCATION_API_URL",
        "https://example.com/json"
    )

    # Mock API response
    expected_data = {
        "ip": "8.8.8.8",
        "country": "United States",
        "city": "Mountain View"
    }

    mock_response = MagicMock()
    mock_response.json.return_value = expected_data

    # Mock HTTPX client
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_client

    with patch(
        "app.external_apis.geolocation_api.httpx.Client",
        return_value=mock_context
    ) as mock_httpx:

        # Act
        result = fetch_ip_location("8.8.8.8")

    # Assert
    assert result == expected_data

    mock_client.get.assert_called_once_with(
        "https://example.com/json/8.8.8.8"
    )

    mock_response.raise_for_status.assert_called_once()
    mock_httpx.assert_called_once()


import httpx


def test_fetch_ip_location_retries_after_timeout(monkeypatch):

    monkeypatch.setattr(
        "app.external_apis.geolocation_api.settings.GEOLOCATION_API_URL",
        "https://example.com/json"
    )

    monkeypatch.setattr(
        "app.external_apis.geolocation_api.settings.GEOLOCATION_MAX_RETRIES",
        2
    )

    monkeypatch.setattr(
        "app.external_apis.geolocation_api.settings.GEOLOCATION_BACKOFF_BASE",
        1
    )

    expected_data = {
        "ip": "8.8.8.8",
        "country": "United States"
    }

    mock_response = MagicMock()
    mock_response.json.return_value = expected_data

    mock_client = MagicMock()

    # First request times out; second request succeeds.
    mock_client.get.side_effect = [
        httpx.TimeoutException("Request timed out"),
        mock_response
    ]

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_client

    with patch(
        "app.external_apis.geolocation_api.httpx.Client",
        return_value=mock_context
    ), patch(
        "app.external_apis.geolocation_api.time.sleep"
    ) as mock_sleep:

        result = fetch_ip_location("8.8.8.8")

    assert result == expected_data

    assert mock_client.get.call_count == 2

    # First retry should wait for 1 second.
    mock_sleep.assert_called_once_with(1)


def test_fetch_ip_location_exponential_backoff(monkeypatch):

    monkeypatch.setattr(
        "app.external_apis.geolocation_api.settings.GEOLOCATION_API_URL",
        "https://example.com/json"
    )

    monkeypatch.setattr(
        "app.external_apis.geolocation_api.settings.GEOLOCATION_MAX_RETRIES",
        3
    )

    monkeypatch.setattr(
        "app.external_apis.geolocation_api.settings.GEOLOCATION_BACKOFF_BASE",
        1
    )

    expected_data = {"ip": "8.8.8.8"}

    mock_response = MagicMock()
    mock_response.json.return_value = expected_data

    mock_client = MagicMock()

    mock_client.get.side_effect = [
        httpx.TimeoutException("Timeout 1"),
        httpx.TimeoutException("Timeout 2"),
        httpx.TimeoutException("Timeout 3"),
        mock_response
    ]

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_client

    with patch(
        "app.external_apis.geolocation_api.httpx.Client",
        return_value=mock_context
    ), patch(
        "app.external_apis.geolocation_api.time.sleep"
    ) as mock_sleep:

        result = fetch_ip_location("8.8.8.8")

    assert result == expected_data
    assert mock_client.get.call_count == 4

    assert [call.args[0] for call in mock_sleep.call_args_list] == [
        1, 2, 4
    ]


def test_fetch_ip_location_permanent_http_error(monkeypatch):

    monkeypatch.setattr(
        "app.external_apis.geolocation_api.settings.GEOLOCATION_API_URL",
        "https://example.com/json"
    )

    monkeypatch.setattr(
        "app.external_apis.geolocation_api.settings.GEOLOCATION_MAX_RETRIES",
        3
    )

    mock_response = MagicMock()

    mock_response.status_code = 404

    http_error = httpx.HTTPStatusError(
        "404 Not Found",
        request=httpx.Request("GET", "https://example.com/json/8.8.8.8"),
        response=httpx.Response(
            404,
            request=httpx.Request("GET", "https://example.com/json/8.8.8.8")
        )
    )

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.get.return_value.raise_for_status.side_effect = http_error

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_client

    with patch(
        "app.external_apis.geolocation_api.httpx.Client",
        return_value=mock_context
    ), patch(
        "app.external_apis.geolocation_api.time.sleep"
    ) as mock_sleep:

        result = fetch_ip_location("8.8.8.8")

    assert result is None

    # Only one request should happen.
    assert mock_client.get.call_count == 1

    # No retry delay.
    mock_sleep.assert_not_called()


import pytest


@pytest.mark.parametrize("status_code", [429, 500, 502, 503])
def test_fetch_ip_location_retries_after_temporary_http_error(
    monkeypatch,
    status_code
):

    monkeypatch.setattr(
        "app.external_apis.geolocation_api.settings.GEOLOCATION_API_URL",
        "https://example.com/json"
    )

    monkeypatch.setattr(
    "app.external_apis.geolocation_api.settings.GEOLOCATION_BACKOFF_BASE",
    1
    )

    error_url = "https://example.com/json/8.8.8.8"

    request = httpx.Request("GET", error_url)

    error_response = httpx.Response(
        status_code,
        request=request
    )

    http_error = httpx.HTTPStatusError(
        f"HTTP {status_code}",
        request=request,
        response=error_response
    )

    expected_data = {"ip": "8.8.8.8"}

    success_response = MagicMock()
    success_response.json.return_value = expected_data

    mock_client = MagicMock()

    error_response_mock = MagicMock()
    error_response_mock.raise_for_status.side_effect = http_error

    mock_client = MagicMock()

    mock_client.get.side_effect = [
    error_response_mock,
    success_response
    ]

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_client

    with patch(
        "app.external_apis.geolocation_api.httpx.Client",
        return_value=mock_context
    ), patch(
        "app.external_apis.geolocation_api.time.sleep"
    ) as mock_sleep:

        result = fetch_ip_location("8.8.8.8")

    assert result == expected_data
    assert mock_client.get.call_count == 2
    mock_sleep.assert_called_once_with(1)


def test_fetch_ip_location_invalid_json(monkeypatch):

    monkeypatch.setattr(
        "app.external_apis.geolocation_api.settings.GEOLOCATION_API_URL",
        "https://example.com/json"
    )

    mock_response = MagicMock()

    mock_response.json.side_effect = ValueError(
        "Invalid JSON"
    )

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_client

    with patch(
        "app.external_apis.geolocation_api.httpx.Client",
        return_value=mock_context
    ), patch(
        "app.external_apis.geolocation_api.time.sleep"
    ) as mock_sleep:

        result = fetch_ip_location("8.8.8.8")

    assert result is None
    assert mock_client.get.call_count == 1
    mock_sleep.assert_not_called()


@pytest.mark.parametrize(
    "invalid_data",
    [
        ["India", "Patna"],
        "India",
        123,
        None
    ]
)
def test_fetch_ip_location_invalid_response_format(
    monkeypatch,
    invalid_data
):

    monkeypatch.setattr(
        "app.external_apis.geolocation_api.settings.GEOLOCATION_API_URL",
        "https://example.com/json"
    )

    mock_response = MagicMock()
    mock_response.json.return_value = invalid_data

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_client

    with patch(
        "app.external_apis.geolocation_api.httpx.Client",
        return_value=mock_context
    ), patch(
        "app.external_apis.geolocation_api.time.sleep"
    ) as mock_sleep:

        result = fetch_ip_location("8.8.8.8")

    assert result is None
    assert mock_client.get.call_count == 1
    mock_sleep.assert_not_called()


def test_fetch_ip_location_retries_exhausted(monkeypatch):

    monkeypatch.setattr(
        "app.external_apis.geolocation_api.settings.GEOLOCATION_API_URL",
        "https://example.com/json"
    )

    monkeypatch.setattr(
        "app.external_apis.geolocation_api.settings.GEOLOCATION_MAX_RETRIES",
        3
    )

    monkeypatch.setattr(
        "app.external_apis.geolocation_api.settings.GEOLOCATION_BACKOFF_BASE",
        1
    )

    mock_client = MagicMock()

    mock_client.get.side_effect = httpx.TimeoutException(
        "Request timed out"
    )

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_client

    with patch(
        "app.external_apis.geolocation_api.httpx.Client",
        return_value=mock_context
    ), patch(
        "app.external_apis.geolocation_api.time.sleep"
    ) as mock_sleep:

        result = fetch_ip_location("8.8.8.8")

    assert result is None

    # Initial attempt + 3 retries.
    assert mock_client.get.call_count == 4

    # Verify exponential backoff.
    assert [
        call.args[0] for call in mock_sleep.call_args_list
    ] == [1, 2, 4]


def test_fetch_ip_location_connection_error(monkeypatch):

    monkeypatch.setattr(
        "app.external_apis.geolocation_api.settings.GEOLOCATION_API_URL",
        "https://example.com/json"
    )

    monkeypatch.setattr(
        "app.external_apis.geolocation_api.settings.GEOLOCATION_MAX_RETRIES",
        2
    )

    monkeypatch.setattr(
        "app.external_apis.geolocation_api.settings.GEOLOCATION_BACKOFF_BASE",
        1
    )

    mock_client = MagicMock()

    mock_client.get.side_effect = httpx.ConnectError(
        "Connection refused"
    )

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_client

    with patch(
        "app.external_apis.geolocation_api.httpx.Client",
        return_value=mock_context
    ), patch(
        "app.external_apis.geolocation_api.time.sleep"
    ) as mock_sleep:

        result = fetch_ip_location("8.8.8.8")

    assert result is None
    assert mock_client.get.call_count == 3

    assert [
        call.args[0] for call in mock_sleep.call_args_list
    ] == [1, 2]






