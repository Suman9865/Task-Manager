import asyncio
import logging

import httpx

from app.core.config import settings
from app.core.http_client import get_http_client
from app.exceptions.weather_exceptions import (
    WeatherAPIError, WeatherAPITimeoutError, WeatherAPIResponseError,
)

logger = logging.getLogger(__name__)


async def get_weather(location: str) -> dict:
    url = f"{settings.WEATHER_API_BASE_URL}/current.json"
    params = {"key": settings.WEATHER_API_KEY, "q": location}
    max_retries = settings.WEATHER_API_MAX_RETRIES

    for attempt in range(max_retries + 1):
        try:
            response = await get_http_client().get(
                url, params=params, timeout=settings.WEATHER_API_TIMEOUT
            )
            response.raise_for_status()
            try:
                data = response.json()
            except ValueError as exc:
                raise WeatherAPIResponseError("Weather API returned invalid JSON") from exc
            if not isinstance(data, dict):
                raise WeatherAPIResponseError("Weather API returned an invalid response")
            return data
        except httpx.TimeoutException as exc:
            logger.warning("Weather API timeout. Attempt %s/%s", attempt + 1, max_retries + 1)
            if attempt == max_retries:
                raise WeatherAPITimeoutError("Weather API request timed out") from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if 400 <= status < 500 and status != 429:
                raise WeatherAPIError(f"Weather API returned HTTP {status}") from exc
            logger.warning("Weather API returned HTTP %s. Attempt %s/%s", status, attempt + 1, max_retries + 1)
            if attempt == max_retries:
                raise WeatherAPIError(f"Weather API failed with HTTP {status}") from exc
        except httpx.RequestError as exc:
            logger.warning("Weather API network error. Attempt %s/%s", attempt + 1, max_retries + 1)
            if attempt == max_retries:
                raise WeatherAPIError("Unable to connect to WeatherAPI") from exc

        if attempt < max_retries:
            await asyncio.sleep(settings.WEATHER_API_BACKOFF_BASE * (2 ** attempt))
