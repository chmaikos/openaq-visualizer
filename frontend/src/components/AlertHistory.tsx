import React, { useEffect, useState } from 'react';
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

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface Alert {
  id: string;
  location: {
    lat: number;
    lon: number;
  };
  pm25: number;
  severity: string;
  threshold: number;
  timestamp: string;
  acknowledged: boolean;
  description?: string;
}

interface DailyStats {
  date: string;
  avg_pm25: number;
  max_pm25: number;
  min_pm25: number;
  alert_count: number;
}

interface TrendData {
  dates: string[];
  values: number[];
}

interface AlertHistoryProps {
  lat: number;
  lon: number;
}

const API_BASE = import.meta.env.PROD ? 'http://localhost:8000/api' : '/api';

const AlertHistory: React.FC<AlertHistoryProps> = ({ lat, lon }) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [dailyStats, setDailyStats] = useState<DailyStats | null>(null);
  const [trendData, setTrendData] = useState<TrendData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch alert history
        const alertsRes = await fetch(
          `${API_BASE}/alerts/history?lat=${lat}&lon=${lon}`
        );
        if (!alertsRes.ok) throw new Error('Failed to fetch alerts');
        const alertsData = await alertsRes.json();
        setAlerts(alertsData);

        // Fetch daily stats
        const statsRes = await fetch(
          `${API_BASE}/analysis/daily?lat=${lat}&lon=${lon}`
        );
        if (!statsRes.ok) throw new Error('Failed to fetch daily stats');
        const statsData = await statsRes.json();
        setDailyStats(statsData);

        // Fetch trend data
        const trendRes = await fetch(
          `${API_BASE}/analysis/trends?lat=${lat}&lon=${lon}`
        );
        if (!trendRes.ok) throw new Error('Failed to fetch trend data');
        const trendData = await trendRes.json();
        setTrendData(trendData);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [lat, lon]);

  const handleAcknowledge = async (alertId: string) => {
    try {
      const res = await fetch(`${API_BASE}/alerts/${alertId}/acknowledge`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('Failed to acknowledge alert');
      
      // Update local state
      setAlerts(prevAlerts =>
        prevAlerts.map(alert =>
          alert.id === alertId ? { ...alert, acknowledged: true } : alert
        )
      );
    } catch (error) {
      console.error('Error acknowledging alert:', error);
    }
  };

  if (loading) {
    return <div>Loading alert history...</div>;
  }

  return (
    <div className="alert-history">
      {dailyStats && dailyStats.avg_pm25 !== undefined && (
        <div className="stats-summary">
          <h3>Daily Statistics</h3>
          <div className="stats-grid">
            <div className="stat-card">
              <h4>Average PM2.5</h4>
              <p>{dailyStats.avg_pm25?.toFixed(1) ?? 'N/A'} µg/m³</p>
            </div>
            <div className="stat-card">
              <h4>Maximum PM2.5</h4>
              <p>{dailyStats.max_pm25?.toFixed(1) ?? 'N/A'} µg/m³</p>
            </div>
            <div className="stat-card">
              <h4>Minimum PM2.5</h4>
              <p>{dailyStats.min_pm25?.toFixed(1) ?? 'N/A'} µg/m³</p>
            </div>
            <div className="stat-card">
              <h4>Alert Count</h4>
              <p>{dailyStats.alert_count ?? 0}</p>
            </div>
          </div>
        </div>
      )}

      {trendData && (
        <div className="trend-chart">
          <h3>PM2.5 Trend</h3>
          <Line
            data={{
              labels: trendData.dates,
              datasets: [
                {
                  label: 'PM2.5 (µg/m³)',
                  data: trendData.values,
                  borderColor: 'rgb(75, 192, 192)',
                  tension: 0.1,
                },
              ],
            }}
            options={{
              responsive: true,
              scales: {
                y: {
                  beginAtZero: true,
                  title: {
                    display: true,
                    text: 'PM2.5 (µg/m³)',
                  },
                },
                x: {
                  title: {
                    display: true,
                    text: 'Date',
                  },
                },
              },
            }}
          />
        </div>
      )}

      <div className="alerts-list">
        <h3>Recent Alerts</h3>
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>PM2.5</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map(alert => (
              <tr key={alert.id}>
                <td>{new Date(alert.timestamp).toLocaleString()}</td>
                <td>{alert.pm25.toFixed(1)} µg/m³</td>
                <td>{alert.severity.toUpperCase()}</td>
                <td>{alert.acknowledged ? 'Acknowledged' : 'New'}</td>
                <td>
                  {!alert.acknowledged && (
                    <button
                      className="acknowledge-btn"
                      onClick={() => handleAcknowledge(alert.id)}
                    >
                      Acknowledge
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AlertHistory; 