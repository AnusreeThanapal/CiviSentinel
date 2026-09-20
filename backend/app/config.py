import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Civic Disruption Early-Warning System Backend"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    LOG_LEVEL: str = "INFO"
    
    # DB URL - default to PostgreSQL, fallback to SQLite for local tests
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://civic_user:civic_pass@localhost:5432/civic_pipeline"
    )
    
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS", 
        "localhost:9092"
    )
    
    KAFKA_ALERTS_TOPIC: str = "alerts"
    KAFKA_SENSOR_TOPIC: str = "raw-sensor-events"
    KAFKA_REPORT_TOPIC: str = "raw-citizen-reports"
    
    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
