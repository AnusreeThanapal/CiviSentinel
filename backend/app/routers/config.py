import logging
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TrustWeight
from app.schemas import TrustWeightsSchema

logger = logging.getLogger("backend.routers.config")
router = APIRouter(prefix="/config/trust-weights", tags=["Trust Weights Config"])

@router.get("", response_model=TrustWeightsSchema)
def get_trust_weights(db: Session = Depends(get_db)):
    """
    Returns current trust weights key-value mapping from Postgres DB.
    Spark reads this table on each micro-batch.
    """
    weights_rows = db.query(TrustWeight).all()
    weights_dict = {w.key: w.value for w in weights_rows}
    
    if not weights_dict:
        # Defaults if empty
        weights_dict = {
            "verified_news": 0.9,
            "social": 0.4,
            "anonymous": 0.2,
            "sensor": 0.85
        }
        
    return TrustWeightsSchema(weights=weights_dict)

@router.put("", response_model=TrustWeightsSchema)
def update_trust_weights(payload: TrustWeightsSchema, db: Session = Depends(get_db)):
    """
    Updates trust weights in Postgres DB.
    The next Spark Structured Streaming micro-batch will automatically fetch these updated weights.
    """
    if not payload.weights:
        raise HTTPException(status_code=400, detail="Weights dictionary cannot be empty.")
        
    updated_dict = {}
    for key, val in payload.weights.items():
        if not isinstance(val, (int, float)) or val < 0.0 or val > 1.0:
            raise HTTPException(status_code=400, detail=f"Weight value for '{key}' must be a float between 0.0 and 1.0.")
            
        existing = db.query(TrustWeight).filter(TrustWeight.key == key).first()
        if existing:
            existing.value = float(val)
        else:
            new_weight = TrustWeight(key=key, value=float(val))
            db.add(new_weight)
        updated_dict[key] = float(val)
        
    db.commit()
    logger.info(f"Updated trust_weights in Postgres: {updated_dict}")
    return TrustWeightsSchema(weights=updated_dict)
