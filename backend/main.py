import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pymongo import MongoClient

app = FastAPI()

# CORS (πρέπει να ταιριάζει με το URL του React)
origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# MongoDB setup
MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongodb:27017/")
mongo = MongoClient(MONGO_URL)
db = mongo["air_quality"]
latest = db["latest_pm25"]


class AQPoint(BaseModel):
    lat: float
    lon: float
    pm25: float | None
    unit: str | None = None
    timestamp: str | None = None


@app.get("/api/latest", response_model=list[AQPoint])
def get_latest():
    """
    Επιστρέφει το πιο πρόσφατο PM2.5 για κάθε (lat, lon).
    """
    docs_cursor = latest.find(
        {"lat": {"$type": ["double", "int"]}, "lon": {"$type": ["double", "int"]}},
        {"_id": 0, "lat": 1, "lon": 1, "pm25": 1, "unit": 1, "timestamp": 1},
    )

    points = []
    for doc in docs_cursor:
        try:
            p = AQPoint(
                lat=float(doc["lat"]),
                lon=float(doc["lon"]),
                pm25=doc.get("pm25", None),
                unit=doc.get("unit", None),
                timestamp=doc.get("timestamp", None),
            )
            points.append(p)
        except (TypeError, ValueError):
            continue

    return JSONResponse(content=[p.dict() for p in points])
