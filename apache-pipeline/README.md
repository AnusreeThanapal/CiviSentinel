# Apache Data Pipeline Layer - Real-Time Civic Disruption Early-Warning System

This sub-project implements the **Kafka + Spark Structured Streaming + Airflow + Postgres** data pipeline layer for detecting real-time urban disruptions (flooding, waterlogging, power outages) by correlating sensor data with multi-lingual (Tamil and English) citizen/news reports.

---

## 🏗 System Architecture & Deliverables Summary

```
                      +-------------------------+
                      |   raw-sensor-events     | (Kafka Topic)
                      +------------+------------+
                                   |
                                   v
                      +------------+------------+
                      |  raw-citizen-reports    | (Kafka Topic)
                      +------------+------------+
                                   |
                                   v
                      +------------+------------+
                      | PySpark Streaming Engine| (stream_correlator.py)
                      |  - Watermarking (5m)    |
                      |  - Grid Cell (~500m)    |
                      |  - 2m Tumbling Window   |
                      +------+------------+-----+
                             |            |
           (High Trust >=0.6)|            | (All Raw Batch Events)
                             v            v
                      +------+----+  +----+-----------+
                      |  alerts   |  | Postgres       |
                      | (Kafka)   |  | (raw_events)   |
                      +-----------+  +----+-----------+
                                          ^
                                          |
                               +----------+----------+
                               | Airflow Maintenance |
                               | Nightly DAG         |
                               +---------------------+
```

### Deliverables Breakdown:
1. `docker-compose.yml`: Zookeeper, Kafka, `kafka-init` (auto-creates `raw-sensor-events`, `raw-citizen-reports`, `alerts`, `config-updates` with 3 partitions), Postgres DB (`civic_pipeline`), Airflow metadata DB (`airflow_db`), and Airflow Webserver + Scheduler.
2. `postgres/init.sql`: Creates database tables: `trust_weights`, `raw_events`, `data_quality_reports`, `model_versions`, and `system_health` with default seed data.
3. `spark/stream_correlator.py` & `run_spark_job.sh`: PySpark Structured Streaming engine performing JSON schema validation, 5m watermarking, ~500m spatial grid cell bucketing, multi-stream window correlation, dynamic JDBC weight lookup, alert scoring ($\ge 0.6$), Kafka alert publishing, and Postgres raw event auditing.
4. `dags/civic_pipeline_maintenance_dag.py`: Nightly Airflow DAG (`@daily`) for data quality auditing, model drift evaluation, conditional retraining, raw event archiving to Parquet (`/opt/airflow/archives/`), and system health tracking.
5. Verification Scripts & Documentation (`scripts/test-kafka.sh`, `scripts/produce_synthetic_data.py`, and this `README.md`).

---

## 📋 Topic & Database Schemas

### 1. `raw-sensor-events` (Kafka Topic)
```json
{
  "sensor_id": "SENS-WATER-101",
  "sensor_type": "water_level",
  "value": 4.8,
  "unit": "meters",
  "lat": 13.0827,
  "lng": 80.2707,
  "location_name": "T. Nagar Canal Zone",
  "event_time": "2026-09-05T12:00:00Z"
}
```

### 2. `raw-citizen-reports` (Kafka Topic)
```json
{
  "report_id": "REP-NEWS-001",
  "text": "BREAKING: Severe flooding near T. Nagar canal after heavy rainfall.",
  "language": "en",
  "source_type": "verified_news",
  "lat": 13.0828,
  "lng": 80.2708,
  "location_name": "T. Nagar Canal Zone",
  "event_time": "2026-09-05T12:01:00Z"
}
```

### 3. `alerts` (Kafka Topic - Spark Produced)
```json
{
  "alert_id": "ALT-1788610000-2907_17837",
  "type": "flooding",
  "location": {
    "lat": 13.0827,
    "lng": 80.2707,
    "name": "T. Nagar Canal Zone"
  },
  "trust_score": 0.95,
  "reasoning": "2 sensor signal(s) + 3 corroborating report(s), trust score 0.95",
  "contributing_signals": [
    { "kind": "sensor", "sensor_id": "SENS-WATER-101", "value": 4.8, "unit": "meters" },
    { "kind": "report", "text": "BREAKING...", "language": "en", "source_type": "verified_news" }
  ],
  "timestamp": "2026-09-05T12:01:30Z"
}
```

