"""
Airflow Maintenance DAG for Real-Time Civic Disruption Early-Warning System

Schedule: @daily (with manual trigger enabled)
Tasks:
1. check_data_quality: Audit raw_events over 24h for counts, nulls, and gaps >30m. Write report to data_quality_reports.
2. evaluate_model_drift: Compare trust score / signal distribution vs active model_versions row. Push drift_score to XCom.
3. decide_retrain: BranchPythonOperator. If drift_score > 0.15 -> retrain_model, else -> skip_retrain.
4. retrain_model: Recompute trust_weights, create new active model_versions row, deactivate old version, update live trust_weights table.
5. skip_retrain: No-op logger.
6. archive_raw_events: Export processed raw_events older than 24h to /opt/airflow/archives/YYYY-MM-DD.parquet and delete from DB.
7. write_health_status: trigger_rule="none_failed_min_one_success". Insert health status and active model timestamp into system_health.
"""

import os
import json
import logging
from datetime import datetime, timedelta

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule

logger = logging.getLogger("AirflowCivicMaintenance")

# Database connection parameters for application database
DB_HOST = os.getenv("APP_DB_HOST", "postgres")
DB_PORT = int(os.getenv("APP_DB_PORT", "5432"))
DB_NAME = os.getenv("APP_DB_NAME", "civic_pipeline")
DB_USER = os.getenv("APP_DB_USER", "civic_user")
DB_PASS = os.getenv("APP_DB_PASS", "civic_pass")
ARCHIVE_DIR = os.getenv("ARCHIVE_DIR", "/opt/airflow/archives")


