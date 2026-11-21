
from fastapi import APIRouter, Query

from app.services.weather_service import get_weather_service

router = APIRouter(tags=["Weather"])


@router.get("/weather")
def get_weather(
    location: str = Query(..., min_length=1)
):
    return get_weather_service(location)
