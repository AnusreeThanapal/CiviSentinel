#!/usr/bin/env bash
set -e

echo "========================================================="
echo " Starting Spark Structured Streaming Correlator Job     "
echo " Target Spark: 3.5.x (Scala 2.12)                        "
echo "========================================================="

export KAFKA_BOOTSTRAP_SERVERS=${KAFKA_BOOTSTRAP_SERVERS:-"localhost:9092"}
export POSTGRES_JDBC_URL=${POSTGRES_JDBC_URL:-"jdbc:postgresql://localhost:5432/civic_pipeline"}
export POSTGRES_USER=${POSTGRES_USER:-"civic_user"}
export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-"civic_pass"}
export MIN_TRUST_THRESHOLD=${MIN_TRUST_THRESHOLD:-"0.6"}

SPARK_PACKAGES="org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.postgresql:postgresql:42.7.3"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
CORRELATOR_SCRIPT="$SCRIPT_DIR/stream_correlator.py"

echo "[+] Submitting PySpark job with packages:"
echo "    $SPARK_PACKAGES"
echo "[+] Kafka Bootstrap: $KAFKA_BOOTSTRAP_SERVERS"
echo "[+] Postgres JDBC URL: $POSTGRES_JDBC_URL"
echo ""

spark-submit \
  --master "local[*]" \
  --packages "$SPARK_PACKAGES" \
  --driver-memory 2g \
  "$CORRELATOR_SCRIPT"
