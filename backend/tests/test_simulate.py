import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_simulate_endpoint_valid_payload():
    payload = {
        "scenario_name": "Tamil & English Flooding Test",
        "sensor_events": [
            {
                "sensor_id": "SENS-001",
                "sensor_type": "water_level",
                "value": 4.5,
                "unit": "meters",
                "lat": 13.0827,
                "lng": 80.2707,
                "location_name": "T. Nagar",
                "event_time": "2026-09-05T12:00:00Z"
            }
        ],
        "citizen_reports": [
            {
                "report_id": "REP-TA-01",
                "text": "தி நகரில் பெரும் வெள்ளப்பெருக்கு (Severe flooding in T. Nagar)",
                "language": "ta",
                "source_type": "verified_news",
                "lat": 13.0828,
                "lng": 80.2708,
                "location_name": "T. Nagar",
                "event_time": "2026-09-05T12:01:00Z"
            },
            {
                "report_id": "REP-EN-02",
                "text": "Water levels rising quickly near canal.",
                "language": "en",
                "source_type": "social",
                "lat": 13.0829,
                "lng": 80.2709,
                "location_name": "T. Nagar",
                "event_time": "2026-09-05T12:02:00Z"
            }
        ]
    }

    with patch("app.routers.simulate.publish_raw_event", return_value=True) as mock_pub:
        response = client.post("/api/simulate", json=payload)
        assert response.status_code == 201
        res_data = response.json()
        assert res_data["status"] == "SUCCESS"
        assert res_data["sensor_events_published"] == 1
        assert res_data["citizen_reports_published"] == 2

        # Verify publish_raw_event called 3 times
        assert mock_pub.call_count == 3

def test_simulate_endpoint_invalid_payload():
    invalid_payload = {
        "sensor_events": [
            {
                "sensor_id": "SENS-INVALID",
                "sensor_type": "invalid_type_enum", # Invalid literal
                "value": 4.5,
                "lat": 13.08,
                "lng": 80.27
            }
        ]
    }
    response = client.post("/api/simulate", json=invalid_payload)
    assert response.status_code == 422 # Validation error
