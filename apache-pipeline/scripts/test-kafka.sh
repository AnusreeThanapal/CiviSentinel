#!/usr/bin/env bash
set -e

KAFKA_CONTAINER=${KAFKA_CONTAINER:-"civic-kafka"}
BOOTSTRAP_SERVER="localhost:9092"
INTERNAL_BOOTSTRAP="localhost:9092"

echo "=========================================="
echo " Testing Kafka Setup & Message Pub/Sub "
echo "=========================================="

# Check container status
if docker ps | grep -q "$KAFKA_CONTAINER"; then
  echo "[+] Kafka container '$KAFKA_CONTAINER' is running."
  EXEC_CMD="docker exec -i $KAFKA_CONTAINER /opt/bitnami/kafka/bin"
else
  echo "[!] Kafka container '$KAFKA_CONTAINER' not found locally via Docker. Using local binary fallback..."
  EXEC_CMD=""
fi

echo ""
echo "--- 1. Verifying Created Topics ---"
if [ -n "$EXEC_CMD" ]; then
  docker exec -i $KAFKA_CONTAINER /opt/bitnami/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list
else
  kafka-topics.sh --bootstrap-server $BOOTSTRAP_SERVER --list
fi

echo ""
echo "--- 2. Publishing Sample Message to 'raw-sensor-events' ---"
SENSOR_MSG='{"sensor_id":"SENS-WATER-001","sensor_type":"water_level","value":4.5,"unit":"meters","lat":13.0827,"lng":80.2707,"location_name":"T. Nagar Canal","event_time":"2026-09-05T12:00:00Z"}'

if [ -n "$EXEC_CMD" ]; then
  echo "$SENSOR_MSG" | docker exec -i $KAFKA_CONTAINER /opt/bitnami/kafka/bin/kafka-console-producer.sh --bootstrap-server localhost:9092 --topic raw-sensor-events
else
  echo "$SENSOR_MSG" | kafka-console-producer.sh --bootstrap-server $BOOTSTRAP_SERVER --topic raw-sensor-events
fi
echo "[+] Sent sensor message."

echo ""
echo "--- 3. Publishing Sample Message to 'raw-citizen-reports' ---"
CITIZEN_MSG='{"report_id":"REP-TA-001","text":"தி நகரில் பெரும் வெள்ளப்பெருக்கு ஏற்பட்டுள்ளது (Severe flooding in T. Nagar)","language":"ta","source_type":"verified_news","lat":13.0830,"lng":80.2710,"location_name":"T. Nagar Central","event_time":"2026-09-05T12:01:00Z"}'

if [ -n "$EXEC_CMD" ]; then
  echo "$CITIZEN_MSG" | docker exec -i $KAFKA_CONTAINER /opt/bitnami/kafka/bin/kafka-console-producer.sh --bootstrap-server localhost:9092 --topic raw-citizen-reports
else
  echo "$CITIZEN_MSG" | kafka-console-producer.sh --bootstrap-server $BOOTSTRAP_SERVER --topic raw-citizen-reports
fi
echo "[+] Sent citizen report message."

echo ""
echo "--- 4. Consuming Published Messages (Timeout 5s) ---"
echo "Fetching from 'raw-sensor-events':"
if [ -n "$EXEC_CMD" ]; then
  docker exec -i $KAFKA_CONTAINER /opt/bitnami/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic raw-sensor-events --from-beginning --max-messages 1 --timeout-ms 5000
fi

echo ""
echo "Fetching from 'raw-citizen-reports':"
if [ -n "$EXEC_CMD" ]; then
  docker exec -i $KAFKA_CONTAINER /opt/bitnami/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic raw-citizen-reports --from-beginning --max-messages 1 --timeout-ms 5000
fi

echo ""
echo "=========================================="
echo " Kafka Sanity Check Complete! Success. "
echo "=========================================="
