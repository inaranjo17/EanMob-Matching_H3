# app/routers/match.py (agregar el endpoint)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.match_schema import GeocodeRequest, MatchFindRequest, MatchFindResponse, MatchCandidate
from app.services.geocoding import geocode_address
from app.services.h3_matching import find_candidates

router = APIRouter()

@router.post("/maps/geocode")
async def geocode(payload: GeocodeRequest): 
    try:
        result = await geocode_address(payload.address)
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/match/find", response_model=MatchFindResponse)
async def match_find(payload: MatchFindRequest, db: Session = Depends(get_db)):
    scored_trips = await find_candidates(db, payload.origin_address, payload.target_time)
    candidates = [
        MatchCandidate(
            id=trip.id,
            origen=trip.origen,
            destino=trip.destino,
            hora_inicio=trip.hora_inicio,
            hora_fin=trip.hora_fin,
            nombre_prestador=trip.nombre_prestador,
            score=score,
        )
        for trip, score in scored_trips
    ]
    return {"candidates": candidates}
