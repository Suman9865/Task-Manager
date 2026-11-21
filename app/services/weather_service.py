
import logging

from app.external_apis.weather_api import get_weather
from app.exceptions.weather_exceptions import WeatherAPIError

logger = logging.getLogger(__name__)


def get_weather_service(location: str) -> dict:

    try:
        weather_data = get_weather(location)

        return {
            "location": location,
            "available": True,
            "weather": weather_data
        }

    except WeatherAPIError as exc:

        logger.warning(
            "Unable to retrieve weather for %s: %s",
            location,
            exc
        )

        return {
            "location": location,
            "available": False,
            "weather": None,
            "message": "Weather information is currently unavailable."
        }
