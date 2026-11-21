class WeatherAPIError(Exception):
    """Base exception for weather APIerrors."""
    

class WeatherAPITimeoutError(WeatherAPIError):
    """Raised when the weather API request times out."""


class WeatherAPIResponseError(WeatherAPIError):
    """Raised when the weather API returns an invalid response."""