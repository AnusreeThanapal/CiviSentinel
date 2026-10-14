import os
import sys
from datetime import datetime

# Set local database path
os.environ["DATABASE_URL"] = "sqlite:///./civic_pipeline.db"

from app.database import engine, Base, SessionLocal
from app.models import Alert, TrustWeight, SystemHealth, ModelVersion

# Create tables
Base.metadata.create_all(bind=engine)
db = SessionLocal()

try:
    # 1. Seed Trust Weights
    weights = [
        ("verified_news", 0.9),
        ("social", 0.4),
        ("anonymous", 0.2),
        ("sensor", 0.85)
    ]
    for key, val in weights:
        existing = db.query(TrustWeight).filter_by(key=key).first()
        if not existing:
            db.add(TrustWeight(key=key, value=val))

    # 2. Seed System Health
    health = db.query(SystemHealth).first()
    if not health:
        db.add(SystemHealth(
            run_timestamp=datetime.utcnow(),
            dag_status="SUCCESS",
            model_last_retrained=datetime.utcnow()
        ))

    # 3. Seed Model Version
    m_ver = db.query(ModelVersion).first()
    if not m_ver:
        db.add(ModelVersion(
            trained_at=datetime.utcnow(),
            weights={"verified_news": 0.9, "social": 0.4, "anonymous": 0.2, "sensor": 0.85},
            metrics={"initial_baseline": True, "f1_score": 0.92},
            is_active=True
        ))

    # 4. Seed Initial Alerts
    alerts_data = [
        {
            "alert_id": "ALT-2026-0905-001",
            "type": "flooding",
            "lat": 13.0827,
            "lng": 80.2707,
            "location_name": "T. Nagar Canal Zone, Chennai",
            "trust_score": 0.92,
            "reasoning": "2 water level sensor signals (5.2m) + 3 corroborating reports (Tamil news & social), trust score 0.92",
            "contributing_signals": [
                {"kind": "sensor", "sensor_id": "SENS-WATER-101", "value": 4.8, "unit": "meters"},
                {"kind": "sensor", "sensor_id": "SENS-WATER-102", "value": 5.2, "unit": "meters"},
                {"kind": "report", "text": "BREAKING: Severe waterlogging and flooding reported near T. Nagar canal after heavy rainfall.", "language": "en", "source_type": "verified_news"},
                {"kind": "report", "text": "தி நகர் பகுதியில் வீடுகளுக்குள் வெள்ளம் புகுந்தது. சாக்கடை நீர் பெருக்கெடுத்து ஓடுகிறது", "language": "ta", "source_type": "social"}
            ],
            "created_at": datetime.utcnow()
        },
        {
            "alert_id": "ALT-2026-0905-002",
            "type": "waterlogging",
            "lat": 13.0405,
            "lng": 80.2337,
            "location_name": "Guindy Industrial Estate, Chennai",
            "trust_score": 0.78,
            "reasoning": "1 water level sensor (3.4m) + 2 news reports confirmed waterlogging, trust score 0.78",
            "contributing_signals": [
                {"kind": "sensor", "sensor_id": "SENS-WATER-204", "value": 3.4, "unit": "meters"},
                {"kind": "report", "text": "Heavy water stagnation outside Guindy Metro Station blocking traffic lanes.", "language": "en", "source_type": "verified_news"},
                {"kind": "report", "text": "கிண்டி பகுதியில் பலத்த மழை காரணமாக சாலைகளில் நீர் தேங்கியுள்ளது", "language": "ta", "source_type": "verified_news"}
            ],
            "created_at": datetime.utcnow()
        },
        {
            "alert_id": "ALT-2026-0905-003",
            "type": "power_outage",
            "lat": 12.9815,
            "lng": 80.2180,
            "location_name": "Velachery Main Road, Chennai",
            "trust_score": 0.85,
            "reasoning": "2 grid telemetry sensors (0V collapse) + 1 social report, trust score 0.85",
            "contributing_signals": [
                {"kind": "sensor", "sensor_id": "GRID-TRANS-08", "value": 0.0, "unit": "volts"},
                {"kind": "sensor", "sensor_id": "GRID-TRANS-09", "value": 0.0, "unit": "volts"},
                {"kind": "report", "text": "வேளச்சேரியில் கடந்த 1 மணி நேரமாக மின்சாரம் துண்டிக்கப்பட்டுள்ளது", "language": "ta", "source_type": "social"}
            ],
            "created_at": datetime.utcnow()
        }
    ]

    for a in alerts_data:
        existing_alert = db.query(Alert).filter_by(alert_id=a["alert_id"]).first()
        if not existing_alert:
            db.add(Alert(**a))

    db.commit()
    print("Database successfully seeded!")
except Exception as e:
    db.rollback()
    print(f"Error seeding database: {e}")
finally:
    db.close()
