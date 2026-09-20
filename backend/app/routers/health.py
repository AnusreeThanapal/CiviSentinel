import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SystemHealth, ModelVersion
from app.schemas import SystemHealthResponseSchema

logger = logging.getLogger("backend.routers.health")

router = APIRouter(tags=["System Health & Liveness"])

@router.get("/healthz")
def get_liveness():
    """
    Plain liveness check endpoint for load balancers and orchestrators.
    """
    return {"status": "ok", "service": "civic-disruption-backend"}

@router.get("/system-health", response_model=SystemHealthResponseSchema)
def get_system_health(db: Session = Depends(get_db)):
    """
    Returns pipeline system health status including recent Airflow DAG run status
    and active model training timestamp/weights.
    """
    # 1. Fetch latest system_health record written by Airflow DAG
    health_rec = db.query(SystemHealth).order_by(SystemHealth.id.desc()).first()
    dag_status = health_rec.dag_status if health_rec else "UNKNOWN (No DAG runs recorded)"
    
    # 2. Fetch active model version
    active_model = db.query(ModelVersion).filter(ModelVersion.is_active == True).order_by(ModelVersion.id.desc()).first()
    
    model_last_retrained = None
    active_model_id = None
    active_model_weights = {}
    
    if active_model:
        model_last_retrained = active_model.trained_at.isoformat() + "Z" if active_model.trained_at else None
        active_model_id = active_model.id
        active_model_weights = active_model.weights or {}
    else:
        # Fallback default baseline weights
        active_model_weights = {
            "verified_news": 0.9,
            "social": 0.4,
            "anonymous": 0.2,
            "sensor": 0.85
        }

    return SystemHealthResponseSchema(
        dag_status=dag_status,
        model_last_retrained=model_last_retrained,
        active_model_id=active_model_id,
        active_model_weights=active_model_weights,
        service_status="HEALTHY"
    )
