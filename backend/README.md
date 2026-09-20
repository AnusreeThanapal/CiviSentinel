# FastAPI Backend Service - Real-Time Civic Disruption Early-Warning System

This sub-project implements the **FastAPI Backend Service** for the Real-Time Civic Disruption Early-Warning System. It sits directly between the Apache Kafka/Spark processing layer (`apache-pipeline/`) and the frontend dashboard.

---

## 🚀 Key Responsibilities

1. **Background Kafka Consumer**: Subscribes to the `alerts` Kafka topic emitted by Spark Structured Streaming. Automatically persists alerts into Postgres (`alerts` table) and broadcasts them live to connected WebSocket clients.
2. **Simulation Injector (`POST /api/simulate`)**: Validates synthetic sensor readings and citizen/news reports (supporting Tamil and English), then publishes them onto input topics `raw-sensor-events` and `raw-citizen-reports` for Spark stream correlation.
3. **WebSocket Streaming (`WS /ws/alerts`)**: Connects dashboard clients, transmits the last 10 alerts as an initial backlog on connect, and streams real-time alerts as they arrive.
4. **REST API**:
   - `GET /api/alerts`: Paginated alert history from Postgres DB.
   - `GET /api/alerts/{alert_id}`: Full alert details including contributing signals.
   - `POST /api/simulate`: Simulation trigger for demo scenarios.
   - `GET /api/system-health`: Latest Airflow maintenance run status and active model weights.
   - `GET /api/config/trust-weights`: Current weights read by Spark on micro-batches.
   - `PUT /api/config/trust-weights`: Dynamically updates trust weights in Postgres.
   - `GET /api/healthz`: Service liveness check.

---

## 📡 API Endpoint Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/alerts?limit=50&type=flooding` | Paginated alert history |
| `GET` | `/api/alerts/{alert_id}` | Detailed alert object with contributing signals |
| `POST` | `/api/simulate` | Publish synthetic simulation events to Kafka raw topics |
| `GET` | `/api/system-health` | Query Airflow `system_health` and active `model_versions` |
| `GET` | `/api/config/trust-weights` | Retrieve current trust weights |
| `PUT` | `/api/config/trust-weights` | Update trust weights in Postgres |
| `GET` | `/api/healthz` | Plain service liveness check |
| `WS` | `/ws/alerts` | WebSocket live alert stream with 10-alert backlog |

---

## 🔧 Environment Configuration (`.env`)

Create or update `.env` in `backend/`:

```env
PORT=8000
HOST=0.0.0.0
LOG_LEVEL=INFO
DATABASE_URL=postgresql://civic_user:civic_pass@localhost:5432/civic_pipeline
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
CORS_ORIGINS=["*"]
```

---

## 🧪 Local Execution & Testing Instructions

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Run Pytest Unit Tests
Run unit tests verifying API endpoints, simulation trigger validation, and mocked Kafka handling:

```bash
pytest -v
```

### 3. Run FastAPI Application Standalone
Start the backend server locally:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access Interactive API Documentation:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

---

## 🐳 Docker Deployment

Build and launch container:

```bash
docker build -t civic-backend .
docker run -p 8000:8000 --env-file .env civic-backend
```

To run alongside the full Apache cluster, add the service entry to `apache-pipeline/docker-compose.yml`:

```yaml
  backend:
    build: ../backend
    container_name: civic-backend
    restart: always
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://civic_user:civic_pass@postgres:5432/civic_pipeline
      - KAFKA_BOOTSTRAP_SERVERS=kafka:29092
    depends_on:
      postgres:
        condition: service_healthy
      kafka:
        condition: service_healthy
```
