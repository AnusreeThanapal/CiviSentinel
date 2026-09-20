export type DisruptionType = 'flooding' | 'waterlogging' | 'power_outage';
export type Language = 'ta' | 'en';
export type SourceType = 'verified_news' | 'social' | 'anonymous';
export type SignalKind = 'sensor' | 'report';

export interface LocationInfo {
  lat: number;
  lng: number;
  name: string;
}

export interface SensorSignal {
  kind: 'sensor';
  sensor_id: string;
  value: number;
  unit: string;
}

export interface ReportSignal {
  kind: 'report';
  text: string;
  language: Language;
  source_type: SourceType;
}

export type ContributingSignal = SensorSignal | ReportSignal;

export interface Alert {
  alert_id: string;
  type: DisruptionType;
  location: LocationInfo;
  trust_score: number;
  reasoning: string;
  contributing_signals: ContributingSignal[];
  timestamp: string;
  is_backlog?: boolean;
}

export interface SimulationRequest {
  type: DisruptionType;
  location: LocationInfo;
  reports: Array<{
    text: string;
    language: Language;
    source_type: SourceType;
  }>;
  sensor_readings: Array<{
    sensor_id: string;
    value: number;
    unit: string;
  }>;
}

export interface SystemHealth {
  connection_ok: boolean;
  last_airflow_run: string;
  airflow_status: 'success' | 'failed' | 'running';
  model_last_retrained: string;
  active_model_weights?: Record<string, number>;
}

export type PipelineStage = 'idle' | 'ingesting' | 'correlating' | 'raised' | 'filtered';
