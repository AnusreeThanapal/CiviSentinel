import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert
from app.schemas import AlertSchema

logger = logging.getLogger("backend.routers.alerts")
router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("", response_model=List[AlertSchema])
def get_alerts(
    limit: int = Query(default=50, ge=1, le=200, description="Max number of alerts to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    type: Optional[str] = Query(default=None, description="Filter by disruption type (flooding, waterlogging, power_outage)"),
    db: Session = Depends(get_db)
):
    """
    Returns paginated alert history from Postgres.
    """
    query = db.query(Alert)
    if type:
        query = query.filter(Alert.type == type)
    
    alerts = query.order_by(Alert.created_at.desc()).offset(offset).limit(limit).all()
    
    # Format DB model to Schema output
    result = []
    for a in alerts:
        result.append(AlertSchema(
            alert_id=a.alert_id,
            type=a.type,
            location={
                "lat": a.lat,
                "lng": a.lng,
                "name": a.location_name or "Unknown Location"
            },
            trust_score=a.trust_score,
            reasoning=a.reasoning or "",
            contributing_signals=a.contributing_signals or [],
            timestamp=a.created_at.isoformat() + "Z"
        ))
    return result

@router.get("/{alert_id}", response_model=AlertSchema)
def get_alert_by_id(alert_id: str, db: Session = Depends(get_db)):
    """
    Returns full details for a single alert including contributing signals.
    """
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert with ID '{alert_id}' not found.")
    
    return AlertSchema(
        alert_id=alert.alert_id,
        type=alert.type,
        location={
            "lat": alert.lat,
            "lng": alert.lng,
            "name": alert.location_name or "Unknown Location"
        },
        trust_score=alert.trust_score,
        reasoning=alert.reasoning or "",
        contributing_signals=alert.contributing_signals or [],
        timestamp=alert.created_at.isoformat() + "Z"
    )
