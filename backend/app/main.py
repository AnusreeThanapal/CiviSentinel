import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models import Alert
from app.websocket_manager import manager
from app.kafka_client import start_kafka_consumer, stop_kafka_consumer
from app.routers import alerts, simulate, health, config

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("backend.main")

# Initialize DB tables on startup if DB is available
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
except Exception as e:
    logger.warning(f"Could not initialize database tables on startup ({e}). Continuing startup...")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan context manager:
    Starts long-lived background Kafka consumer task on startup
    and shuts it down on application termination.
    """
    logger.info("Starting up Civic Disruption Early-Warning System Backend...")
    # Start background Kafka Consumer task
    await start_kafka_consumer()
    yield
    logger.info("Shutting down Civic Disruption Early-Warning System Backend...")
    # Stop background Kafka Consumer task
    await stop_kafka_consumer()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST API Routers under /api prefix
app.include_router(alerts.router, prefix=settings.API_PREFIX)
app.include_router(simulate.router, prefix=settings.API_PREFIX)
app.include_router(health.router, prefix=settings.API_PREFIX)
app.include_router(config.router, prefix=settings.API_PREFIX)

@app.websocket("/ws/alerts")
async def websocket_alerts_endpoint(websocket: WebSocket):
    """
    WebSocket Endpoint (/ws/alerts):
    1. On client connect, sends backlog of last 10 alerts from Postgres.
    2. Keeps connection open to stream real-time alerts emitted by Kafka background consumer.
    """
    await manager.connect(websocket)
    
    # 1. Fetch and send last 10 alerts as backlog
    db = SessionLocal()
    try:
        recent_alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(10).all()
        # Send backlog (oldest to newest for chronological playback)
        recent_alerts.reverse()
        
        for alert in recent_alerts:
            alert_payload = {
                "alert_id": alert.alert_id,
                "type": alert.type,
                "location": {
                    "lat": alert.lat,
                    "lng": alert.lng,
                    "name": alert.location_name or "Unknown Location"
                },
                "trust_score": alert.trust_score,
                "reasoning": alert.reasoning or "",
                "contributing_signals": alert.contributing_signals or [],
                "timestamp": alert.created_at.isoformat() + "Z",
                "is_backlog": True
            }
            await websocket.send_json(alert_payload)
        logger.info(f"Sent backlog of {len(recent_alerts)} alerts to newly connected WebSocket client.")
    except Exception as e:
        logger.error(f"Error fetching/sending alert backlog to WebSocket client: {e}")
    finally:
        db.close()

    # 2. Receive loop (handles ping/pong and client disconnect)
    try:
        while True:
            data = await websocket.receive_text()
            # Client can send 'ping' or heartbeat messages
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected from /ws/alerts.")
    except Exception as e:
        logger.warning(f"WebSocket loop exception: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
