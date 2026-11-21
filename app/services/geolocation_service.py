import ipaddress
import logging

from app.external_apis.geolocation_api import fetch_ip_location

logger = logging.getLogger(__name__)


def get_ip_location(ip_address: str) -> dict:
    """
    Retrieve country and city information for a public IP address.

    Returns fallback values if geolocation is unavailable.
    """

    fallback = {
        "country": None,
        "city": None
    }

    # 1. Validate IP address.
    try:
        ip = ipaddress.ip_address(ip_address)

    except ValueError:
        logger.warning("Invalid IP address received for geolocation")
        return fallback

    # 2. Skip private, loopback and other non-public IP addresses.
    if not ip.is_global:
        logger.info("Skipping geolocation for non-public IP address")
        return fallback

    # 3. Call external geolocation API.
    data = fetch_ip_location(str(ip))

    if data is None:
        return fallback

    # 4. Check API-level success.
    if not data.get("success"):
        logger.warning(
            "Geolocation provider returned an unsuccessful response"
        )
        return fallback

    # 5. Extract location information.
    return {
        "country": data.get("country"),
        "city": data.get("city")
    }