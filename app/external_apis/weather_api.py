import logging
import time

import httpx

from app.config import settings
from app.exceptions.weather_exceptions import WeatherAPIError, WeatherAPITimeoutError, WeatherAPIResponseError
logger = logging.getLogger(__name__)

def get_weather(location: str) -> dict:

    url = f"{settings.WEATHER_API_BASE_URL}/current.json"

    params = {
        "key": settings.WEATHER_API_KEY,
        "q": location
    }

    max_retries = settings.WEATHER_API_MAX_RETRIES

    for attempt in range(max_retries + 1):

        try:
            with httpx.Client(
                timeout=settings.WEATHER_API_TIMEOUT
            ) as client:

                response = client.get(
                    url,
                    params=params
                )

                response.raise_for_status()

                try:
                    return response.json()

                except ValueError as exc:
                    raise WeatherAPIResponseError(
                        "Weather API returned invalid JSON"
                    ) from exc

        except httpx.TimeoutException as exc:

            logger.warning(
                "Weather API timeout. Attempt %s/%s",
                attempt + 1,
                max_retries + 1
            )

            if attempt == max_retries:
                raise WeatherAPITimeoutError(
                    "Weather API request timed out"
                ) from exc

        except httpx.HTTPStatusError as exc:

            status_code = exc.response.status_code

            # Do not retry client errors except HTTP 429.
            if 400 <= status_code < 500 and status_code != 429:
                raise WeatherAPIError(
                    f"Weather API returned HTTP {status_code}"
                ) from exc

            logger.warning(
                "Weather API returned HTTP %s. Attempt %s/%s",
                status_code,
                attempt + 1,
                max_retries + 1
            )

            if attempt == max_retries:
                raise WeatherAPIError(
                    f"Weather API failed with HTTP {status_code}"
                ) from exc

        except httpx.RequestError as exc:

            logger.warning(
                "Weather API network error. Attempt %s/%s",
                attempt + 1,
                max_retries + 1
            )

            if attempt == max_retries:
                raise WeatherAPIError(
                    "Unable to connect to WeatherAPI"
                ) from exc

        # Exponential backoff before the next attempt.
        if attempt < max_retries:

            delay = (
                settings.WEATHER_API_BACKOFF_BASE
                * (2 ** attempt)
            )

            logger.info(
                "Retrying WeatherAPI request in %s seconds",
                delay
            )

            time.sleep(delay)
