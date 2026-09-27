from datetime import datetime, timedelta
from math import atan2, cos, radians, sin, sqrt

import h3
from sqlalchemy.orm import Session

from app.models.trayecto import Trayecto, TripStatus
from app.services.geocoding import geocode_address

TIME_TOLERANCE_MINUTES = 30
MAX_DISTANCE_KM = 0.5  # ~ radio de grid_disk(k=1) en resolución 9


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distancia en línea recta entre dos coordenadas, en kilómetros."""
    R = 6371
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def score_distance(distance_km: float) -> float:
    """1.0 = misma ubicación, 0.0 = en el borde de MAX_DISTANCE_KM o más lejos."""
    return max(0.0, 1 - (distance_km / MAX_DISTANCE_KM))


def score_time(diff_minutes: float) -> float:
    """1.0 = mismo horario exacto, 0.0 = en el borde de TIME_TOLERANCE_MINUTES o más."""
    return max(0.0, 1 - (diff_minutes / TIME_TOLERANCE_MINUTES))


async def find_candidates(db: Session, origin_address: str, target_time: datetime):
    geo = await geocode_address(origin_address)
    passenger_lat, passenger_lng = geo["lat"], geo["lng"]
    passenger_h3 = geo["h3_index"]

    candidate_cells = h3.grid_disk(passenger_h3, 1)
    time_min = target_time - timedelta(minutes=TIME_TOLERANCE_MINUTES)
    time_max = target_time + timedelta(minutes=TIME_TOLERANCE_MINUTES)

    trips = (
        db.query(Trayecto)
        .filter(Trayecto.status == TripStatus.open)
        .filter(Trayecto.origin_h3.in_(candidate_cells))
        .filter(Trayecto.hora_inicio.between(time_min, time_max))
        .filter(Trayecto.available_seats > 0)
        .all()
    )

    scored = []
    for trip in trips:
        distance_km = haversine_km(
            passenger_lat, passenger_lng, float(trip.origin_lat), float(trip.origin_lng)
        )
        diff_minutes = abs((trip.hora_inicio - target_time).total_seconds()) / 60

        s_dist = score_distance(distance_km)
        s_time = score_time(diff_minutes)
        relevance_score = round(0.6 * s_dist + 0.4 * s_time, 4)

        scored.append((trip, relevance_score))

    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored
