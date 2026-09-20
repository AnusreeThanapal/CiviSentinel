from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

# --- Raw Kafka Payload Schemas ---

class RawSensorEventSchema(BaseModel):
    sensor_id: str = Field(..., example="SENS-WATER-001")
    sensor_type: Literal["traffic", "water_level", "power_grid"] = Field(..., example="water_level")
    value: float = Field(..., example=4.5)
    unit: str = Field(..., example="meters")
    lat: float = Field(..., example=13.0827)
    lng: float = Field(..., example=80.2707)
    location_name: str = Field(..., example="T. Nagar Canal")
    event_time: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

class RawCitizenReportSchema(BaseModel):
    report_id: str = Field(..., example="REP-TA-001")
    text: str = Field(..., example="தி நகரில் வெள்ளப்பெருக்கு (Flooding in T. Nagar)")
    language: Literal["ta", "en"] = Field(..., example="ta")
    source_type: Literal["verified_news", "social", "anonymous"] = Field(..., example="verified_news")
    lat: float = Field(..., example=13.0830)
    lng: float = Field(..., example=80.2710)
    location_name: str = Field(..., example="T. Nagar Central")
    event_time: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

# --- Alert Location & Signal Schemas ---

class LocationSchema(BaseModel):
    lat: float
    lng: float
    name: str

class ContributingSignalSchema(BaseModel):
    kind: Literal["sensor", "report"]
    sensor_id: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    text: Optional[str] = None
    language: Optional[Literal["ta", "en"]] = None
    source_type: Optional[str] = None

class AlertSchema(BaseModel):
    alert_id: str
    type: Literal["flooding", "waterlogging", "power_outage"]
    location: LocationSchema
    trust_score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    contributing_signals: List[Dict[str, Any]]
    timestamp: str

    class Config:
        from_attributes = True

# --- Simulation Request Schema ---

class SimulateRequestSchema(BaseModel):
    scenario_name: Optional[str] = Field(default="Flooding Scenario")
    sensor_events: List[RawSensorEventSchema] = Field(default_factory=list)
    citizen_reports: List[RawCitizenReportSchema] = Field(default_factory=list)

class SimulateResponseSchema(BaseModel):
    status: str
    message: str
    sensor_events_published: int
    citizen_reports_published: int

# --- System Health Schema ---

class SystemHealthResponseSchema(BaseModel):
    dag_status: str
    model_last_retrained: Optional[str] = None
    active_model_id: Optional[int] = None
    active_model_weights: Dict[str, float] = Field(default_factory=dict)
    service_status: str = "HEALTHY"

# --- Config Schemas ---

class TrustWeightsSchema(BaseModel):
    weights: Dict[str, float]
