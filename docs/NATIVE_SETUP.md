# Native Setup Guide (No Docker)

This guide covers setting up the Real-Time Civic Disruption Early-Warning System natively on your local machine, without using Docker. This setup requires running Kafka, Spark, and Airflow as local processes.

## 1. Prerequisites

- **OS:** WSL2 Ubuntu, native Linux, or macOS.
- **Java:** Java 17 (Required for Kafka and Spark).
- **Python:** Python 3.11. 
  - **Important:** Airflow 2.9.1 requires Python 3.8 - 3.12. Python 3.14+ will **NOT** work for the Airflow or PySpark driver side. We strongly recommend using `pyenv` to install and set Python 3.11 locally if your system default is newer.

## 2. Kafka 3.7.2 Manual Installation

Kafka 3.7.2 must be downloaded from the Apache archives (the main downloads mirror only keeps the most current releases).

```bash
# Download and Extract
wget https://archive.apache.org/dist/kafka/3.7.2/kafka_2.13-3.7.2.tgz
tar -xzf kafka_2.13-3.7.2.tgz
cd kafka_2.13-3.7.2
export KAFKA_HOME=$(pwd)

# Start Zookeeper (in a separate terminal)
bin/zookeeper-server-start.sh config/zookeeper.properties

# Start Kafka Broker (in a separate terminal)
bin/kafka-server-start.sh config/server.properties

# Create required topics
bin/kafka-topics.sh --create --topic raw-sensor-events --bootstrap-server localhost:9092
bin/kafka-topics.sh --create --topic raw-citizen-reports --bootstrap-server localhost:9092
bin/kafka-topics.sh --create --topic alerts --bootstrap-server localhost:9092
bin/kafka-topics.sh --create --topic config-updates --bootstrap-server localhost:9092
```

## 3. Spark 3.5.1 Manual Installation

```bash
# Download and Extract
wget https://archive.apache.org/dist/spark/spark-3.5.1/spark-3.5.1-bin-hadoop3.tgz
tar -xzf spark-3.5.1-bin-hadoop3.tgz
export SPARK_HOME=$(pwd)/spark-3.5.1-bin-hadoop3

# Ensure PYSPARK_PYTHON points to your Python 3.11 interpreter
export PYSPARK_PYTHON=$(which python3.11)
```

## 4. PostgreSQL Native Installation

```bash
# Install PostgreSQL
sudo apt update
sudo apt install -y postgresql postgresql-contrib

# Start service
sudo service postgresql start

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE civic_pipeline;"
sudo -u postgres psql -c "CREATE USER civic_user WITH PASSWORD 'civic_pass';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE civic_pipeline TO civic_user;"

# Apply initialization schema (from the repository root)
PGPASSWORD=civic_pass psql -h localhost -U civic_user -d civic_pipeline -f apache-pipeline/postgres/init.sql
```

## 5. Airflow 2.9.1 Manual Installation

Airflow requires specific constraints to install properly.

```bash
# Create and activate a Python 3.11 virtual environment
python3.11 -m venv airflow-venv
source airflow-venv/bin/activate

# Install Airflow with strict constraints
AIRFLOW_VERSION=2.9.1
PYTHON_VERSION=3.11
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"

# Initialize Database
export AIRFLOW_HOME=$(pwd)/airflow_home
airflow db init

# Create Admin User
airflow users create \
    --username admin \
    --password admin \
    --firstname Civic \
    --lastname Admin \
    --role Admin \
    --email admin@example.com

# Setup DAGs and Archives
mkdir -p $AIRFLOW_HOME/dags
mkdir -p $AIRFLOW_HOME/archives
cp apache-pipeline/dags/civic_pipeline_maintenance_dag.py $AIRFLOW_HOME/dags/
```

**Important Airflow Environment Variables when running natively:**
You must override these defaults so they point to localhost and native directories (instead of docker container defaults):
```bash
export APP_DB_HOST=localhost
export ARCHIVE_DIR=$AIRFLOW_HOME/archives
```

## 6. Running the Spark Correlator Natively

To run the Spark streaming job, ensure your PySpark environment variables are pointing to Python 3.11, then execute the wrapper script:

```bash
export PYSPARK_PYTHON=$(which python3.11)
export PYSPARK_DRIVER_PYTHON=$(which python3.11)
./apache-pipeline/spark/run_spark_job.sh
```

## 7. Running the Synthetic Data Producer

To feed live synthetic data into the pipeline (which would normally be handled by the simulator docker container), run the simulator script locally:

```bash
# In the repository root
pip install -r backend/requirements.txt # Make sure kafka-python is installed
python scripts/ambient_simulator.py
```
