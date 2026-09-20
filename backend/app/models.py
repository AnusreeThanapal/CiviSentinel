from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from app.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(String(128), primary_key=True, index=True)
    type = Column(String(64), nullable=False, index=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    location_name = Column(String(256), nullable=True)
    trust_score = Column(Float, nullable=False, index=True)
    reasoning = Column(Text, nullable=True)
    contributing_signals = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class RawEvent(Base):
    __tablename__ = "raw_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    kind = Column(String(64), nullable=False)
    payload = Column(JSON, nullable=False)
    event_time = Column(DateTime, nullable=False)
    processed_flag = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trained_at = Column(DateTime, nullable=False)
    weights = Column(JSON, nullable=False)
    metrics = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=False)

class SystemHealth(Base):
    __tablename__ = "system_health"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_timestamp = Column(DateTime, nullable=False)
    dag_status = Column(String(64), nullable=False)
    model_last_retrained = Column(DateTime, nullable=True)

class TrustWeight(Base):
    __tablename__ = "trust_weights"

    key = Column(String(64), primary_key=True)
    value = Column(Float, nullable=False)
