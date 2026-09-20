#!/bin/bash
# Script to verify the native stack services are reachable and configured correctly.

echo "============================================="
echo " Verifying Native Civic Pipeline Stack"
echo "============================================="

FAILED=0

# 1. Check Kafka on port 9092
echo -n "Checking Kafka (port 9092)... "
if nc -z localhost 9092 2>/dev/null; then
    echo "PASS"
else
    echo "FAIL (Not reachable)"
    FAILED=1
fi

# 2. Check Postgres on 5432
echo -n "Checking Postgres (port 5432)... "
if nc -z localhost 5432 2>/dev/null; then
    echo "PASS"
else
    echo "FAIL (Not reachable)"
    FAILED=1
fi

# 3. Check Postgres Database 'civic_pipeline' exists
echo -n "Checking Postgres Database 'civic_pipeline'... "
if PGPASSWORD=civic_pass psql -h localhost -U civic_user -d civic_pipeline -c '\q' 2>/dev/null; then
    echo "PASS"
else
    echo "FAIL (Database or user missing/incorrect)"
    FAILED=1
fi

# 4. Check Airflow Webserver on port 8080
echo -n "Checking Airflow Webserver (port 8080)... "
if curl -s -o /dev/null http://localhost:8080/health; then
    echo "PASS"
else
    echo "FAIL (Not reachable or not healthy)"
    FAILED=1
fi

# 5. Check Kafka Topics
echo -e "\nChecking Kafka Topics..."
if [ -z "$KAFKA_HOME" ]; then
    echo "Warning: KAFKA_HOME is not set. Assuming kafka-topics.sh is in PATH."
    KAFKA_BIN="kafka-topics.sh"
else
    KAFKA_BIN="$KAFKA_HOME/bin/kafka-topics.sh"
fi

TOPICS=("raw-sensor-events" "raw-citizen-reports" "alerts" "config-updates")

for topic in "${TOPICS[@]}"; do
    echo -n "  Topic '$topic'... "
    if $KAFKA_BIN --list --bootstrap-server localhost:9092 2>/dev/null | grep -q "^${topic}$"; then
        echo "PASS"
    else
        echo "FAIL (Missing)"
        FAILED=1
    fi
done

echo "============================================="
if [ $FAILED -eq 0 ]; then
    echo "All services verified successfully! ✅"
    exit 0
else
    echo "Some services failed verification. ❌"
    exit 1
fi
