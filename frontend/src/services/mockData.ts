import { Alert, SystemHealth, SimulationRequest } from '../types';

export const INITIAL_MOCK_ALERTS: Alert[] = [
  {
    alert_id: 'ALT-2026-0905-001',
    type: 'flooding',
    location: {
      lat: 13.0827,
      lng: 80.2707,
      name: 'T. Nagar Canal Zone, Chennai'
    },
    trust_score: 0.92,
    reasoning: '2 water level sensor signals (5.2m) + 3 corroborating reports (Tamil news & social), trust score 0.92',
    contributing_signals: [
      { kind: 'sensor', sensor_id: 'SENS-WATER-101', value: 4.8, unit: 'meters' },
      { kind: 'sensor', sensor_id: 'SENS-WATER-102', value: 5.2, unit: 'meters' },
      { kind: 'report', text: 'BREAKING: Severe waterlogging and flooding reported near T. Nagar canal after heavy rainfall.', language: 'en', source_type: 'verified_news' },
      { kind: 'report', text: 'தி நகர் பகுதியில் வீடுகளுக்குள் வெள்ளம் புகுந்தது. சாக்கடை நீர் பெருக்கெடுத்து ஓடுகிறது', language: 'ta', source_type: 'social' },
      { kind: 'report', text: 'Canal water overflowing onto main street. Vehicles submerged near T. Nagar.', language: 'en', source_type: 'anonymous' }
    ],
    timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString()
  },
  {
    alert_id: 'ALT-2026-0905-002',
    type: 'waterlogging',
    location: {
      lat: 13.0405,
      lng: 80.2337,
      name: 'Guindy Industrial Estate, Chennai'
    },
    trust_score: 0.78,
    reasoning: '1 water level sensor (3.4m) + 2 news reports confirmed waterlogging, trust score 0.78',
    contributing_signals: [
      { kind: 'sensor', sensor_id: 'SENS-WATER-204', value: 3.4, unit: 'meters' },
      { kind: 'report', text: 'Heavy water stagnation outside Guindy Metro Station blocking traffic lanes.', language: 'en', source_type: 'verified_news' },
      { kind: 'report', text: 'கிண்டி பகுதியில் பலத்த மழை காரணமாக சாலைகளில் நீர் தேங்கியுள்ளது', language: 'ta', source_type: 'verified_news' }
    ],
    timestamp: new Date(Date.now() - 18 * 60 * 1000).toISOString()
  },
  {
    alert_id: 'ALT-2026-0905-003',
    type: 'power_outage',
    location: {
      lat: 12.9815,
      lng: 80.2180,
      name: 'Velachery Main Road, Chennai'
    },
    trust_score: 0.85,
    reasoning: '2 grid telemetry sensors (0V collapse) + 1 social report, trust score 0.85',
    contributing_signals: [
      { kind: 'sensor', sensor_id: 'GRID-TRANS-08', value: 0.0, unit: 'volts' },
      { kind: 'sensor', sensor_id: 'GRID-TRANS-09', value: 0.0, unit: 'volts' },
      { kind: 'report', text: 'வேளச்சேரியில் கடந்த 1 மணி நேரமாக மின்சாரம் துண்டிக்கப்பட்டுள்ளது', language: 'ta', source_type: 'social' }
    ],
    timestamp: new Date(Date.now() - 42 * 60 * 1000).toISOString()
  }
];

export const INITIAL_MOCK_HEALTH: SystemHealth = {
  connection_ok: true,
  last_airflow_run: new Date(Date.now() - 2 * 3600 * 1000).toISOString(),
  airflow_status: 'success',
  model_last_retrained: new Date(Date.now() - 14 * 3600 * 1000).toISOString(),
  active_model_weights: {
    verified_news: 0.9,
    social: 0.4,
    anonymous: 0.2,
    sensor: 0.85
  }
};

// Pre-scripted Demo Scenarios for Demo Control Panel
export const PRESET_SCENARIOS = {
  HIGH_TRUST_FLOODING: {
    name: "Scenario 1: High-Trust Flooding (Sensors + Multi-lingual Reports)",
    request: {
      type: 'flooding' as const,
      location: {
        lat: 13.0827,
        lng: 80.2707,
        name: 'T. Nagar Canal Zone, Chennai'
      },
      reports: [
        {
          text: "BREAKING: Canal embankment breached near Usman Road flyover. Floodwaters inundating shops.",
          language: "en" as const,
          source_type: "verified_news" as const
        },
        {
          text: "உஸ்மான் சாலையில் வெள்ள நீர் 3 அடி உயரத்தில் பாய்கிறது. வாகனங்கள் போக முடியாது!",
          language: "ta" as const,
          source_type: "social" as const
        },
        {
          text: "Water level rising very fast near bus depot.",
          language: "en" as const,
          source_type: "anonymous" as const
        }
      ],
      sensor_readings: [
        { sensor_id: "SENS-WATER-101", value: 4.9, unit: "meters" },
        { sensor_id: "SENS-WATER-102", value: 5.3, unit: "meters" }
      ]
    },
    expectedScore: 0.94,
    expectedReasoning: "2 water level sensors (5.3m) + 3 corroborating reports (Tamil news & social), trust score 0.94"
  },

  UNVERIFIED_BELOW_THRESHOLD: {
    name: "Scenario 2: Single Anonymous Report (Below Threshold - No Alert)",
    request: {
      type: 'waterlogging' as const,
      location: {
        lat: 13.0220,
        lng: 80.2240,
        name: 'Saidapet Bridge Area, Chennai'
      },
      reports: [
        {
          text: "Looks like water accumulating near subway entrance...",
          language: "en" as const,
          source_type: "anonymous" as const
        }
      ],
      sensor_readings: []
    },
    expectedScore: 0.20,
    expectedReasoning: "Below alert threshold (0.20 < 0.60) — No alert emitted by Spark."
  },

  SENSOR_ONLY_POWER_OUTAGE: {
    name: "Scenario 3: Sensor-Only Power Grid Failure",
    request: {
      type: 'power_outage' as const,
      location: {
        lat: 12.9815,
        lng: 80.2180,
        name: 'Velachery Substation Zone'
      },
      reports: [],
      sensor_readings: [
        { sensor_id: "GRID-TRANS-12", value: 0.0, unit: "volts" },
        { sensor_id: "GRID-TRANS-13", value: 0.0, unit: "volts" }
      ]
    },
    expectedScore: 0.85,
    expectedReasoning: "2 grid telemetry sensors (0V grid trip), trust score 0.85"
  }
};
