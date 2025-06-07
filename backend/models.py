from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr

class AlertPreference(BaseModel):
    severity_levels: List[str] = ["critical", "alert"]  # Default to critical and alert
    location_filter: Optional[List[dict]] = None  # List of {lat, lon, radius} objects
    min_threshold: Optional[float] = None
    max_threshold: Optional[float] = None
    notification_channels: List[str] = ["web"]  # Default to web notifications

class UserPreferences(BaseModel):
    user_id: str
    email: Optional[EmailStr] = None
    alert_preferences: AlertPreference
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

class AlertAcknowledgment(BaseModel):
    alert_id: str
    user_id: str
    acknowledged_at: datetime = datetime.utcnow()
    comment: Optional[str] = None

class AlertHistory(BaseModel):
    alert_id: str
    lat: float
    lon: float
    pm25: float
    unit: str
    severity: str
    threshold: float
    description: str
    timestamp: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    acknowledgment_comment: Optional[str] = None 