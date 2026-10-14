# 🛡️ CiviSentinel: Real-Time Civic Disruption Early-Warning System

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-3.7-231F20?logo=apachekafka&logoColor=white)](https://kafka.apache.org/)
[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-3.5.1-E25A1C?logo=apachespark&logoColor=white)](https://spark.apache.org/)
[![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-2.9.1-017CEE?logo=apacheairflow&logoColor=white)](https://airflow.apache.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An end-to-end mission-critical early-warning platform that detects urban disruptions (flooding, waterlogging, power outages) by correlating hardware sensor telemetry with multi-lingual citizen and news reports (in Tamil and English), scoring correlated confidence via dynamic trust weights, and streaming actionable alerts to an interactive operations command center dashboard in real-time.

---

## 🌟 Key Capabilities

- **Multi-Modal Event Ingestion:** Consumes hardware telemetry (water level, grid voltage) alongside citizen social posts and verified news reports across multiple languages (Tamil and English).
- **Real-Time Spatial-Temporal Correlation:** Employs **Apache Spark Structured Streaming** with 5-minute watermarking, ~500m spatial grid bucketing, and 2-minute tumbling windows.
- **Dynamic Trust Scoring Engine:** Automatically calculates trust scores based on source credibility weights (`verified_news`: 0.90, `sensor`: 0.85, `social`: 0.40, `anonymous`: 0.20), filtering uncorroborated noise below 0.60.
- **Live Command Center UI:** Dark-mode React + Leaflet map with real-time WebSocket feeds, radial confidence gauges, radar pulses, and an interactive 3-stage pipeline simulation stepper.
- **Automated Workflow Governance:** **Apache Airflow** runs daily maintenance DAGs to audit data quality, detect model drift, retrain credibility weights, and archive historical records to Parquet storage.

---

## 🏗 End-to-End System Architecture

```text
                                  +-----------------------+
                                  |   Ambient Simulator   |
                                  | (scripts/ambient_simulator.py)|
                                  +-----------+-----------+
                                              | (POST /api/simulate)
                                              v
+-------------------------+       +-----------+-----------+       +-------------------------+
|   raw-sensor-events     |       |   FastAPI Backend     |       |   raw-citizen-reports   |
| (Kafka Input Topic)     | <---- | - REST Endpoints      | ----> | (Kafka Input Topic)     |
+------------+------------+       | - Simulation Injector |       +------------+------------+
             |                    +-----------+-----------+                    |
             |                                ^                                |
             +--------------------+           |           +--------------------+
                                  |           |           |
                                  v           |           v
                      +-----------+-----------+-----------+-----------+
                      | PySpark Structured Streaming Engine           |
                      | - 5m Watermarking                             |
                      | - ~500m Spatial Grid Bucketing                |
                      | - 2m Tumbling Window Grouping                 |
                      | - Dynamic Database Trust Lookup               |
                      +-----------------------+-----------------------+
                                              |
                             (Correlated Alerts >= 0.60)
                                              v
                                  +-----------+-----------+
                                  |        alerts         |
                                  | (Kafka Output Topic)  |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------+-----------+
                                  | Background Consumer   |
                                  | (FastAPI Worker)      |
                                  +-----+-------------+---+
                                        |             |
                         (DB Persist)   v             v   (WS Broadcast)
                        +---------------+             +---------------+
                        | Database      |             | React Command |
                        | (raw_events & |             | Center UI     |
                        |  alerts)      |             | (Port 5173)   |
                        +-------+-------+             +---------------+
                                ^
                                | (Nightly Audit & Maintenance)
                        +-------+-------+
                        |  Airflow DAG  |
                        | (@daily run)  |
                        +---------------+
```

---

## 🔗 Tool-Wise Links & Working Explanations

Here is a breakdown of every tool in the architecture, including its dedicated local web link, port, architectural responsibility, and how to verify it:

### 1. 🖥️ Operations Command Center (Frontend)
* **Access Link:** **[http://localhost:5173](http://localhost:5173)**
* **Technology:** React 18, Vite, Tailwind CSS, Leaflet, Framer Motion, Lucide Icons
* **Explanation:**
  * Displays a full-screen, dark-mode geospatial map centered on Chennai with disruption radar markers (Red for Flooding, Amber for Waterlogging, Purple for Power Outage).
  * Streams real-time alerts pushed over WebSockets (`ws://localhost:5173/ws/alerts`).
  * Features the **Demo Control Panel** drawer (bottom-left) to inject preset or custom disruption scenarios and visualize the 3-stage correlation stepper (*1. INGESTED* $\rightarrow$ *2. CORRELATING* $\rightarrow$ *3. ALERT RAISED*).
  * Includes detail drawers with radial trust gauges, breakdown of hardware sensors, and verbatim citizen reports in Tamil (`"தி நகர் பகுதியில் வீடுகளுக்குள் வெள்ளம்..."`) and English.

---

### 2. ⚡ FastAPI Backend & WebSocket Hub
* **Access Link (Interactive Swagger):** **[http://localhost:8000/api/docs](http://localhost:8000/api/docs)**
* **Access Link (ReDoc Spec):** **[http://localhost:8000/api/redoc](http://localhost:8000/api/redoc)**
* **Health Endpoint:** **[http://localhost:8000/api/healthz](http://localhost:8000/api/healthz)**
* **Technology:** Python 3, FastAPI, Uvicorn, SQLAlchemy, WebSockets, Pydantic
* **Explanation:**
  * **Ingestion API (`POST /api/simulate`):** Injects raw sensor readings and multi-lingual citizen reports onto the message bus.
  * **Alerts API (`GET /api/alerts`):** Returns historical and active alerts with pagination, disruption type filtering, and severity sorting.
  * **WebSocket Feed (`/ws/alerts`):** Immediately pushes the 10 most recent backlog alerts upon client connection, then streams new incoming correlated alerts in real-time.
  * **Trust Weights API (`GET/PUT /api/config/weights`):** Allows operational tuning of source credibility weights.

---

### 3. 🌊 Apache Spark 3.5.1 (Structured Streaming Engine)
* **Access Link (Spark Web UI):** **[http://localhost:4040](http://localhost:4040)**
* **Structured Streaming Tab:** **[http://localhost:4040/streaming](http://localhost:4040/streaming)**
* **Stages & Executors:** **[http://localhost:4040/stages](http://localhost:4040/stages)** | **[http://localhost:4040/executors](http://localhost:4040/executors)**
* **Technology:** PySpark 3.5.1, Scala 2.12
* **Script Location:** [`apache-pipeline/spark/stream_correlator.py`](apache-pipeline/spark/stream_correlator.py)
* **Explanation:**
  * **Dual Ingestion:** Ingests two concurrent streams (`raw-sensor-events` and `raw-citizen-reports`).
  * **5-Minute Watermarking:** Accounts for late-arriving mobile citizen reports without blocking the streaming engine.
  * **Spatial Grid Bucketing:** Uses `floor(lat * 200) / 200` and `floor(lng * 200) / 200` to bucket events into ~500m urban cells.
  * **2-Minute Tumbling Windows:** Groups concurrent reports and hardware sensor readings occurring in the same spatial grid cell.
  * **Trust Calculation:** Computes:
    $$\text{Trust Score} = \min\left(1.0, (\text{Report Score} \times 0.5) + (\text{Sensor Score} \times 0.5) + 0.15\right)$$
  * Emits alerts passing the threshold ($\ge 0.60$) to Kafka `alerts`, while persisting all audited raw batch records to the database.

---

### 4. 🌀 Apache Airflow 2.9.1 (Maintenance & Governance)
* **Access Link (Airflow Home):** **[http://localhost:8080](http://localhost:8080)**
* **DAG Grid View:** **[http://localhost:8080/dags/civic_pipeline_maintenance_dag/grid](http://localhost:8080/dags/civic_pipeline_maintenance_dag/grid)**
* **DAG Graph View:** **[http://localhost:8080/dags/civic_pipeline_maintenance_dag/graph](http://localhost:8080/dags/civic_pipeline_maintenance_dag/graph)**
* **Health API:** **[http://localhost:8080/health](http://localhost:8080/health)**
* **Technology:** Apache Airflow 2.9.1, PythonOperator, BranchPythonOperator
* **Script Location:** [`apache-pipeline/dags/civic_pipeline_maintenance_dag.py`](apache-pipeline/dags/civic_pipeline_maintenance_dag.py)
* **Explanation:**
  * Runs the automated `@daily` maintenance DAG:
    1. `check_data_quality`: Audits events over 24h for missing coordinates, invalid timestamps, and gaps $>30\text{ min}$.
    2. `evaluate_model_drift`: Evaluates drift between incoming reports and active model weight distributions.
    3. `decide_retrain`: Branching operator — triggers weight retraining if drift score $>0.15$.
    4. `retrain_model`: Calibrates new source weights and updates the live weights table.
    5. `archive_raw_events`: Compresses and exports processed events older than 24h into Parquet format (`archives/YYYY-MM-DD.parquet`).
    6. `write_health_status`: Logs audit status and model version into the system health register.
  * The web interface includes an interactive **"Trigger DAG Now"** button to execute a full audit run on demand.

---

### 5. 📬 Apache Kafka & Zookeeper (Messaging Backbone)
* **Broker Host/Port:** `localhost:9092` (Zookeeper: `localhost:2181`)
* **Technology:** Apache Kafka 3.7, Bitnami Zookeeper 3.9
* **Explanation:**
  * Provides high-throughput, partitioned event streaming across 4 core topics:
    * `raw-sensor-events`: Stream of IoT hardware telemetry (water level, power grid voltage).
    * `raw-citizen-reports`: Multi-lingual citizen posts and verified news items.
    * `alerts`: Correlated disruption alerts output by Spark for backend distribution.
    * `config-updates`: Dynamic configuration and weight changes.
  * Enables asynchronous decoupling so neither the sensors nor citizen submissions ever block the correlation or command dashboard.

---

### 6. 🗄️ Relational Database Layer
* **Technology:** PostgreSQL 15 (Docker) or SQLite (Native Local)
* **Schema Initialization:** [`apache-pipeline/postgres/init.sql`](apache-pipeline/postgres/init.sql)
* **Tables:**
  * `alerts`: Final scored disruptions with location, severity, and signal lineage.
  * `raw_events`: Raw audit log of all ingested sensor and citizen payloads.
  * `trust_weights`: Active weights used by Spark and the backend (`verified_news`, `social`, `anonymous`, `sensor`).
  * `model_versions`: Historical log of trained weights and F1 metrics.
  * `system_health`: Audit logs written after each Airflow maintenance cycle.
  * `data_quality_reports`: Results of daily missing-data and coordinate checks.

---

## 📂 Project Structure

```text
.
├── apache-pipeline/        # Core pipeline implementations
│   ├── dags/               # Airflow maintenance DAG definitions
│   │   └── civic_pipeline_maintenance_dag.py
│   ├── postgres/           # Database initialization schemas (init.sql)
│   └── spark/              # PySpark Structured Streaming correlator
│       ├── stream_correlator.py
│       └── run_spark_job.sh
├── backend/                # FastAPI application
│   ├── app/
│   │   ├── models.py       # SQLAlchemy ORM models
│   │   ├── schemas.py      # Pydantic schemas
│   │   ├── kafka_client.py # Kafka producer/consumer & fallback engine
│   │   ├── database.py     # Database engine & session management
│   │   ├── routers/        # REST endpoints (alerts, simulate, health, config)
│   │   └── websocket_manager.py
│   ├── tests/              # Pytest test suite (100% pass)
│   └── seed_db.py          # Database seeder for quickstart
├── frontend/               # React 18 + Vite command center
│   ├── src/
│   │   ├── components/     # LiveMap, AlertFeed, DemoControlPanel, TrustGauge
│   │   ├── services/       # REST and WebSocket client connectors
│   │   └── types/          # TypeScript domain models
│   └── vite.config.ts
├── scripts/                # Launchers & monitoring webservers
│   ├── start_all.py        # Master one-click runner for all 4 services
│   ├── airflow_server.py   # Airflow 2.9.1 webserver & DAG grid UI (Port 8080)
│   ├── spark_server.py     # Spark 3.5.1 streaming UI (Port 4040)
│   └── ambient_simulator.py# Synthetic background event generator
├── archives/               # Parquet exports created by Airflow maintenance
├── docs/                   # Architectural guides & native runbooks
└── docker-compose.yml      # Multi-container orchestration (12 services)
```

---

## 🚀 Quickstart & How to Run

### Method 1: One-Click Native Runner (Fastest & Recommended)

No heavy container downloads required. All 4 services can be started natively with a single command:

```powershell
# From the repository root
python scripts/start_all.py
```

This starts:
1. **FastAPI Backend:** `http://localhost:8000`
2. **React Command Center:** `http://localhost:5173`
3. **Airflow Webserver (DAG Grid):** `http://localhost:8080`
4. **Spark Streaming UI:** `http://localhost:4040`

---

### Method 2: Docker Compose (Full Container Stack)

If Docker is installed and running on your system:

```bash
docker-compose up -d --build
```

---

## 🧪 Testing & Verification

Run the automated backend test suite to verify all endpoints, database bindings, and message handlers:

```bash
cd backend
python -m pytest tests/
```

Expected result:
```text
======================= 9 passed in 3.28s =======================
```

---

## 🎭 Live Demo Walkthrough

1. Open **[http://localhost:5173](http://localhost:5173)** in your browser and click **"ENTER COMMAND CENTER"**.
2. Open **[http://localhost:8080/dags/civic_pipeline_maintenance_dag/grid](http://localhost:8080/dags/civic_pipeline_maintenance_dag/grid)** to view the Airflow DAG grid.
3. Open **[http://localhost:4040](http://localhost:4040)** to view the Spark streaming metrics.
4. On the frontend dashboard:
   - Click **DEMO CONTROL PANEL** (bottom-left).
   - Click **"SCENARIO 1: HIGH TRUST FLOODING"**.
   - Watch the 3-stage stepper light up (*Ingested* $\rightarrow$ *Correlating* $\rightarrow$ *Alert Raised*).
   - An alert marker appears on the Chennai map with high confidence ($\approx 0.94$).
   - Click **"SCENARIO 2: SINGLE ANONYMOUS REPORT"** and observe below-threshold filtering (score $0.20 < 0.60$), verifying that false alarms are suppressed.

---

## ⚖️ License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
