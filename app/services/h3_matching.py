# app/services/h3_matching.py
from datetime import datetime, timedelta
import h3
from sqlalchemy.orm import Session
from app.models.trayecto import Trayecto, TripStatus

TIME_TOLERANCE_MINUTES = 30

def find_candidates(db: Session, passenger_origin_h3: str, target_time: datetime):
    # 1. Vecinos H3 (celda propia + anillo de 1 alrededor = 7 celdas)
    candidate_cells = h3.grid_disk(passenger_origin_h3, 1)

    # 2. Ventana de tiempo
    time_min = target_time - timedelta(minutes=TIME_TOLERANCE_MINUTES)
    time_max = target_time + timedelta(minutes=TIME_TOLERANCE_MINUTES)

    # 3. Query real contra trayectos
    results = (
        db.query(Trayecto)
        .filter(Trayecto.status == TripStatus.open)
        .filter(Trayecto.origin_h3.in_(candidate_cells))
        .filter(Trayecto.hora_inicio.between(time_min, time_max))
        .filter(Trayecto.available_seats > 0)
        .all()
    )
    return results