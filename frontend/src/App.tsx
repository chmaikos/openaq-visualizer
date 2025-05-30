import React, { useEffect, useState } from 'react';
interface Alert { city: string; location: string; parameter: string; value: number; timestamp: string; }

function App() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/alerts');
    ws.onmessage = (e) => {
      const alert: Alert = JSON.parse(e.data);
      setAlerts(prev => [alert, ...prev].slice(0, 20));
    };
    return () => ws.close();
  }, []);

  return (
    <div className="p-4 font-sans">
      <h1 className="text-2xl mb-4">Live Air Quality Alerts</h1>
      <ul>
        {alerts.map((a,i) => (
          <li key={i} className="mb-2">
            <strong>{a.city} - {a.location}</strong>: {a.parameter} = {a.value} at {a.timestamp}
          </li>
        ))}
      </ul>
    </div>
  );
}
export default App;