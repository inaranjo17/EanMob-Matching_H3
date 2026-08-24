## app/schemas/match_schema.py
from pydantic import BaseModel


class GeocodeRequest(BaseModel):
    address: str