from fastapi import APIRouter, Query
from app.services.weather_service import get_weather_service

router = APIRouter(tags=["Weather"])


@router.get("/weather")
async def get_weather(location: str = Query(..., min_length=1)):
    return await get_weather_service(location)
