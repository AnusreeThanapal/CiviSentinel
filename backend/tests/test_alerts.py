import os
import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock

TEST_DB_FILE = "./test_civic_alerts.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE}"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db, engine
from app.models import Alert
from app.kafka_client import process_alert_message

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass

def test_get_empty_alerts():
    response = client.get("/api/alerts")
    assert response.status_code == 200
    assert response.json() == []

def test_get_alerts_pagination_and_filtering():
    db = TestingSessionLocal()
    alert1 = Alert(
        alert_id="ALT-001",
        type="flooding",
        lat=13.0827,
        lng=80.2707,
        location_name="T. Nagar",
        trust_score=0.9,
        reasoning="High trust flooding alert",
        contributing_signals=[],
        created_at=datetime.utcnow()
    )
    alert2 = Alert(
        alert_id="ALT-002",
        type="power_outage",
        lat=13.0830,
        lng=80.2710,
        location_name="Adyar",
        trust_score=0.7,
        reasoning="Power grid offline",
        contributing_signals=[],
        created_at=datetime.utcnow()
    )
    db.add_all([alert1, alert2])
    db.commit()
    db.close()

    resp = client.get("/api/alerts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2

    resp_flood = client.get("/api/alerts?type=flooding")
    assert resp_flood.status_code == 200
    assert len(resp_flood.json()) == 1
    assert resp_flood.json()[0]["alert_id"] == "ALT-001"

def test_get_alert_by_id():
    db = TestingSessionLocal()
    alert = Alert(
        alert_id="ALT-TEST-123",
        type="waterlogging",
        lat=13.08,
        lng=80.27,
        location_name="Central",
        trust_score=0.8,
        reasoning="Waterlogging observed",
        contributing_signals=[{"kind": "sensor", "sensor_id": "S1", "value": 3.0}],
        created_at=datetime.utcnow()
    )
    db.add(alert)
    db.commit()
    db.close()

    resp = client.get("/api/alerts/ALT-TEST-123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["alert_id"] == "ALT-TEST-123"
    assert data["type"] == "waterlogging"
    assert len(data["contributing_signals"]) == 1

def test_process_alert_message_persists_and_broadcasts():
    alert_payload = {
        "alert_id": "ALT-KAFKA-999",
        "type": "flooding",
        "location": {"lat": 13.0827, "lng": 80.2707, "name": "T. Nagar Canal"},
        "trust_score": 0.95,
        "reasoning": "2 sensors + 3 reports",
        "contributing_signals": [{"kind": "sensor", "sensor_id": "S1", "value": 4.5}],
        "timestamp": "2026-09-05T12:00:00Z"
    }

    mock_loop = MagicMock()
    mock_loop.is_running.return_value = True

    with patch("app.kafka_client.SessionLocal", TestingSessionLocal):
        with patch("app.kafka_client.main_event_loop", mock_loop):
            with patch("asyncio.run_coroutine_threadsafe") as mock_run_coro:
                process_alert_message(alert_payload)

                db = TestingSessionLocal()
                saved = db.query(Alert).filter(Alert.alert_id == "ALT-KAFKA-999").first()
                assert saved is not None
                assert saved.trust_score == 0.95
                assert saved.location_name == "T. Nagar Canal"
                db.close()

                mock_run_coro.assert_called_once()
