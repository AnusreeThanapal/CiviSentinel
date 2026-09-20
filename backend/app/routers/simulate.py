import logging
from fastapi import APIRouter, HTTPException, status
from app.schemas import SimulateRequestSchema, SimulateResponseSchema
from app.kafka_client import publish_raw_event
from app.config import settings

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
    
    return SimulateResponseSchema(
        status="SUCCESS",
        message=f"Successfully injected {total_published} synthetic event(s) into Kafka processing pipeline.",
        sensor_events_published=sensor_count,
        citizen_reports_published=report_count
    )
