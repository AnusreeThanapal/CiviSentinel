import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Alert } from '../types';
import { CONFIG } from '../config';

interface LiveMapProps {
  alerts: Alert[];
  selectedAlert: Alert | null;
  onSelectAlert: (alert: Alert) => void;
}

// Custom Leaflet DivIcon generator with radar-ping concentric rings
function createRadarIcon(score: number, isSelected: boolean) {
  let colorClass = 'bg-sev-cyan border-sev-cyan text-sev-cyan';
  let ringClass = 'border-sev-cyan';
  let shadowGlow = '0 0 15px rgba(0, 242, 254, 0.6)';

  if (score >= 0.7) {
    colorClass = 'bg-sev-red border-sev-red text-sev-red';
    ringClass = 'border-sev-red';
    shadowGlow = '0 0 20px rgba(255, 51, 102, 0.8)';
  } else if (score >= 0.4) {
    colorClass = 'bg-sev-amber border-sev-amber text-sev-amber';
    ringClass = 'border-sev-amber';
    shadowGlow = '0 0 15px rgba(255, 184, 0, 0.7)';
  }

  const selectedRing = isSelected
    ? `<div class="absolute -inset-3 rounded-full border-2 ${ringClass} animate-ping"></div>`
    : '';

  const html = `
    <div class="relative flex items-center justify-center">
      ${selectedRing}
      <!-- Radar Pulsing Outer Ring -->
      <div class="radar-ring absolute w-10 h-10 rounded-full border-2 ${ringClass} opacity-75"></div>
      <!-- Center Core Marker -->
      <div class="relative w-5 h-5 rounded-full ${colorClass} border-2 border-slate-900 shadow-lg flex items-center justify-center" style="box-shadow: ${shadowGlow};">
        <div class="w-1.5 h-1.5 rounded-full bg-slate-900"></div>
      </div>
    </div>
  `;

  return L.divIcon({
    html: html,
    className: 'custom-radar-marker',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  });
}

// Controller component to pan map smoothly when an alert is selected
function MapRecenter({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo(center, 14, { duration: 1.2 });
  }, [center, map]);
  return null;
}

export const LiveMap: React.FC<LiveMapProps> = ({
  alerts,
  selectedAlert,
  onSelectAlert
}) => {
  const mapCenter: [number, number] = selectedAlert
    ? [selectedAlert.location.lat, selectedAlert.location.lng]
    : [CONFIG.MAP_CENTER.lat, CONFIG.MAP_CENTER.lng];

  return (
    <div className="relative w-full h-full">
      <MapContainer
        center={mapCenter}
        zoom={CONFIG.MAP_CENTER.zoom}
        zoomControl={false}
        className="w-full h-full z-0"
      >
        {/* Base Map Tiles: Use CARTO Dark Matter if key configured, otherwise dark-styled OSM */}
        {CONFIG.CARTO_API_KEY ? (
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
            url={`https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png?key=${CONFIG.CARTO_API_KEY}`}
            maxZoom={19}
          />
        ) : (
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            className="dark-tiles"
            maxZoom={19}
          />
        )}

        <MapRecenter center={mapCenter} />

        {/* Render Alert Radar Markers */}
        {alerts.map((alert) => {
          const isSelected = selectedAlert?.alert_id === alert.alert_id;
          const icon = createRadarIcon(alert.trust_score, isSelected);

          return (
            <Marker
              key={alert.alert_id}
              position={[alert.location.lat, alert.location.lng]}
              icon={icon}
              eventHandlers={{
                click: () => onSelectAlert(alert)
              }}
            >
              <Popup className="custom-popup" closeButton={false}>
                <div className="p-2 text-slate-100 font-mono text-xs space-y-1">
                  <div className="font-bold text-ops-accent uppercase tracking-wider">{alert.type}</div>
                  <div className="text-slate-300 font-sans">{alert.location.name}</div>
                  <div className="flex items-center space-x-2 pt-1">
                    <span className="text-slate-400">Trust:</span>
                    <span className="font-bold text-sev-amber">{alert.trust_score.toFixed(2)}</span>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
};
