-- Postgres Initialization Script for Real-Time Civic Disruption Early-Warning System

CREATE TABLE IF NOT EXISTS trust_weights (
    key TEXT PRIMARY KEY,
    value DOUBLE PRECISION NOT NULL
);

-- Seed trust_weights default values
INSERT INTO trust_weights (key, value) VALUES
    ('verified_news', 0.9),
    ('social', 0.4),
    ('anonymous', 0.2),
    ('sensor', 0.85)
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

CREATE TABLE IF NOT EXISTS alerts (
    alert_id VARCHAR(128) PRIMARY KEY,
    type VARCHAR(64) NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lng DOUBLE PRECISION NOT NULL,
    location_name VARCHAR(256),
    trust_score DOUBLE PRECISION NOT NULL,
    reasoning TEXT,
    contributing_signals JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw_events (
    id SERIAL PRIMARY KEY,
    kind VARCHAR(64) NOT NULL,
    payload JSONB NOT NULL,
    event_time TIMESTAMP WITH TIME ZONE NOT NULL,
    processed_flag BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS data_quality_reports (
    id SERIAL PRIMARY KEY,
    run_date DATE NOT NULL,
    summary JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_versions (
    id SERIAL PRIMARY KEY,
    trained_at TIMESTAMP WITH TIME ZONE NOT NULL,
    weights JSONB NOT NULL,
    metrics JSONB NOT NULL,
    is_active BOOLEAN DEFAULT false
);

-- Seed initial active model version
INSERT INTO model_versions (trained_at, weights, metrics, is_active)
VALUES (
    CURRENT_TIMESTAMP,
    '{"verified_news": 0.9, "social": 0.4, "anonymous": 0.2, "sensor": 0.85}'::jsonb,
    '{"initial_baseline": true, "f1_score": 0.92}'::jsonb,
    true
);

CREATE TABLE IF NOT EXISTS system_health (
    id SERIAL PRIMARY KEY,
    run_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    dag_status VARCHAR(64) NOT NULL,
    model_last_retrained TIMESTAMP WITH TIME ZONE
);
