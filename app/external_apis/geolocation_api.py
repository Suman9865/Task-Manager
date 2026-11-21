import logging
import time

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def fetch_ip_location(ip_address: str) -> dict | None:
    """
    Fetch location information for an IP address
    from the external geolocation API.

    Returns:
        dict: API response on success.
        None: If the external API request fails.
    """

    url = f"{settings.GEOLOCATION_API_URL.rstrip('/')}/{ip_address}"

    total_attempts = settings.GEOLOCATION_MAX_RETRIES + 1

    for attempt in range(total_attempts):

        try:
            with httpx.Client(
                timeout=settings.GEOLOCATION_TIMEOUT
            ) as client:

                response = client.get(url)
                response.raise_for_status()

                data = response.json()

                if not isinstance(data, dict):
                    logger.warning(
                        "Geolocation API returned an invalid response format"
                    )
                    return None

                return data

        except httpx.HTTPStatusError as exc:

            status_code = exc.response.status_code

            # Do not retry permanent client errors.
            if status_code != 429 and status_code < 500:
                logger.warning(
                    "Geolocation API returned HTTP %s",
                    status_code
                )
                return None

            logger.warning(
                "Temporary geolocation API error: HTTP %s",
                status_code
            )

        except httpx.RequestError:
            logger.warning(
                "Geolocation API network or timeout error"
            )

        except ValueError:
            logger.warning(
                "Geolocation API returned invalid JSON"
            )
            return None

        # Exponential backoff before the next attempt.
        if attempt < settings.GEOLOCATION_MAX_RETRIES:

            delay = (
                settings.GEOLOCATION_BACKOFF_BASE * (2 ** attempt)
            )

            logger.info(
                "Retrying geolocation request in %s seconds",
                delay
            )

            time.sleep(delay)

    logger.error(
        "Geolocation API request failed after %s attempts",
        total_attempts
    )

    return None