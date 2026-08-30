## app/schemas/match_schema.py
from pydantic import BaseModel
from datetime import datetime


class GeocodeRequest(BaseModel):
    address: str

class MatchFindRequest(BaseModel):
    origin_h3: str
    target_time: datetime

class MatchCandidate(BaseModel):
    id: int
    origen: str
    destino: str
    hora_inicio: datetime
    hora_fin: datetime | None
    nombre_prestador: str

class MatchFindResponse(BaseModel):
    candidates: list[MatchCandidate]