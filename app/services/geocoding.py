# app/services/geocoding.py
import os

import h3
import httpx
from dotenv import load_dotenv

load_dotenv()

BACKEND_GOOGLE_MAPS_API_KEY = os.getenv("BACKEND_GOOGLE_MAPS_API_KEY")
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
H3_RESOLUTION = int(os.getenv("H3_RESOLUTION", "9"))

async def geocode_address(address: str) -> dict:
    params = {"address": f"{address}, Bogotá, Colombia", "key": BACKEND_GOOGLE_MAPS_API_KEY}
    async with httpx.AsyncClient() as client:
        response = await client.get(GEOCODE_URL, params=params)
        data = response.json()

    if data["status"] != "OK":
        raise ValueError(f"Geocoding falló: {data['status']}")

    location = data["results"][0]["geometry"]["location"]
    lat, lng = location["lat"], location["lng"]
    h3_index = h3.latlng_to_cell(lat, lng, H3_RESOLUTION)

    return {"lat": lat, "lng": lng, "h3_index": h3_index}