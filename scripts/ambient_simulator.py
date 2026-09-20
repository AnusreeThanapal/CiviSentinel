#!/usr/bin/env python3
"""
Ambient Scenario Simulator Service

Continuously pushes synthetic multi-lingual Tamil & English urban disruption scenarios
into the backend REST API (POST /api/simulate) every 35-45 seconds.
Ensures live ambient background activity on the command center dashboard.
"""

import os
import sys
import time
import random
import logging

try:
    import urllib.request
    import json
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] AmbientSimulator - %(message)s")
logger = logging.getLogger("AmbientSimulator")

BACKEND_SIMULATE_URL = os.getenv("BACKEND_SIMULATE_URL", "http://backend:8000/api/simulate")
INTERVAL_SECONDS = int(os.getenv("INTERVAL_SECONDS", "35"))

AMBIENT_SCENARIOS = [
  {
    "scenario_name": "T. Nagar Water Level Rise",
    "sensor_events": [
      {
        "sensor_id": "SENS-WATER-101",
        "sensor_type": "water_level",
        "value": 4.8,
        "unit": "meters",
        "lat": 13.0827,
        "lng": 80.2707,
        "location_name": "T. Nagar Canal Zone, Chennai",
        "event_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
      }
    ],
    "citizen_reports": [
      {
        "report_id": f"REP-AMB-{int(time.time())}-1",
        "text": "தி நகரில் கால்வாய் நீர் நிரம்பி வழிகிறது. சாலையில் நீர் தேக்கம் (Canal overflowing in T. Nagar).",
        "language": "ta",
        "source_type": "verified_news",
        "lat": 13.0828,
        "lng": 80.2708,
        "location_name": "T. Nagar Canal Zone, Chennai",
        "event_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
      },
      {
        "report_id": f"REP-AMB-{int(time.time())}-2",
        "text": "Waterlogging near Usman Road flyover. Traffic moving slowly.",
        "language": "en",
        "source_type": "social",
        "lat": 13.0829,
        "lng": 80.2709,
        "location_name": "T. Nagar Canal Zone, Chennai",
        "event_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
      }
    ]
  },
  {
    "scenario_name": "Guindy Industrial Estate Inundation",
    "sensor_events": [
      {
        "sensor_id": "SENS-WATER-204",
        "sensor_type": "water_level",
        "value": 3.9,
        "unit": "meters",
        "lat": 13.0405,
        "lng": 80.2337,
        "location_name": "Guindy Estate, Chennai",
        "event_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
      }
    ],
    "citizen_reports": [
      {
        "report_id": f"REP-AMB-{int(time.time())}-3",
        "text": "Heavy water stagnation outside Guindy Metro Station blocking bus lanes.",
        "language": "en",
        "source_type": "verified_news",
        "lat": 13.0406,
        "lng": 80.2338,
        "location_name": "Guindy Estate, Chennai",
        "event_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
      },
      {
        "report_id": f"REP-AMB-{int(time.time())}-4",
        "text": "கிண்டி தொழிலதிபர் பகுதியில் பலத்த மழை நீர் தேங்கியுள்ளது",
        "language": "ta",
        "source_type": "social",
        "lat": 13.0407,
        "lng": 80.2339,
        "location_name": "Guindy Estate, Chennai",
        "event_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
      }
    ]
  },
  {
    "scenario_name": "Velachery Power Grid Trip",
    "sensor_events": [
      {
        "sensor_id": "GRID-TRANS-08",
        "sensor_type": "power_grid",
        "value": 0.0,
        "unit": "volts",
        "lat": 12.9815,
        "lng": 80.2180,
        "location_name": "Velachery Main Substation",
        "event_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
      },
      {
        "sensor_id": "GRID-TRANS-09",
        "sensor_type": "power_grid",
        "value": 0.0,
        "unit": "volts",
        "lat": 12.9816,
        "lng": 80.2181,
        "location_name": "Velachery Main Substation",
        "event_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
      }
    ],
    "citizen_reports": [
      {
        "report_id": f"REP-AMB-{int(time.time())}-5",
        "text": "வேளச்சேரியில் கடந்த 30 நிமிடங்களாக மின்சாரம் துண்டிக்கப்பட்டுள்ளது",
        "language": "ta",
        "source_type": "social",
        "lat": 12.9817,
        "lng": 80.2182,
        "location_name": "Velachery Main Substation",
        "event_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
      }
    ]
  }
]

def send_simulation_request(payload):
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BACKEND_SIMULATE_URL,
        data=data_bytes,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
            logger.info(f"Published scenario '{payload.get('scenario_name')}'. Backend response: {res_body}")
            return True
    except Exception as e:
        logger.warning(f"Could not reach backend at {BACKEND_SIMULATE_URL} ({e}). Retrying next interval...")
        return False

def main():
    logger.info("Starting Ambient Scenario Simulator loop...")
    logger.info(f"Target Backend API: {BACKEND_SIMULATE_URL}")
    logger.info(f"Interval: {INTERVAL_SECONDS} seconds.")
    
    # Wait initial 15s for backend and spark startup
    time.sleep(15)
    
    scenario_idx = 0
    while True:
        try:
            scenario = AMBIENT_SCENARIOS[scenario_idx % len(AMBIENT_SCENARIOS)]
            # Update timestamps dynamically
            now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            for s in scenario["sensor_events"]:
                s["event_time"] = now_iso
            for c in scenario["citizen_reports"]:
                c["event_time"] = now_iso
                c["report_id"] = f"REP-AMB-{int(time.time())}-{random.randint(100, 999)}"
                
            send_simulation_request(scenario)
            scenario_idx += 1
        except Exception as e:
            logger.error(f"Unexpected error in simulation loop: {e}")
            
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
