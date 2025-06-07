// frontend/src/App.tsx
import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

// Import MQTT client
import mqtt from "mqtt";

import AlertHistory from './components/AlertHistory';
import UserPreferences from './components/UserPreferences';

import "leaflet/dist/leaflet.css";
import "./App.css";

// Fix Leaflet default icon issue
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface AQPoint {
  lat: number;
  lon: number;
  pm25: number;
  unit?: string;
  timestamp: string | null;
  severity?: string;
  threshold?: number;
  description?: string;
}

const severityColors = {
  info: "#3498db",     // Blue
  warning: "#f1c40f",  // Yellow
  alert: "#e67e22",    // Orange
  critical: "#e74c3c", // Red
} as const;

type SeverityLevel = keyof typeof severityColors;

function App() {
  const [data, setData] = useState<AQPoint[]>([]);
  const [client, setClient] = useState<mqtt.MqttClient | null>(null);
  const [selectedPoint, setSelectedPoint] = useState<AQPoint | null>(null);
  const [showPreferences, setShowPreferences] = useState(false);
  const [isMapReady, setIsMapReady] = useState(false);

  useEffect(() => {
    // Get MQTT broker WebSocket URL from env
    const wsUrl = import.meta.env.VITE_MQTT_WS_URL ?? "ws://localhost:9001";

    // Connect to broker via WebSocket
    const mqttClient = mqtt.connect(wsUrl);

    mqttClient.on("connect", () => {
      console.log("[MQTT] Connected to broker via WebSocket:", wsUrl);
      // Subscribe to "alerts" topic
      mqttClient.subscribe("alerts", { qos: 0 }, (err) => {
        if (err) {
          console.error("[MQTT] Subscribe error:", err);
        }
      });
    });

    mqttClient.on("message", (topic: string, message: Buffer) => {
      try {
        const payload = JSON.parse(message.toString()) as AQPoint;
        const lat = payload.lat;
        const lon = payload.lon;
        const pm25 = payload.pm25;
        const unit = payload.unit;
        const timestamp = payload.timestamp;
        const severity = payload.severity;
        const threshold = payload.threshold;
        const description = payload.description;

        setData((prev: AQPoint[]) => {
          // If marker with this lat/lon exists, update it
          const idx = prev.findIndex(
            (pt) => pt.lat === lat && pt.lon === lon
          );
          if (idx >= 0) {
            const updated = [...prev];
            updated[idx] = { lat, lon, pm25, unit, timestamp, severity, threshold, description };
            return updated;
          } else {
            // Add new point
            return [...prev, { lat, lon, pm25, unit, timestamp, severity, threshold, description }];
          }
        });
      } catch (err) {
        console.error("[MQTT] Parse error:", err);
      }
    });

    mqttClient.on("error", (err) => {
      console.error("[MQTT] Error:", err);
    });

    setClient(mqttClient);

    return () => {
      mqttClient.end(true);
    };
  }, []);

  // Triangular icon factory, based on PM2.5 value and severity
  const iconFor = (point: AQPoint) => {
    const color = point.severity && point.severity in severityColors
      ? severityColors[point.severity as SeverityLevel]
      : `rgb(${Math.floor(255 * Math.min(1, point.pm25 / 50))},${Math.floor(255 * (1 - Math.min(1, point.pm25 / 50)))},0)`;
    
    return L.divIcon({
      html: `<svg width="24" height="24" viewBox="0 0 10 10">
               <path d="M5 0 L10 10 L0 10 Z" fill="${color}" />
             </svg>`,
      className: "",
      iconSize: [24, 24],
      iconAnchor: [12, 12],
      popupAnchor: [0, -12],
    });
  };

  return (
    <div className="app-container">
      <div className="map-container">
        <MapContainer 
          center={[20, 0]} 
          zoom={2} 
          className="map"
          whenReady={() => setIsMapReady(true)}
        >
          <TileLayer 
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          {data.map((pt) => (
            <Marker
              key={`${pt.lat}-${pt.lon}`}
              position={[pt.lat, pt.lon]}
              icon={iconFor(pt)}
              eventHandlers={{
                click: () => setSelectedPoint(pt)
              }}
            >
              <Popup>
                {pt.severity && (
                  <>
                    <strong>Severity: {pt.severity.toUpperCase()}</strong>
                    <br />
                  </>
                )}
                PM2.5: {pt.pm25.toFixed(1)} {pt.unit || "µg/m³"}
                {pt.threshold && (
                  <>
                    <br />
                    Threshold: {pt.threshold} {pt.unit || "µg/m³"}
                  </>
                )}
                {pt.description && (
                  <>
                    <br />
                    {pt.description}
                  </>
                )}
                <br />
                {pt.timestamp
                  ? new Date(pt.timestamp).toLocaleString()
                  : "—"}
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>

      <div className="controls">
        <button
          className="preferences-btn"
          onClick={() => setShowPreferences(!showPreferences)}
        >
          {showPreferences ? "Hide Preferences" : "Show Preferences"}
        </button>
      </div>

      {showPreferences && (
        <div className="preferences-panel">
          <UserPreferences />
        </div>
      )}

      {selectedPoint && (
        <div className="details-panel">
          <button
            className="close-btn"
            onClick={() => setSelectedPoint(null)}
          >
            ×
          </button>
          <AlertHistory
            lat={selectedPoint.lat}
            lon={selectedPoint.lon}
          />
        </div>
      )}
    </div>
  );
}

export default App;
