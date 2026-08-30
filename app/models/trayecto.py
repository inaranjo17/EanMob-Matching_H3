# app/models/trayecto.py
from sqlalchemy import Column, Integer, String, DECIMAL, TIMESTAMP, Enum
from app.database import Base
import enum

class TripStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

class Trayecto(Base):
    __tablename__ = "trayectos"

    id = Column(Integer, primary_key=True)
    conductor_id = Column(Integer, nullable=False)
    nombre_prestador = Column(String(100), nullable=False)
    origen = Column(String(200), nullable=False)
    destino = Column(String(200), nullable=False)
    hora_inicio = Column(TIMESTAMP, nullable=False)
    hora_fin = Column(TIMESTAMP, nullable=True)
    origin_lat = Column(DECIMAL(10, 8), nullable=True)
    origin_lng = Column(DECIMAL(11, 8), nullable=True)
    destination_lat = Column(DECIMAL(10, 8), nullable=True)
    destination_lng = Column(DECIMAL(11, 8), nullable=True)
    origin_h3 = Column(String(20), nullable=True)
    destination_h3 = Column(String(20), nullable=True)
    available_seats = Column(Integer, nullable=False, default=1)
    cost_per_passenger = Column(DECIMAL(10, 2), nullable=True)
    status = Column(Enum(TripStatus), nullable=False, default=TripStatus.open)
    vehicle_id = Column(Integer, nullable=True)