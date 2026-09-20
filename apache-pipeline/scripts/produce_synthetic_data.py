#!/usr/bin/env python3
"""
Synthetic Scenario Data Generator for Civic Disruption Early-Warning System

Publishes a synthetic flooding scenario:
- 2 sensor readings (water_level)
- 3 citizen/news reports (Tamil & English, verified_news, social, anonymous)
All clustered in the same spatial grid (~13.0827, 80.2707 - T. Nagar, Chennai) and time window.
"""

import os
import sys
import json
import time
from datetime import datetime

try:
    from kafka import KafkaProducer
except ImportError:
    print("[!] kafka-python package not installed. Install with: pip install kafka-python")
    sys.exit(1)

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

def json_serializer(data):
    return json.dumps(data).encode("utf-8")

def main():
    print(f"Connecting to Kafka producer at {KAFKA_BOOTSTRAP}...")
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=json_serializer
    )

    now_iso = datetime.utcnow().isoformat() + "Z"
    location_lat = 13.0827
    location_lng = 80.2707
    location_name = "T. Nagar Canal Zone, Chennai"

    # 1. Synthetic Sensor Readings (2 sensors)
    sensor_events = [
        {
            "sensor_id": "SENS-WATER-101",
            "sensor_type": "water_level",
            "value": 4.8,
            "unit": "meters",
            "lat": location_lat,
            "lng": location_lng,
            "location_name": location_name,
            "event_time": now_iso
        },
        {
            "sensor_id": "SENS-WATER-102",
            "sensor_type": "water_level",
            "value": 5.2,
            "unit": "meters",
            "lat": location_lat + 0.0001,
            "lng": location_lng - 0.0001,
            "location_name": location_name,
            "event_time": now_iso
        }
    ]

    # 2. Synthetic Citizen/News Reports (3 reports in Tamil & English)
    citizen_reports = [
        {
            "report_id": "REP-NEWS-001",
            "text": "BREAKING: Severe waterlogging and flooding reported near T. Nagar canal after heavy rainfall.",
            "language": "en",
            "source_type": "verified_news",
            "lat": location_lat + 0.0002,
            "lng": location_lng + 0.0001,
            "location_name": location_name,
            "event_time": now_iso
        },
        {
            "report_id": "REP-TA-002",
            "text": "தி நகர் பகுதியில் வீடுகளுக்குள் வெள்ளம் புகுந்தது. சாக்கடை நீர் பெருக்கெடுத்து ஓடுகிறது (Homes flooded in T. Nagar area).",
            "language": "ta",
            "source_type": "social",
            "lat": location_lat - 0.0001,
            "lng": location_lng + 0.0002,
            "location_name": location_name,
            "event_time": now_iso
        },
        {
            "report_id": "REP-SOC-003",
            "text": "Canal water overflowing onto main street. Vehicles submerged near T. Nagar.",
            "language": "en",
            "source_type": "anonymous",
            "lat": location_lat + 0.0001,
            "lng": location_lng - 0.0002,
            "location_name": location_name,
            "event_time": now_iso
        }
    ]

    print("\n--- Publishing Synthetic Sensor Events ---")
    for s_event in sensor_events:
        producer.send("raw-sensor-events", value=s_event)
        print(f"[+] Sent sensor event: {s_event['sensor_id']} (value={s_event['value']} {s_event['unit']})")
        time.sleep(0.2)

    print("\n--- Publishing Synthetic Citizen Reports ---")
    for c_report in citizen_reports:
        producer.send("raw-citizen-reports", value=c_report)
        print(f"[+] Sent citizen report: {c_report['report_id']} ({c_report['language']}/{c_report['source_type']})")
        time.sleep(0.2)

    producer.flush()
    print("\n[✔] All synthetic events successfully published!")

if __name__ == "__main__":
    main()
