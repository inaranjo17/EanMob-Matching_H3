# app/routers/match.py (agregar el endpoint)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.h3_matching import find_candidates
from app.schemas.match_schema import MatchFindRequest, MatchFindResponse, GeocodeRequest
from app.services.geocoding import geocode_address

router = APIRouter()

@router.post("/maps/geocode")
async def geocode(payload: GeocodeRequest):
    try:
        result = await geocode_address(payload.address)
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/match/find", response_model=MatchFindResponse)
def match_find(payload: MatchFindRequest, db: Session = Depends(get_db)):
    results = find_candidates(db, payload.origin_h3, payload.target_time)
    return {"candidates": results}