#!/bin/bash
# Script to start native stack background services and print instructions for foreground services.

echo "============================================="
echo " Starting Native Civic Pipeline Stack"
echo "============================================="

echo -e "\n[1/2] Starting PostgreSQL natively..."
if command -v systemctl &> /dev/null; then
    sudo systemctl start postgresql
elif command -v service &> /dev/null; then
    sudo service postgresql start
else
    echo "Warning: Could not automatically start PostgreSQL. Please start it manually."
fi

echo -e "\n[2/2] Printing Launch Instructions for Foreground Services"
echo "The remaining services require their own terminal windows to stay foregrounded."
echo "Please open 5 separate terminal windows and run the following commands:"

echo -e "\n---------------------------------------------"
echo "Terminal 1: Zookeeper"
echo "---------------------------------------------"
echo "cd /path/to/kafka_2.13-3.7.2"
echo "bin/zookeeper-server-start.sh config/zookeeper.properties"

echo -e "\n---------------------------------------------"
echo "Terminal 2: Kafka Broker"
echo "---------------------------------------------"
echo "cd /path/to/kafka_2.13-3.7.2"
echo "bin/kafka-server-start.sh config/server.properties"

echo -e "\n---------------------------------------------"
echo "Terminal 3: Airflow Webserver"
echo "---------------------------------------------"
echo "source /path/to/airflow-venv/bin/activate"
echo "export AIRFLOW_HOME=/path/to/airflow_home"
echo "export APP_DB_HOST=localhost"
echo "export ARCHIVE_DIR=\$AIRFLOW_HOME/archives"
echo "airflow webserver -p 8080"

echo -e "\n---------------------------------------------"
echo "Terminal 4: Airflow Scheduler"
echo "---------------------------------------------"
echo "source /path/to/airflow-venv/bin/activate"
echo "export AIRFLOW_HOME=/path/to/airflow_home"
echo "export APP_DB_HOST=localhost"
echo "export ARCHIVE_DIR=\$AIRFLOW_HOME/archives"
echo "airflow scheduler"

echo -e "\n---------------------------------------------"
echo "Terminal 5: Spark Correlator"
echo "---------------------------------------------"
echo "cd $(pwd)"
echo "export SPARK_HOME=/path/to/spark-3.5.1-bin-hadoop3"
echo "export PYSPARK_PYTHON=\$(which python3.11)"
echo "export PYSPARK_DRIVER_PYTHON=\$(which python3.11)"
echo "./apache-pipeline/spark/run_spark_job.sh"

echo -e "\n============================================="
echo "Once all services are running, you can run the simulator:"
echo "python scripts/ambient_simulator.py"
echo "============================================="
