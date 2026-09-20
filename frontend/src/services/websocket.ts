import { CONFIG } from '../config';
import { Alert } from '../types';
import { INITIAL_MOCK_ALERTS } from './mockData';

type AlertListener = (alert: Alert) => void;
type ConnectionListener = (connected: boolean) => void;

class AlertWebSocketService {
  private socket: WebSocket | null = null;
  private alertListeners: Set<AlertListener> = new Set();
  private connectionListeners: Set<ConnectionListener> = new Set();
  private isConnected: boolean = false;
  private reconnectTimer: any = null;

  constructor() {
    if (CONFIG.USE_MOCK_DATA) {
      // Mock mode: set connected to true
      setTimeout(() => this.setConnected(true), 300);
    } else {
      this.connect();
    }
  }

  public subscribeAlerts(listener: AlertListener): () => void {
    this.alertListeners.add(listener);
    return () => this.alertListeners.delete(listener);
  }

  public subscribeConnection(listener: ConnectionListener): () => void {
    this.connectionListeners.add(listener);
    // Emit current state immediately
    listener(this.isConnected);
    return () => this.connectionListeners.delete(listener);
  }

  private setConnected(connected: boolean) {
    this.isConnected = connected;
    this.connectionListeners.forEach(fn => fn(connected));
  }

  private connect() {
    if (CONFIG.USE_MOCK_DATA) return;

    try {
      this.socket = new WebSocket(CONFIG.WS_URL);

      this.socket.onopen = () => {
        console.log('[WS] Connected to Civic Alerts stream.');
        this.setConnected(true);
        if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
      };

      this.socket.onmessage = (event) => {
        try {
          const alert: Alert = JSON.parse(event.data);
          this.alertListeners.forEach(fn => fn(alert));
        } catch (e) {
          console.error('[WS] Error parsing message:', e);
        }
      };

      this.socket.onclose = () => {
        console.warn('[WS] Connection closed. Attempting reconnect in 3s...');
        this.setConnected(false);
        this.reconnectTimer = setTimeout(() => this.connect(), 3000);
      };

      this.socket.onerror = (err) => {
        console.error('[WS] Error:', err);
        this.socket?.close();
      };
    } catch (e) {
      console.error('[WS] Connection exception:', e);
      this.setConnected(false);
      this.reconnectTimer = setTimeout(() => this.connect(), 3000);
    }
  }

  // Method to inject synthetic alert locally (for mock scenarios or simulation button)
  public emitMockAlert(alert: Alert) {
    this.alertListeners.forEach(fn => fn(alert));
  }
}

export const wsService = new AlertWebSocketService();
