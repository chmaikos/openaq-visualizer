// frontend/src/App.tsx
import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";

// Import της browser‐έκδοσης του MQTT client
import mqtt, { MqttClient } from "mqtt/dist/mqtt.js";

import "leaflet/dist/leaflet.css";
import "./App.css";

interface AQPoint {
  lat:       number;
  lon:       number;
  pm25:      number;
  unit?:     string;
  timestamp: string | null;
}

function App() {
  const [data, setData] = useState<AQPoint[]>([]);
  const [client, setClient] = useState<MqttClient | null>(null);

  useEffect(() => {
    // Διαβάζουμε URL MQTT broker‐over‐WebSocket από το env
    const wsUrl = import.meta.env.VITE_MQTT_WS_URL ?? "ws://localhost:9001";

    // Συνδεόμαστε στο broker μέσω WebSocket
    const mqttClient = mqtt.connect(wsUrl);

    mqttClient.on("connect", () => {
      console.log("[MQTT] Connected to broker via WebSocket:", wsUrl);
      // Subscribe στο topic "alerts"
      mqttClient.subscribe("alerts", { qos: 0 }, (err) => {
        if (err) {
          console.error("[MQTT] Subscribe error:", err);
        }
      });
    });

    mqttClient.on("message", (_, messageBuffer) => {
      try {
        const payload = JSON.parse(messageBuffer.toString()) as any;
        const lat = payload.lat;
        const lon = payload.lon;
        const pm25 = payload.pm25;
        const unit = payload.unit;
        const timestamp = payload.timestamp;

        setData((prev) => {
          // Αν υπάρχει ήδη marker με αυτό το lat/lon, κάνουμε update
          const idx = prev.findIndex(
            (pt) => pt.lat === lat && pt.lon === lon
          );
          if (idx >= 0) {
            const updated = [...prev];
            updated[idx] = { lat, lon, pm25, unit, timestamp };
            return updated;
          } else {
            // Προσθέτουμε νέο σημείο
            return [...prev, { lat, lon, pm25, unit, timestamp }];
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

  // Triangular icon factory, ανά PM2.5 value
  const iconFor = (val: number) => {
    const t = Math.min(1, val / 50);
    const color = `rgb(${Math.floor(255 * t)},${Math.floor(255 * (1 - t))},0)`;
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
    <MapContainer center={[20, 0]} zoom={2} className="map">
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {data.map((pt, idx) => (
        <Marker
          key={`${pt.lat}-${pt.lon}`}
          position={[pt.lat, pt.lon]}
          icon={iconFor(pt.pm25)}
        >
          <Popup>
            PM2.5: {pt.pm25.toFixed(1)} {pt.unit || "µg/m³"}
            <br />
            {pt.timestamp
              ? new Date(pt.timestamp).toLocaleString()
              : "—"}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}

export default App;
