# Real-Time Civic Disruption Early-Warning System

An end-to-end mission-critical early-warning platform that detects urban disruptions (flooding, waterlogging, power outages) by correlating hardware sensor telemetry with multi-lingual citizen and news reports (in Tamil and English), scoring correlated confidence, and streaming alerts to an operations command center dashboard.

---

## 🌟 Key Features
- **Multi-modal Data Ingestion:** Consumes hardware telemetry (sensors) alongside social/news citizen reports (text).
- **Real-Time Correlation Engine:** Uses Apache Spark Structured Streaming with spatial grid bucketing (~500m precision) and time-windowing.
- **Dynamic Trust Scoring:** Computes confidence based on source credibility (e.g., verified news vs. anonymous post) using weights synced dynamically from a Postgres database.
- **Live Command Center Dashboard:** A sleek, dark-mode React UI with Leaflet maps, real-time WebSocket alert feeds, and interactive pipeline simulation controls.
- **Automated Nightly Maintenance:** Apache Airflow DAGs run nightly to audit data quality, evaluate model drift, retrain weights, and archive old events.

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
                      | - Dynamic JDBC Weight Lookup                  |
                      +-----------------------+-----------------------+
                                              |
                             (Correlated Alerts >= 0.6)
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
                        | Postgres DB   |             | React Command |
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

## 📂 Project Structure

```text
.
├── apache-pipeline/        # Spark scripts, Airflow DAGs, and Database initialization
│   ├── dags/               # Airflow DAG definitions
│   ├── postgres/           # init.sql schemas for civic_pipeline database
│   └── spark/              # Spark Structured Streaming correlator scripts
├── backend/                # FastAPI application, WebSocket broadcasting, Kafka consumers
├── frontend/               # React (Vite) dashboard UI
├── scripts/                # Synthetic data generators and ambient simulators
├── archives/               # Parquet exports of old events (created by Airflow)
└── docker-compose.yml      # Orchestration for all 12 services
```

---

## 🛠 Tech Stack

- **Data Processing & Orchestration:** Apache Spark, Apache Kafka, Apache Airflow, Zookeeper
- **Backend Services:** Python, FastAPI, Pydantic, SQLAlchemy, psycopg2, WebSockets
- **Database:** PostgreSQL (with JDBC driver for Spark)
- **Frontend Command Center:** React, Vite, Tailwind CSS, Leaflet, Framer Motion
- **Deployment:** Docker, Docker Compose

---

## 🚀 Setup & Installation

This project can be run in two modes:

### Option A: Docker (recommended for quick start)
Bring up the complete multi-container stack with a single command. (Requires Docker Desktop or Engine).

```bash
docker-compose up -d --build
```

#### Access Services:
- **Operations Command Center (Frontend)**: [`http://localhost:5173`](http://localhost:5173)
- **FastAPI Backend REST API Docs**: [`http://localhost:8000/api/docs`](http://localhost:8000/api/docs)
- **Airflow Maintenance UI**: [`http://localhost:8080`](http://localhost:8080) *(User: `admin`, Pass: `admin`)*
- **Postgres Database**: `localhost:5432` *(User: `civic_user`, Pass: `civic_pass`, DB: `civic_pipeline`)*

---

### Option B: Native / no-Docker
If you need to demonstrate individual tool proficiency, or if you are in an environment where Docker isn't available or desired, you can run all services natively on your host machine. 

Please refer to the detailed **[docs/NATIVE_SETUP.md](docs/NATIVE_SETUP.md)** for a complete guide covering prerequisites, manual tool installation, and scripted startup.

---

## 🎭 Live Demo Walkthrough

1. **Open Command Center Dashboard**: Navigate to [`http://localhost:5173`](http://localhost:5173). Observe the full-bleed dark Leaflet map of Chennai, floating health header, and real-time alert feed.
2. **Observe Ambient Activity**: The `simulator` background container automatically injects realistic Tamil and English flooding/outage scenarios every 35 seconds. Notice alerts popping onto the feed with spring physics animations and radar markers pulsing on the map.
3. **Manual Simulation Trigger (Demo Control Panel)**:
   - Click the **DEMO CONTROL PANEL** drawer at the bottom-left of the screen.
   - Click **SCENARIO 1: HIGH TRUST FLOODING**.
   - Watch the animated 3-stage pipeline stepper light up: **1. INGESTED** $\rightarrow$ **2. CORRELATING** $\rightarrow$ **3. ALERT RAISED**.
   - Within ~5-8 seconds, a high-trust alert marker (`trust_score ~0.94`) appears on the map at T. Nagar, Chennai.
4. **Inspect Signal Trace**: Click on the new alert row or marker to open the glassmorphic detail drawer. Review the animated radial trust score gauge and raw signal breakdown comparing hardware water level sensors (5.3m) with original Tamil citizen reports (*"தி நகர் பகுதியில் வீடுகளுக்குள் வெள்ளம்..."*).
5. **Inspect Below-Threshold Filtering**: Click **SCENARIO 2: SINGLE ANONYMOUS REPORT**. Observe the pipeline status stepper advance and report **Filtered (Trust Score 0.20 < 0.60)** — demonstrating that uncorroborated single posts do not trigger false alarms.

---

## 📋 Integration Testing Checklist

Run through this literal verification checklist to validate end-to-end functionality:

- [x] **1. Automated Cold Start**: `docker-compose up -d --build` brings up all 12 services (`zookeeper`, `kafka`, `kafka-init`, `postgres`, `airflow-postgres`, `airflow-init`, `airflow-webserver`, `airflow-scheduler`, `spark-correlator`, `backend`, `frontend`, `simulator`) with zero manual commands.
- [x] **2. Full Pipeline Loop (<10s)**: A message published to `raw-sensor-events` + `raw-citizen-reports` is processed by Spark $\rightarrow$ emitted to `alerts` Kafka topic $\rightarrow$ consumed by backend $\rightarrow$ saved to Postgres $\rightarrow$ broadcast over WebSocket $\rightarrow$ animated marker appears on frontend map within ~8 seconds.
- [x] **3. Interactive Simulation Stepper**: Triggering an event via `POST /api/simulate` or the frontend Demo Control Panel updates the pipeline status stepper (*Ingested* $\rightarrow$ *Correlating* $\rightarrow$ *Alert Raised*) in sync with real pipeline processing timing.
- [x] **4. Airflow DAG Health Sync**: Manually executing `docker exec -it civic-airflow-scheduler airflow dags trigger civic_pipeline_maintenance` (or natively: `airflow dags trigger civic_pipeline_maintenance`) updates Postgres tables `data_quality_reports`, `model_versions`, and `system_health`. The frontend's header bar reflects the updated retrain timestamp within seconds.
- [x] **5. Cold Restart Resilience**: Executing `docker-compose down` followed by `docker-compose up -d` cleanly recreates the cluster and resumes alert streaming with zero state corruption.

---

## ⚖️ License
This project is licensed under the MIT License - see the LICENSE file for details.
