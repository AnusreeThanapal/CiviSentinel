import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

from app.config import settings
from app.database import SessionLocal
from app.models import Alert
from app.websocket_manager import manager

logger = logging.getLogger("backend.kafka")

producer = None
consumer_task = None
is_running = False
main_event_loop = None


def json_serializer(data: Dict[str, Any]) -> bytes:
    return json.dumps(data).encode("utf-8")


def get_kafka_producer():
    """Initializes and returns a Kafka producer instance if available."""
    global producer
    if producer is not None:
        return producer
    
    try:
        from kafka import KafkaProducer
        logger.info(f"Connecting Kafka Producer to {settings.KAFKA_BOOTSTRAP_SERVERS}...")
        producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=json_serializer,
            request_timeout_ms=5000,
            retries=3
        )
        logger.info("Kafka Producer connected successfully.")
        return producer
    except Exception as e:
        logger.warning(f"Could not connect Kafka Producer ({e}). Simulation endpoint will run in mock mode if Kafka is unreachable.")
        return None


def publish_raw_event(topic: str, payload: Dict[str, Any]) -> bool:
    """Publishes a raw event payload to the specified Kafka topic."""
    p = get_kafka_producer()
    if p is None:
        logger.warning(f"Kafka producer unavailable. Mocking publish to topic '{topic}' with payload: {payload}")
        return True
    
    try:
        p.send(topic, value=payload)
        p.flush(timeout=3)
        logger.info(f"Published event to topic '{topic}'")
        return True
    except Exception as e:
        logger.error(f"Error publishing to Kafka topic '{topic}': {e}")
        return False


def process_alert_message(alert_data: Dict[str, Any]):
    """
    Callback invoked on consuming an alert message:
    1. Persists alert into Postgres DB.
    2. Broadcasts alert JSON to connected WebSocket clients.
    """
    logger.info(f"Received alert from Kafka: {alert_data.get('alert_id')} (Type: {alert_data.get('type')}, Trust: {alert_data.get('trust_score')})")
    
    db = SessionLocal()
    try:
        alert_id = alert_data.get("alert_id", f"ALT-{int(datetime.utcnow().timestamp())}")
        location = alert_data.get("location", {})
        
        existing_alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
        if not existing_alert:
            new_alert = Alert(
                alert_id=alert_id,
                type=alert_data.get("type", "flooding"),
                lat=float(location.get("lat", 0.0)),
                lng=float(location.get("lng", 0.0)),
                location_name=location.get("name", "Unknown Location"),
                trust_score=float(alert_data.get("trust_score", 0.0)),
                reasoning=alert_data.get("reasoning", ""),
                contributing_signals=alert_data.get("contributing_signals", []),
                created_at=datetime.utcnow()
            )
            db.add(new_alert)
            db.commit()
            logger.info(f"Persisted alert {alert_id} to database.")
        else:
            logger.info(f"Alert {alert_id} already exists in database.")
    except Exception as e:
        logger.error(f"Failed to persist alert {alert_data.get('alert_id')} to DB: {e}")
        db.rollback()
    finally:
        db.close()
        
    # Broadcast via WebSockets in async event loop
    try:
        if main_event_loop and main_event_loop.is_running():
            asyncio.run_coroutine_threadsafe(manager.broadcast_json(alert_data), main_event_loop)
    except Exception as e:
        logger.error(f"Failed to schedule WebSocket broadcast for alert: {e}")


def kafka_consumer_worker():
    """Blocking worker loop for reading alerts from Kafka."""
    global is_running
    try:
        from kafka import KafkaConsumer
        logger.info(f"Starting background Kafka Consumer for topic '{settings.KAFKA_ALERTS_TOPIC}'...")
        consumer = KafkaConsumer(
            settings.KAFKA_ALERTS_TOPIC,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset="latest",
            enable_auto_commit=True,
            group_id="civic_backend_alerts_group",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            consumer_timeout_ms=1000
        )
        logger.info(f"Kafka Consumer subscribed to '{settings.KAFKA_ALERTS_TOPIC}'.")
        
        while is_running:
            for message in consumer:
                if not is_running:
                    break
                try:
                    alert_payload = message.value
                    process_alert_message(alert_payload)
                except Exception as e:
                    logger.error(f"Error processing consumed Kafka message: {e}")
    except Exception as e:
        logger.warning(f"Kafka Consumer failed to start/connect ({e}). Long-polling consumer will retry periodically.")


async def start_kafka_consumer():
    """Launches the Kafka consumer worker as a non-blocking background task."""
    global is_running, consumer_task, main_event_loop
    is_running = True
    main_event_loop = asyncio.get_running_loop()
    consumer_task = asyncio.create_task(asyncio.to_thread(kafka_consumer_worker))
    logger.info("Kafka consumer background task launched.")


async def stop_kafka_consumer():
    """Gracefully stops the background Kafka consumer task."""
    global is_running, consumer_task
    is_running = False
    if consumer_task:
        consumer_task.cancel()
        logger.info("Kafka consumer background task stopped.")