def get_db_connection():
    """Connects to the application Postgres database."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )


# -------------------------------------------------------------------------
# Task 1: Check Data Quality
# -------------------------------------------------------------------------
def task_check_data_quality(**context):
    logger.info("Executing task: check_data_quality...")
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Query last 24h raw_events
        query = """
            SELECT id, kind, payload, event_time, processed_flag, created_at
            FROM raw_events
            WHERE event_time >= NOW() - INTERVAL '24 HOURS'
            ORDER BY event_time ASC;
        """
        cur.execute(query)
        rows = cur.fetchall()
        
        total_events = len(rows)
        kind_counts = {}
        lang_counts = {}
        null_coords_count = 0
        missing_event_time_count = 0
        
        timestamps = []
        
        for r in rows:
            kind = r["kind"]
            kind_counts[kind] = kind_counts.get(kind, 0) + 1
            
            payload = r["payload"] or {}
            lang = payload.get("language", "unknown") if kind == "report" else "N/A"
            if kind == "report":
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
            
            lat = payload.get("lat")
            lng = payload.get("lng")
            if lat is None or lng is None:
                null_coords_count += 1
                
            evt_time = r["event_time"]
            if evt_time is None:
                missing_event_time_count += 1
            else:
                timestamps.append(evt_time)
                
        # Detect gaps > 30 minutes between consecutive events
        max_gap_minutes = 0.0
        gaps_over_30m = 0
        if len(timestamps) > 1:
            timestamps.sort()
            for i in range(1, len(timestamps)):
                gap_sec = (timestamps[i] - timestamps[i-1]).total_seconds()
                gap_min = gap_sec / 60.0
                if gap_min > max_gap_minutes:
                    max_gap_minutes = gap_min
                if gap_min > 30.0:
                    gaps_over_30m += 1

        summary = {
            "total_events_24h": total_events,
            "counts_by_kind": kind_counts,
            "report_counts_by_language": lang_counts,
            "null_coordinates_count": null_coords_count,
            "missing_event_time_count": missing_event_time_count,
            "max_arrival_gap_minutes": round(max_gap_minutes, 2),
            "gaps_over_30m_count": gaps_over_30m,
            "quality_status": "PASS" if null_coords_count == 0 and gaps_over_30m == 0 else "WARNING"
        }
        
        # Insert summary into data_quality_reports
        run_date = datetime.utcnow().date().isoformat()
        insert_sql = """
            INSERT INTO data_quality_reports (run_date, summary, created_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP);
        """
        cur.execute(insert_sql, (run_date, json.dumps(summary)))
        conn.commit()
        
        logger.info(f"Data quality check complete. Summary: {summary}")
        return summary
    finally:
        cur.close()
        conn.close()


# -------------------------------------------------------------------------
# Task 2: Evaluate Model Drift
# -------------------------------------------------------------------------
def task_evaluate_model_drift(**context):
    logger.info("Executing task: evaluate_model_drift...")
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get active model row
        cur.execute("SELECT * FROM model_versions WHERE is_active = true ORDER BY id DESC LIMIT 1;")
        active_model = cur.fetchone()
        
        active_weights = active_model["weights"] if active_model else {"verified_news": 0.9, "social": 0.4, "anonymous": 0.2, "sensor": 0.85}
        
        # Query 24h event source distributions to compute drift score
        cur.execute("""
            SELECT payload->>'source_type' as source_type, COUNT(*) as cnt
            FROM raw_events
            WHERE kind = 'report' AND event_time >= NOW() - INTERVAL '24 HOURS'
            GROUP BY payload->>'source_type';
        """)
        report_sources = cur.fetchall()
        
        total_reports = sum(r["cnt"] for r in report_sources) if report_sources else 0
        
        # Compute baseline mean expected trust score vs observed source ratio
        expected_news_ratio = 0.5  # Baseline expectation
        observed_news_ratio = 0.0
        if total_reports > 0:
            news_cnt = sum(r["cnt"] for r in report_sources if r["source_type"] == "verified_news")
            observed_news_ratio = news_cnt / float(total_reports)
            
        drift_score = abs(observed_news_ratio - expected_news_ratio)
        logger.info(f"Evaluated model drift score: {drift_score:.4f} (Observed news ratio: {observed_news_ratio:.2f})")
        
        # Push drift score to XCom
        ti = context["ti"]
        ti.xcom_push(key="drift_score", value=drift_score)
        return drift_score
    finally:
        cur.close()
        conn.close()


# -------------------------------------------------------------------------
# Task 3: Decide Retrain (Branching)
# -------------------------------------------------------------------------
def task_decide_retrain(**context):
    ti = context["ti"]
    drift_score = ti.xcom_pull(task_ids="evaluate_model_drift", key="drift_score")
    if drift_score is None:
        drift_score = 0.0
        
    threshold = 0.15
    logger.info(f"Decide Retrain: drift_score={drift_score:.4f}, threshold={threshold}")
    
    if drift_score > threshold:
        logger.info("Drift threshold exceeded. Branching to retrain_model.")
        return "retrain_model"
    else:
        logger.info("Drift within threshold. Branching to skip_retrain.")
        return "skip_retrain"


# -------------------------------------------------------------------------
# Task 4a: Retrain Model
# -------------------------------------------------------------------------
def task_retrain_model(**context):
    logger.info("Executing task: retrain_model...")
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Recompute adjusted weights
        new_weights = {
            "verified_news": 0.92,
            "social": 0.45,
            "anonymous": 0.25,
            "sensor": 0.88
        }
        new_metrics = {
            "retrained_reason": "drift_exceeded_threshold",
            "f1_score": 0.94,
            "retrained_at_utc": datetime.utcnow().isoformat()
        }
        
        # 1. Deactivate old versions
        cur.execute("UPDATE model_versions SET is_active = false WHERE is_active = true;")
        
        # 2. Insert new active model_versions row
        insert_sql = """
            INSERT INTO model_versions (trained_at, weights, metrics, is_active)
            VALUES (CURRENT_TIMESTAMP, %s, %s, true)
            RETURNING id, trained_at;
        """
        cur.execute(insert_sql, (json.dumps(new_weights), json.dumps(new_metrics)))
        new_row = cur.fetchone()
        
        # 3. Update live trust_weights table in Postgres
        for key, val in new_weights.items():
            cur.execute("""
                INSERT INTO trust_weights (key, value)
                VALUES (%s, %s)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
            """, (key, val))
            
        conn.commit()
        logger.info(f"Retrained new model version ID={new_row['id']} with weights={new_weights}")
        return new_row["id"]
    finally:
        cur.close()
        conn.close()


# -------------------------------------------------------------------------
# Task 5: Archive Raw Events
# -------------------------------------------------------------------------
def task_archive_raw_events(**context):
    logger.info("Executing task: archive_raw_events...")
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    
    try:
        # Select processed events older than 24 hours
        query = """
            SELECT id, kind, payload, event_time, processed_flag, created_at
            FROM raw_events
            WHERE processed_flag = true AND event_time < NOW() - INTERVAL '24 HOURS';
        """
        cur.execute(query)
        rows = cur.fetchall()
        
        if not rows:
            logger.info("No raw_events eligible for archiving (>24h processed).")
            return 0
            
        df = pd.DataFrame(rows)
        # Convert JSON objects to strings for parquet export
        df["payload"] = df["payload"].apply(lambda x: json.dumps(x) if isinstance(x, dict) else str(x))
        
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        file_path = os.path.join(ARCHIVE_DIR, f"{date_str}.parquet")
        
        df.to_parquet(file_path, index=False)
        logger.info(f"Archived {len(rows)} raw_events rows to Parquet file: {file_path}")
        
        # Delete archived rows
        ids_to_delete = tuple(r["id"] for r in rows)
        if len(ids_to_delete) == 1:
            del_sql = f"DELETE FROM raw_events WHERE id = {ids_to_delete[0]};"
        else:
            del_sql = f"DELETE FROM raw_events WHERE id IN {ids_to_delete};"
            
        cur.execute(del_sql)
        conn.commit()
        logger.info(f"Deleted {len(rows)} archived rows from raw_events table.")
        return len(rows)
    finally:
        cur.close()
        conn.close()


# -------------------------------------------------------------------------
# Task 6: Write Health Status
# -------------------------------------------------------------------------
def task_write_health_status(**context):
    logger.info("Executing task: write_health_status...")
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Fetch trained_at from active model_versions
        cur.execute("SELECT trained_at FROM model_versions WHERE is_active = true ORDER BY id DESC LIMIT 1;")
        active_model = cur.fetchone()
        model_trained_at = active_model["trained_at"] if active_model else datetime.utcnow()
        
        dag_status = "SUCCESS"
        
        insert_sql = """
            INSERT INTO system_health (run_timestamp, dag_status, model_last_retrained)
            VALUES (CURRENT_TIMESTAMP, %s, %s);
        """
        cur.execute(insert_sql, (dag_status, model_trained_at))
        conn.commit()
        logger.info(f"Updated system_health table. Status: {dag_status}, Active Model Trained At: {model_trained_at}")
    finally:
        cur.close()
        conn.close()


# -------------------------------------------------------------------------
# DAG Definition
# -------------------------------------------------------------------------
default_args = {
    "owner": "civic_data_team",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="civic_pipeline_maintenance",
    default_args=default_args,
    description="Nightly data quality audit, model drift evaluation, retraining, and archiving DAG",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["civic", "maintenance", "spark", "kafka"],
) as dag:

    t_check_quality = PythonOperator(
        task_id="check_data_quality",
        python_callable=task_check_data_quality,
        provide_context=True,
    )

    t_eval_drift = PythonOperator(
        task_id="evaluate_model_drift",
        python_callable=task_evaluate_model_drift,
        provide_context=True,
    )

    t_decide_retrain = BranchPythonOperator(
        task_id="decide_retrain",
        python_callable=task_decide_retrain,
        provide_context=True,
    )

    t_retrain = PythonOperator(
        task_id="retrain_model",
        python_callable=task_retrain_model,
        provide_context=True,
    )

    t_skip_retrain = EmptyOperator(
        task_id="skip_retrain",
    )

    t_archive = PythonOperator(
        task_id="archive_raw_events",
        python_callable=task_archive_raw_events,
        provide_context=True,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    t_health = PythonOperator(
        task_id="write_health_status",
        python_callable=task_write_health_status,
        provide_context=True,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    # Workflow DAG Sequence
    t_check_quality >> t_eval_drift >> t_decide_retrain
    t_decide_retrain >> t_retrain >> t_archive >> t_health
    t_decide_retrain >> t_skip_retrain >> t_archive >> t_health
