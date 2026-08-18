# app/main.py
from fastapi import FastAPI
from app.routers import health

app = FastAPI(
    title="EanMob Geo-Matching Service",
    description="Servicio de matching inteligente con H3",
    version="0.1.0",
)

app.include_router(health.router)