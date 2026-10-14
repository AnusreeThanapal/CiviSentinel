import time
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from app.schemas import SimulateRequestSchema, SimulateResponseSchema
from app.kafka_client import publish_raw_event, get_kafka_producer, process_alert_message
from app.config import settings
from app.database import SessionLocal
from app.models import TrustWeight

logger = logging.getLogger("backend.routers.simulate")
router = APIRouter(prefix="/simulate", tags=["Simulation Injector"])

@router.post("", response_model=SimulateResponseSchema, status_code=status.HTTP_201_CREATED)
def trigger_simulation(payload: SimulateRequestSchema):
    """
    Simulates urban disruption events by publishing raw sensor readings and multi-lingual
    citizen/news reports onto Kafka raw topics for Spark Structured Streaming correlation.
    """
    sensor_count = 0
    report_count = 0
    
    # 1. Publish Sensor Events
    for s_event in payload.sensor_events:
        event_dict = s_event.model_dump()
        success = publish_raw_event(settings.KAFKA_SENSOR_TOPIC, event_dict)
        if success:
            sensor_count += 1
            
    # 2. Publish Citizen Reports
    for c_report in payload.citizen_reports:
        report_dict = c_report.model_dump()
        success = publish_raw_event(settings.KAFKA_REPORT_TOPIC, report_dict)
        if success:
            report_count += 1
            
    total_published = sensor_count + report_count
    logger.info(f"Simulation trigger processed. Published {sensor_count} sensor events and {report_count} citizen reports.")

    # 3. If Kafka/Spark broker is offline, execute correlation logic locally
    if get_kafka_producer() is None and total_published > 0:
        logger.info("Kafka/Spark offline: running standalone correlation engine fallback.")
        db = SessionLocal()
        weights = {"verified_news": 0.9, "social": 0.4, "anonymous": 0.2, "sensor": 0.85}
        try:
            db_weights = db.query(TrustWeight).all()
            for w in db_weights:
                weights[w.key] = float(w.value)
        except Exception:
            pass
        finally:
            db.close()

        # Calculate report score
        rep_weight_sum = sum(weights.get(r.source_type, 0.2) for r in payload.citizen_reports)
        report_score = min(1.0, rep_weight_sum)
        sensor_score = min(1.0, weights.get("sensor", 0.85) if payload.sensor_events else 0.0)

        if payload.citizen_reports and payload.sensor_events:
            trust_score = min(1.0, (report_score * 0.5) + (sensor_score * 0.5) + 0.15)
        elif payload.citizen_reports:
            trust_score = report_score
        else:
            trust_score = sensor_score

        # Check threshold (0.6)
        if trust_score >= 0.6:
            ref_lat = payload.sensor_events[0].lat if payload.sensor_events else (payload.citizen_reports[0].lat if payload.citizen_reports else 13.0827)
            ref_lng = payload.sensor_events[0].lng if payload.sensor_events else (payload.citizen_reports[0].lng if payload.citizen_reports else 80.2707)
            ref_loc = payload.sensor_events[0].location_name if payload.sensor_events and payload.sensor_events[0].location_name else (payload.citizen_reports[0].location_name if payload.citizen_reports and payload.citizen_reports[0].location_name else "Chennai Central")

            contributing = []
            for s in payload.sensor_events:
                contributing.append({"kind": "sensor", "sensor_id": s.sensor_id, "value": s.value, "unit": s.unit})
            for r in payload.citizen_reports:
                contributing.append({"kind": "report", "text": r.text, "language": r.language, "source_type": r.source_type})

            all_text = " ".join(r.text for r in payload.citizen_reports).lower()
            s_types = [s.sensor_type for s in payload.sensor_events]
            if "power" in all_text or "power_grid" in s_types or "மின்சார" in all_text:
                disruption_type = "power_outage"
            elif "waterlogging" in all_text or "தேங்கிய" in all_text:
                disruption_type = "waterlogging"
            else:
                disruption_type = "flooding"

            alert_payload = {
                "alert_id": f"ALT-LIVE-{int(time.time())}",
                "type": disruption_type,
                "location": {"lat": ref_lat, "lng": ref_lng, "name": ref_loc},
                "trust_score": round(trust_score, 2),
                "reasoning": f"{len(payload.sensor_events)} sensor signal(s) + {len(payload.citizen_reports)} report(s), trust score {trust_score:.2f}",
                "contributing_signals": contributing,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            process_alert_message(alert_payload)
    
    return SimulateResponseSchema(
        status="SUCCESS",
        message=f"Successfully injected {total_published} synthetic event(s) into Kafka processing pipeline.",
        sensor_events_published=sensor_count,
        citizen_reports_published=report_count
    )

