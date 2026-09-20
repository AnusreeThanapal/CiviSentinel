import { CONFIG } from '../config';
import { Alert, SystemHealth, SimulationRequest } from '../types';
import { INITIAL_MOCK_ALERTS, INITIAL_MOCK_HEALTH } from './mockData';

export async function fetchAlerts(limit: number = 50, type?: string): Promise<Alert[]> {
  if (CONFIG.USE_MOCK_DATA) {
    let list = [...INITIAL_MOCK_ALERTS];
    if (type) {
      list = list.filter(a => a.type === type);
    }
    return list.slice(0, limit);
  }

  const url = new URL(`${CONFIG.API_BASE_URL}/alerts`, window.location.origin);
  url.searchParams.append('limit', limit.toString());
  if (type) url.searchParams.append('type', type);

  const res = await fetch(url.toString());
  if (!res.ok) {
    throw new Error(`Failed to fetch alerts: ${res.statusText}`);
  }
  return res.json();
}

export async function triggerSimulation(payload: SimulationRequest): Promise<{ status: string; message: string }> {
  if (CONFIG.USE_MOCK_DATA) {
    // Return mock response immediately for local demo
    return {
      status: 'SUCCESS',
      message: `Injected simulation payload into mock pipeline.`
    };
  }

  const res = await fetch(`${CONFIG.API_BASE_URL}/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      scenario_name: `Simulation - ${payload.type}`,
      sensor_events: payload.sensor_readings.map(s => ({
        sensor_id: s.sensor_id,
        sensor_type: payload.type === 'power_outage' ? 'power_grid' : 'water_level',
        value: s.value,
        unit: s.unit,
        lat: payload.location.lat,
        lng: payload.location.lng,
        location_name: payload.location.name,
        event_time: new Date().toISOString()
      })),
      citizen_reports: payload.reports.map((r, idx) => ({
        report_id: `REP-SIM-${Date.now()}-${idx}`,
        text: r.text,
        language: r.language,
        source_type: r.source_type,
        lat: payload.location.lat,
        lng: payload.location.lng,
        location_name: payload.location.name,
        event_time: new Date().toISOString()
      }))
    })
  });

  if (!res.ok) {
    throw new Error(`Failed to trigger simulation: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchSystemHealth(): Promise<SystemHealth> {
  if (CONFIG.USE_MOCK_DATA) {
    return INITIAL_MOCK_HEALTH;
  }

  const res = await fetch(`${CONFIG.API_BASE_URL}/system-health`);
  if (!res.ok) {
    return {
      connection_ok: false,
      last_airflow_run: new Date().toISOString(),
      airflow_status: 'failed',
      model_last_retrained: new Date().toISOString()
    };
  }
  const data = await res.json();
  return {
    connection_ok: true,
    last_airflow_run: data.model_last_retrained || new Date().toISOString(),
    airflow_status: data.dag_status === 'SUCCESS' ? 'success' : 'failed',
    model_last_retrained: data.model_last_retrained || new Date().toISOString(),
    active_model_weights: data.active_model_weights
  };
}