---

## 🧪 Testing the Apache layer without any backend or frontend

Follow these exact step-by-step commands to verify the entire pipeline independently via CLI.

### Step 1: Start Container Infrastructure
Navigate to the `apache-pipeline` folder and launch Docker Compose:

```bash
cd apache-pipeline
docker-compose up -d
```

Verify that all containers are healthy:
```bash
docker-compose ps
```

---

### Step 2: Sanity-Check Kafka Setup (`test-kafka.sh`)
Execute the Kafka test script to verify topic auto-creation and message publishing/consuming:

```bash
bash scripts/test-kafka.sh
```

**Expected Output:**
- Topics listed: `raw-sensor-events`, `raw-citizen-reports`, `alerts`, `config-updates`.
- Published sample messages sent and received successfully via `kafka-console-consumer`.

---

### Step 3: Run PySpark Structured Streaming Correlator
Submit the PySpark streaming job:

```bash
bash spark/run_spark_job.sh
```

*Note: Target Spark version is Spark 3.5.x using package flags:*
`--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.postgresql:postgresql:42.7.3`

Keep this terminal window open. You will observe console logs reporting micro-batch processing execution, counts of processed raw events, and generated alerts.

---

### Step 4: Publish Synthetic Flooding Scenario
In a **new terminal window**, publish a synthetic multi-lingual flooding scenario (2 sensors + 3 reports in Tamil/English for the same spatial grid and time window):

```bash
python scripts/produce_synthetic_data.py
```

---

### Step 5: Tail Alerts Kafka Topic
In a **separate terminal window**, listen to the `alerts` topic to confirm that Spark outputs the correlated alert:

```bash
docker exec -it civic-kafka /opt/bitnami/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic alerts \
  --from-beginning
```

**Expected Result:**
An alert JSON message appears containing `trust_score >= 0.6` and the dynamic reasoning string:
`"reasoning": "2 sensor signal(s) + 3 corroborating report(s), trust score 0.95"`.

---

### Step 6: Query Postgres DB for Raw Events
Verify that ALL raw events processed in the batch were written to Postgres with `processed_flag = true`:

```bash
docker exec -it civic-postgres psql -U civic_user -d civic_pipeline \
  -c "SELECT id, kind, payload->>'location_name' as location, processed_flag, event_time FROM raw_events;"
```

**Expected Output:**
Rows corresponding to the published sensor and citizen report events are listed with `processed_flag = t`.

---

### Step 7: Trigger & Validate Airflow Maintenance DAG
Trigger the `civic_pipeline_maintenance` DAG manually via Airflow CLI:

```bash
docker exec -it civic-airflow-scheduler airflow dags trigger civic_pipeline_maintenance
```

Wait a few seconds for completion, then check task states:

```bash
docker exec -it civic-airflow-scheduler airflow dags state civic_pipeline_maintenance $(date +%Y-%m-)
```

Alternatively, open the Airflow UI in your browser at `http://localhost:8080` (Username: `admin`, Password: `admin`) to view the DAG DAG graph.

Query the Postgres database tables to confirm that maintenance tasks completed successfully:

```bash
# 1. Data Quality Reports
docker exec -it civic-postgres psql -U civic_user -d civic_pipeline \
  -c "SELECT * FROM data_quality_reports ORDER BY id DESC LIMIT 1;"

# 2. Active Model Version & Weights
docker exec -it civic-postgres psql -U civic_user -d civic_pipeline \
  -c "SELECT id, trained_at, weights, is_active FROM model_versions;"

# 3. System Health Log
docker exec -it civic-postgres psql -U civic_user -d civic_pipeline \
  -c "SELECT * FROM system_health ORDER BY id DESC LIMIT 1;"
```

**Expected Output:**
- `data_quality_reports` has a JSON audit row summarizing event counts, language distributions, and gap checks.
- `model_versions` shows model records with `is_active` status.
- `system_health` contains a row logging status `SUCCESS` along with `model_last_retrained`.
- Archived raw events older than 24h are saved as Parquet files under `archives/`.
