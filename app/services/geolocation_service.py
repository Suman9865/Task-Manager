import ipaddress
import logging

from app.external_apis.geolocation_api import fetch_ip_location

logger = logging.getLogger(__name__)


async def get_ip_location(ip_address: str) -> dict:
    fallback = {"country": None, "city": None}
    try:
        ip = ipaddress.ip_address(ip_address)
    except ValueError:
        logger.warning("Invalid IP address received for geolocation")
        return fallback

    if not ip.is_global:
        logger.info("Skipping geolocation for non-public IP address")
        return fallback

    data = await fetch_ip_location(str(ip))
    if data is None or not data.get("success"):
        if data is not None:
            logger.warning("Geolocation provider returned an unsuccessful response")
        return fallback

    return {"country": data.get("country"), "city": data.get("city")}
