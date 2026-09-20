import os
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

TEST_DB_FILE = "./test_civic_health.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE}"

from app.main import app
from app.database import Base, get_db, engine
from app.models import SystemHealth, ModelVersion, TrustWeight

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

def test_liveness():
    response = client.get("/api/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_system_health_endpoint():
    db = TestingSessionLocal()
    health_rec = SystemHealth(
        run_timestamp=datetime.utcnow(),
        dag_status="SUCCESS",
        model_last_retrained=datetime.utcnow()
    )
    model_rec = ModelVersion(
        trained_at=datetime.utcnow(),
        weights={"verified_news": 0.9, "social": 0.4, "anonymous": 0.2, "sensor": 0.85},
        metrics={"f1_score": 0.92},
        is_active=True
    )
    db.add_all([health_rec, model_rec])
    db.commit()
    db.close()

    response = client.get("/api/system-health")
    assert response.status_code == 200
    data = response.json()
    assert data["dag_status"] == "SUCCESS"
    assert data["active_model_id"] == 1
    assert data["active_model_weights"]["verified_news"] == 0.9

def test_trust_weights_get_and_put():
    resp_get = client.get("/api/config/trust-weights")
    assert resp_get.status_code == 200
    assert "verified_news" in resp_get.json()["weights"]

    update_payload = {
        "weights": {
            "verified_news": 0.95,
            "social": 0.5,
            "anonymous": 0.3,
            "sensor": 0.9
        }
    }
    resp_put = client.put("/api/config/trust-weights", json=update_payload)
    assert resp_put.status_code == 200
    assert resp_put.json()["weights"]["verified_news"] == 0.95

    resp_verify = client.get("/api/config/trust-weights")
    assert resp_verify.status_code == 200
    assert resp_verify.json()["weights"]["verified_news"] == 0.95
