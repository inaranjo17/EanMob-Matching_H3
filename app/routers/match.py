# app/routers/match.py (agregar el endpoint)
from fastapi import APIRouter, HTTPException

from app.schemas.match_schema import GeocodeRequest
from app.services.geocoding import geocode_address

router = APIRouter()

@router.post("/maps/geocode")
async def geocode(payload: GeocodeRequest):
    try:
        result = await geocode_address(payload.address)
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))