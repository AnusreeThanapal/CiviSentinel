# Civic Disruption Early-Warning System: Live Demo Script

1. **Native Data Injection**: "First, we'll start our Kafka broker locally and run our native producer script to begin streaming synthetic telemetry and citizen reports into the raw Kafka topics."
2. **Native Real-Time Correlation**: "Next, we launch our PySpark correlator in a local terminal, which streams from those topics, dynamically scores trust, and emits high-confidence alerts back to Kafka."
3. **Automated Maintenance**: "Here in the Airflow UI, we trigger our nightly DAG; you can see all 7 tasks succeed, simulating the daily audit, model drift evaluation, retraining, and data archiving."
4. **Production Docker Stack**: "While that ran natively, we can package this entire 12-service architecture using Docker Compose, bringing up Zookeeper, Kafka, Spark, Airflow, Postgres, FastAPI, and React with a single command for production deployment."
5. **Command Center Dashboard**: "Finally, looking at our React dashboard connected to the backend WebSocket, you can watch real-time disruption alerts instantly appear on the map as soon as they are correlated by the pipeline."
