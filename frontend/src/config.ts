// Global Application Configuration

export const CONFIG = {
  // Flag controlling whether to use pre-scripted mock scenarios (true) or real backend (false)
  USE_MOCK_DATA: false,

  // Backend API base URL
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || '/api',

  // Backend WebSocket URL
  WS_URL: import.meta.env.VITE_WS_URL || (
    window.location.protocol === 'https:'
      ? `wss://${window.location.host}/ws/alerts`
      : `ws://${window.location.host}/ws/alerts`
  ),

  // Map Default Center (Chennai, India)
  MAP_CENTER: {
    lat: 13.0827,
    lng: 80.2707,
    zoom: 13
  },

  // Trust Score Thresholds
  THRESHOLDS: {
    HIGH: 0.7,
    MEDIUM: 0.4
  }
};
