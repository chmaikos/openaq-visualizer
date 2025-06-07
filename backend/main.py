import os
from datetime import datetime, timedelta
from typing import List, Optional
from bson import ObjectId

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient, ASCENDING, DESCENDING

from models import AlertPreference, UserPreferences, AlertAcknowledgment, AlertHistory

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# MongoDB setup
MONGO_URL = os.getenv("MONGODB_URI", "mongodb://mongodb:27017/")
mongo = MongoClient(MONGO_URL)
db = mongo["air_quality"]
latest = db["latest_pm25"]
alerts = db["alerts"]
user_prefs = db["user_preferences"]

# Create indexes
alerts.create_index([("timestamp", DESCENDING)])
alerts.create_index([("severity", ASCENDING)])
alerts.create_index([("lat", ASCENDING), ("lon", ASCENDING)])
user_prefs.create_index([("user_id", ASCENDING)], unique=True)

def serialize_mongo_doc(doc):
    if doc is None:
        return None
    if isinstance(doc, dict):
        return {k: serialize_mongo_doc(v) for k, v in doc.items()}
    if isinstance(doc, list):
        return [serialize_mongo_doc(item) for item in doc]
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, datetime):
        return doc.isoformat()
    return doc

class AQPoint(BaseModel):
    lat: float
    lon: float
    pm25: float | None
    unit: str | None = None
    timestamp: str | None = None

# User Preferences Endpoints
@app.post("/api/preferences/{user_id}")
async def create_user_preferences(user_id: str, preferences: AlertPreference):
    """Create or update user preferences."""
    try:
        result = user_prefs.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "user_id": user_id,
                    "alert_preferences": preferences.dict(),
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {"created_at": datetime.utcnow()}
            },
            upsert=True
        )
        
        # Get the updated document
        updated_prefs = user_prefs.find_one({"user_id": user_id})
        if not updated_prefs:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated preferences")
            
        return serialize_mongo_doc(updated_prefs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/preferences/{user_id}")
async def get_user_preferences(user_id: str):
    """Get user preferences."""
    prefs = user_prefs.find_one({"user_id": user_id})
    if not prefs:
        raise HTTPException(status_code=404, detail="Preferences not found")
    return serialize_mongo_doc(prefs)

# Alert History Endpoints
@app.get("/api/alerts/history")
async def get_alert_history(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    severity: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    """Get alert history with optional filters."""
    query = {}
    if start_date:
        query["timestamp"] = {"$gte": start_date}
    if end_date:
        query.setdefault("timestamp", {})["$lte"] = end_date
    if severity:
        query["severity"] = severity

    cursor = alerts.find(
        query,
        {"_id": 0}
    ).sort("timestamp", DESCENDING).limit(limit)

    return [serialize_mongo_doc(doc) for doc in cursor]

@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, acknowledgment: AlertAcknowledgment):
    """Acknowledge an alert."""
    result = alerts.update_one(
        {"alert_id": alert_id},
        {
            "$set": {
                "acknowledged": True,
                "acknowledged_by": acknowledgment.user_id,
                "acknowledged_at": acknowledgment.acknowledged_at,
                "acknowledgment_comment": acknowledgment.comment
            }
        }
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "success"}

# Historical Data Analysis Endpoints
@app.get("/api/analysis/daily")
async def get_daily_analysis(
    lat: float,
    lon: float,
    days: int = Query(7, le=30)
):
    """Get daily PM2.5 statistics for a location."""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    pipeline = [
        {
            "$match": {
                "lat": lat,
                "lon": lon,
                "timestamp": {"$gte": start_date}
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$timestamp"
                    }
                },
                "avg_pm25": {"$avg": "$pm25"},
                "max_pm25": {"$max": "$pm25"},
                "min_pm25": {"$min": "$pm25"},
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]
    
    results = list(alerts.aggregate(pipeline))
    return results

@app.get("/api/analysis/trends")
async def get_trends(
    lat: float,
    lon: float,
    days: int = Query(7, le=30)
):
    """Get PM2.5 trends for a location."""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    pipeline = [
        {
            "$match": {
                "lat": lat,
                "lon": lon,
                "timestamp": {"$gte": start_date}
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d %H:00",
                        "date": "$timestamp"
                    }
                },
                "pm25": {"$avg": "$pm25"}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]
    
    results = list(alerts.aggregate(pipeline))
    return results

# Latest Readings Endpoint (existing)
@app.get("/api/latest", response_model=List[AQPoint])
def get_latest():
    """Returns the latest PM2.5 for each (lat, lon)."""
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
