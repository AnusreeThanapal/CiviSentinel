#!/usr/bin/env python3
"""
Real-Time Civic Disruption Early-Warning System
Spark Structured Streaming Correlator Engine (PySpark)

This script:
1. Reads raw-sensor-events and raw-citizen-reports streams from Kafka.
2. Parses JSON values using explicit StructType schemas.
3. Applies watermarks (5 minutes) and spatial grid cell bucketing (~500m).
4. Correlates events over a 2-minute tumbling window across grid cells.
5. In foreachBatch:
   - Queries trust_weights from Postgres via JDBC.
   - Computes trust scores (supporting sensor+report, report-only, and sensor-only clusters).
   - Filters alerts (trust_score >= 0.6).
   - Formulates dynamic alert JSON and publishes to Kafka 'alerts' topic.
   - Writes all raw events processed in the batch into Postgres 'raw_events' table.

Targeted Spark Version: Spark 3.5.x (Scala 2.12)
Required Packages: org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.postgresql:postgresql:42.7.3
"""

import os
import sys
import json
import logging
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, to_json, struct, floor, concat, lit, coalesce,
    window, collect_list, sum as _sum, avg, first, expr, when
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, TimestampType, BooleanType
)

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CivicStreamCorrelator")

# Configuration via environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
POSTGRES_JDBC_URL = os.getenv("POSTGRES_JDBC_URL", "jdbc:postgresql://localhost:5432/civic_pipeline")
POSTGRES_USER = os.getenv("POSTGRES_USER", "civic_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "civic_pass")
MIN_TRUST_THRESHOLD = float(os.getenv("MIN_TRUST_THRESHOLD", "0.6"))

# Define explicit schemas for input Kafka topics
SENSOR_SCHEMA = StructType([
    StructField("sensor_id", StringType(), False),
    StructField("sensor_type", StringType(), False),
    StructField("value", DoubleType(), False),
    StructField("unit", StringType(), True),
    StructField("lat", DoubleType(), False),
    StructField("lng", DoubleType(), False),
    StructField("location_name", StringType(), True),
    StructField("event_time", StringType(), False)
])

REPORT_SCHEMA = StructType([
    StructField("report_id", StringType(), False),
    StructField("text", StringType(), False),
    StructField("language", StringType(), False),
    StructField("source_type", StringType(), False),
    StructField("lat", DoubleType(), False),
    StructField("lng", DoubleType(), False),
    StructField("location_name", StringType(), True),
    StructField("event_time", StringType(), False)
])


def fetch_trust_weights_from_db(spark):
    """
    Reads the trust_weights table from Postgres via JDBC.
    Returns a dictionary of key -> float weight.
    Fallback default weights are returned if query fails or table is empty.
    """
    default_weights = {
        "verified_news": 0.9,
        "social": 0.4,
        "anonymous": 0.2,
        "sensor": 0.85
    }
    try:
        weights_df = spark.read \
            .format("jdbc") \
            .option("url", POSTGRES_JDBC_URL) \
            .option("dbtable", "trust_weights") \
            .option("user", POSTGRES_USER) \
            .option("password", POSTGRES_PASSWORD) \
            .option("driver", "org.postgresql.Driver") \
            .load()
        
        db_weights = {}
        for row in weights_df.collect():
            db_weights[row['key']] = float(row['value'])
        
        if db_weights:
            logger.info(f"Loaded trust weights from Postgres: {db_weights}")
            return db_weights
    except Exception as e:
        logger.warning(f"Could not load trust_weights from Postgres ({e}). Using default weights.")
    
    return default_weights


def compute_trust_score(signals, weights):
    """
    Computes trust score for a group of correlated signals in a spatial-temporal cell.
    Formula:
      - Report Score = min(1.0, sum of source_type weights for reports)
      - Sensor Score = weight('sensor') if sensor signals exist else 0.0
      - Combined Score = min(1.0, Report Score + Sensor Score) if report-only or sensor-only,
                         or weighted blend min(1.0, Report Score * 0.6 + Sensor Score * 0.5) when both present.
    Returns: (score, reasoning_string, alert_type, contributing_signals_list)
    """
    reports = [s for s in signals if s.get("kind") == "report"]
    sensors = [s for s in signals if s.get("kind") == "sensor"]
    
    # 1. Report score calculation
    report_weight_sum = 0.0
    for r in reports:
        src = r.get("source_type", "anonymous")
        report_weight_sum += weights.get(src, 0.2)
    report_score = min(1.0, report_weight_sum)
    
    # 2. Sensor score calculation
    sensor_weight_sum = 0.0
    if len(sensors) > 0:
        sensor_weight_sum = weights.get("sensor", 0.85)
    sensor_score = min(1.0, sensor_weight_sum)
    
    # 3. Trust Score normalization
    if len(reports) > 0 and len(sensors) > 0:
        # Both present: strong corroboration boost
        trust_score = min(1.0, (report_score * 0.5) + (sensor_score * 0.5) + 0.15)
    elif len(reports) > 0:
        # Report only cluster
        trust_score = report_score
    else:
        # Sensor only cluster
        trust_score = sensor_score

    # Construct contributing signals list for output schema
    contributing_signals = []
    for s in sensors:
        contributing_signals.append({
            "kind": "sensor",
            "sensor_id": s.get("signal_id"),
            "value": float(s.get("value", 0.0)),
            "unit": s.get("unit", "")
        })
    for r in reports:
        contributing_signals.append({
            "kind": "report",
            "text": r.get("text", ""),
            "language": r.get("language", "en"),
            "source_type": r.get("source_type", "anonymous")
        })

    # Construct dynamic reasoning string
    n_sensors = len(sensors)
    n_reports = len(reports)
    reasoning = f"{n_sensors} sensor signal(s) + {n_reports} corroborating report(s), trust score {trust_score:.2f}"

    # Determine disruption type based on sensor_type or text content
    disruption_type = "flooding"
    all_text = " ".join([r.get("text", "") for r in reports]).lower()
    sensor_types = [s.get("sensor_type", "") for s in sensors]
    
    if "power" in all_text or "power_grid" in sensor_types or "மின்சார" in all_text:
        disruption_type = "power_outage"
    elif "waterlogging" in all_text or "தேங்கிய" in all_text:
        disruption_type = "waterlogging"
    elif "water_level" in sensor_types or "வெள்ள" in all_text or "flood" in all_text:
        disruption_type = "flooding"

    return trust_score, reasoning, disruption_type, contributing_signals


def process_micro_batch(batch_df, batch_id, spark):
    """
    foreachBatch sink callback:
    1. Fetches current weights from DB.
    2. Processes correlated groups, calculates trust scores.
    3. Publishes alerts >= MIN_TRUST_THRESHOLD to Kafka 'alerts' topic.
    4. Writes ALL processed raw events in batch to Postgres 'raw_events' table.
    """
    logger.info(f"=== Processing Micro-Batch ID: {batch_id} ===")
    
    # Materialize batch rows
    batch_rows = batch_df.collect()
    total_grouped_cells = len(batch_rows)
    logger.info(f"Batch {batch_id}: Received {total_grouped_cells} correlated spatial-temporal cell(s).")
    
    if total_grouped_cells == 0:
        logger.info(f"Batch {batch_id}: No events to process.")
        return

    # Fetch live trust weights from Postgres
    weights = fetch_trust_weights_from_db(spark)
    
    alerts_to_publish = []
    raw_events_to_store = []
    
    total_raw_events_count = 0
    alerts_count = 0
    
    for row in batch_rows:
        signals_raw = row['signals']
        avg_lat = float(row['avg_lat']) if row['avg_lat'] is not None else 0.0
        avg_lng = float(row['avg_lng']) if row['avg_lng'] is not None else 0.0
        location_name = row['sample_location'] or "Unknown Location"
        
        # Convert Spark Row structs to Python dicts
        signals = [s.asDict() for s in signals_raw]
        total_raw_events_count += len(signals)
        
        # Collect raw events for Postgres audit table
        for s in signals:
            raw_events_to_store.append({
                "kind": s["kind"],
                "payload": json.loads(s["raw_json"]) if s.get("raw_json") else {},
                "event_time": str(s["event_time"])
            })
        
        # Compute trust score
        trust_score, reasoning, alert_type, contributing_signals = compute_trust_score(signals, weights)
        
        # Check threshold
        if trust_score >= MIN_TRUST_THRESHOLD:
            alerts_count += 1
            alert_id = f"ALT-{int(datetime.utcnow().timestamp())}-{row['grid_cell']}"
            alert_payload = {
                "alert_id": alert_id,
                "type": alert_type,
                "location": {
                    "lat": round(avg_lat, 4),
                    "lng": round(avg_lng, 4),
                    "name": location_name
                },
                "trust_score": round(trust_score, 2),
                "reasoning": reasoning,
                "contributing_signals": contributing_signals,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            alerts_to_publish.append(alert_payload)

    logger.info(f"Batch {batch_id}: Processed {total_raw_events_count} raw event(s) -> Generated {alerts_count} alert(s).")

    # 1. Publish Alerts to Kafka 'alerts' topic
    if alerts_to_publish:
        try:
            alert_records = [(a["alert_id"], json.dumps(a)) for a in alerts_to_publish]
            alert_df = spark.createDataFrame(alert_records, ["key", "value"])
            alert_df.write \
                .format("kafka") \
                .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
                .option("topic", "alerts") \
                .save()
            logger.info(f"Batch {batch_id}: Successfully published {len(alerts_to_publish)} alert(s) to Kafka 'alerts' topic.")
        except Exception as e:
            logger.error(f"Batch {batch_id}: Failed to publish alerts to Kafka: {e}")

    # 2. Write ALL raw events to Postgres 'raw_events' table
    if raw_events_to_store:
        try:
            # Build DataFrame matching raw_events schema
            db_rows = []
            for item in raw_events_to_store:
                db_rows.append((
                    item["kind"],
                    json.dumps(item["payload"]),
                    item["event_time"],
                    True  # processed_flag
                ))
            
            raw_df = spark.createDataFrame(db_rows, ["kind", "payload_str", "event_time_str", "processed_flag"])
            
            # Use SQL expression to cast json and timestamp for JDBC
            from pyspark.sql.functions import to_timestamp
            formatted_raw_df = raw_df \
                .withColumn("payload", expr("CAST(payload_str AS STRING)")) \
                .withColumn("event_time", to_timestamp(col("event_time_str"))) \
                .select("kind", "payload", "event_time", "processed_flag")

            formatted_raw_df.write \
                .format("jdbc") \
                .option("url", POSTGRES_JDBC_URL) \
                .option("dbtable", "raw_events") \
                .option("user", POSTGRES_USER) \
                .option("password", POSTGRES_PASSWORD) \
                .option("driver", "org.postgresql.Driver") \
                .option("stringtype", "unspecified") \
                .mode("append") \
                .save()
            logger.info(f"Batch {batch_id}: Successfully wrote {len(raw_events_to_store)} raw event(s) to Postgres raw_events table.")
        except Exception as e:
            logger.error(f"Batch {batch_id}: Failed to write raw events to Postgres: {e}")


def main():
    logger.info("Initializing Spark Session for Civic Stream Correlator...")
    spark = SparkSession.builder \
        .appName("CivicDisruptionStreamCorrelator") \
        .config("spark.sql.session.timeZone", "UTC") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")

    logger.info(f"Connecting to Kafka at {KAFKA_BOOTSTRAP_SERVERS}...")

    # 1. Read Stream: raw-sensor-events
    sensor_raw_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", "raw-sensor-events") \
        .option("startingOffsets", "latest") \
        .load()

    sensor_parsed_df = sensor_raw_df \
        .select(col("value").cast("string").alias("json_str")) \
        .select(from_json(col("json_str"), SENSOR_SCHEMA).alias("data"), col("json_str")) \
        .select("data.*", "json_str") \
        .filter(col("sensor_id").isNotNull() & col("event_time").isNotNull()) \
        .withColumn("event_timestamp", to_timestamp(col("event_time"))) \
        .withColumn("grid_lat", floor(col("lat") / lit(0.0045))) \
        .withColumn("grid_lng", floor(col("lng") / lit(0.0045))) \
        .withColumn("grid_cell", concat(col("grid_lat"), lit("_"), col("grid_lng"))) \
        .select(
            lit("sensor").alias("kind"),
            col("sensor_id").alias("signal_id"),
            col("grid_cell"),
            col("event_timestamp").alias("event_time"),
            col("lat"),
            col("lng"),
            col("location_name"),
            col("sensor_type"),
            col("value"),
            col("unit"),
            lit(None).cast("string").alias("text"),
            lit(None).cast("string").alias("language"),
            lit(None).cast("string").alias("source_type"),
            col("json_str").alias("raw_json")
        )

    # 2. Read Stream: raw-citizen-reports
    report_raw_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", "raw-citizen-reports") \
        .option("startingOffsets", "latest") \
        .load()

    report_parsed_df = report_raw_df \
        .select(col("value").cast("string").alias("json_str")) \
        .select(from_json(col("json_str"), REPORT_SCHEMA).alias("data"), col("json_str")) \
        .select("data.*", "json_str") \
        .filter(col("report_id").isNotNull() & col("event_time").isNotNull()) \
        .withColumn("event_timestamp", to_timestamp(col("event_time"))) \
        .withColumn("grid_lat", floor(col("lat") / lit(0.0045))) \
        .withColumn("grid_lng", floor(col("lng") / lit(0.0045))) \
        .withColumn("grid_cell", concat(col("grid_lat"), lit("_"), col("grid_lng"))) \
        .select(
            lit("report").alias("kind"),
            col("report_id").alias("signal_id"),
            col("grid_cell"),
            col("event_timestamp").alias("event_time"),
            col("lat"),
            col("lng"),
            col("location_name"),
            lit(None).cast("string").alias("sensor_type"),
            lit(None).cast("double").alias("value"),
            lit(None).cast("string").alias("unit"),
            col("text"),
            col("language"),
            col("source_type"),
            col("json_str").alias("raw_json")
        )

    # 3. Union streams to allow sensor-only, report-only, and combined correlation
    unified_signals_df = sensor_parsed_df.union(report_parsed_df)

    # 4. Apply Watermark (5 minutes) on event_time
    watermarked_df = unified_signals_df \
        .withWatermark("event_time", "5 minutes")

    # 5. Group by grid_cell and 2-minute tumbling window
    grouped_df = watermarked_df \
        .groupBy(
            col("grid_cell"),
            window(col("event_time"), "2 minutes")
        ) \
        .agg(
            collect_list(
                struct(
                    "kind", "signal_id", "grid_cell", "event_time",
                    "lat", "lng", "location_name", "sensor_type",
                    "value", "unit", "text", "language", "source_type", "raw_json"
                )
            ).alias("signals"),
            avg("lat").alias("avg_lat"),
            avg("lng").alias("avg_lng"),
            first("location_name").alias("sample_location")
        )

    # 6. Start Structured Streaming query using foreachBatch sink
    logger.info("Starting PySpark Structured Streaming query...")
    
    query = grouped_df.writeStream \
        .outputMode("update") \
        .foreachBatch(lambda df, b_id: process_micro_batch(df, b_id, spark)) \
        .option("checkpointLocation", "/tmp/spark_civic_correlator_checkpoint") \
        .start()

    query.awaitTermination()


if __name__ == "__main__":
    main()
