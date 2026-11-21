import asyncio
import logging

import httpx

from app.core.config import settings
from app.core.http_client import get_http_client

logger = logging.getLogger(__name__)


async def fetch_ip_location(ip_address: str) -> dict | None:
    url = f"{settings.GEOLOCATION_API_URL.rstrip('/')}/{ip_address}"
    total_attempts = settings.GEOLOCATION_MAX_RETRIES + 1

    for attempt in range(total_attempts):
        try:
            response = await get_http_client().get(
                url, timeout=settings.GEOLOCATION_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                return data
            logger.warning("Geolocation API returned an invalid response format")
            return None
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status != 429 and status < 500:
                logger.warning("Geolocation API returned HTTP %s", status)
                return None
            logger.warning("Temporary geolocation API error: HTTP %s", status)
        except httpx.RequestError:
            logger.warning("Geolocation API network or timeout error")
        except ValueError:
            logger.warning("Geolocation API returned invalid JSON")
            return None

        if attempt < settings.GEOLOCATION_MAX_RETRIES:
            delay = settings.GEOLOCATION_BACKOFF_BASE * (2 ** attempt)
            await asyncio.sleep(delay)

    logger.error("Geolocation API request failed after %s attempts", total_attempts)
    return None
