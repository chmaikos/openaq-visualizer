import React, { useEffect, useState } from 'react';

interface AlertPreference {
  severity_levels: string[];
  location_filter?: Array<{
    lat: number;
    lon: number;
    radius: number;
  }>;
  min_threshold?: number;
  max_threshold?: number;
  notification_channels: string[];
}

interface UserPreferences {
  user_id: string;
  email?: string;
  alert_preferences: AlertPreference;
  created_at: string;
  updated_at: string;
}

const severityOptions = ['info', 'warning', 'alert', 'critical'];
const notificationChannels = ['web', 'email', 'sms'];

const defaultPreferences: AlertPreference = {
  severity_levels: ['warning', 'alert', 'critical'],
  notification_channels: ['web'],
  min_threshold: 10,
  max_threshold: 50,
};

const API_BASE = import.meta.env.PROD ? 'http://localhost:8000/api' : '/api';

const UserPreferences: React.FC = () => {
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const fetchPreferences = async () => {
      try {
        const res = await fetch(`${API_BASE}/preferences/current_user`);
        if (!res.ok) {
          throw new Error('Failed to fetch preferences');
        }
        const data = await res.json();
        setPreferences(data);
      } catch (error) {
        console.error('Error fetching preferences:', error);
        // Set default preferences if fetch fails
        setPreferences({
          user_id: 'current_user',
          alert_preferences: defaultPreferences,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        });
      } finally {
        setLoading(false);
      }
    };

    fetchPreferences();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!preferences) return;

    setSaving(true);
    try {
      const res = await fetch(`${API_BASE}/preferences/current_user`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: preferences.user_id,
          alert_preferences: preferences.alert_preferences
        }),
      });
      
      if (!res.ok) {
        throw new Error('Failed to save preferences');
      }
      
      const updatedData = await res.json();
      if (updatedData.status === 'success') {
        // Fetch the updated preferences
        const getRes = await fetch(`${API_BASE}/preferences/current_user`);
        if (!getRes.ok) {
          throw new Error('Failed to fetch updated preferences');
        }
        const updatedPreferences = await getRes.json();
        setPreferences(updatedPreferences);
      }
    } catch (error) {
      console.error('Error saving preferences:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleSeverityChange = (severity: string) => {
    if (!preferences) return;

    const newSeverities = preferences.alert_preferences.severity_levels.includes(severity)
      ? preferences.alert_preferences.severity_levels.filter(s => s !== severity)
      : [...preferences.alert_preferences.severity_levels, severity];

    setPreferences({
      ...preferences,
      alert_preferences: {
        ...preferences.alert_preferences,
        severity_levels: newSeverities,
      },
    });
  };

  const handleChannelChange = (channel: string) => {
    if (!preferences) return;

    const newChannels = preferences.alert_preferences.notification_channels.includes(channel)
      ? preferences.alert_preferences.notification_channels.filter(c => c !== channel)
      : [...preferences.alert_preferences.notification_channels, channel];

    setPreferences({
      ...preferences,
      alert_preferences: {
        ...preferences.alert_preferences,
        notification_channels: newChannels,
      },
    });
  };

  if (loading) {
    return <div>Loading preferences...</div>;
  }

  if (!preferences) {
    return <div>No preferences found</div>;
  }

  return (
    <div className="user-preferences">
      <h2>Alert Preferences</h2>
      <form onSubmit={handleSubmit}>
        <div className="preference-section">
          <h3>Severity Levels</h3>
          <div className="checkbox-group">
            {severityOptions.map(severity => (
              <label key={severity} className="checkbox-item">
                <input
                  type="checkbox"
                  checked={preferences.alert_preferences.severity_levels.includes(severity)}
                  onChange={() => handleSeverityChange(severity)}
                />
                {severity.charAt(0).toUpperCase() + severity.slice(1)}
              </label>
            ))}
          </div>
        </div>

        <div className="preference-section">
          <h3>Notification Channels</h3>
          <div className="checkbox-group">
            {notificationChannels.map(channel => (
              <label key={channel} className="checkbox-item">
                <input
                  type="checkbox"
                  checked={preferences.alert_preferences.notification_channels.includes(channel)}
                  onChange={() => handleChannelChange(channel)}
                />
                {channel.toUpperCase()}
              </label>
            ))}
          </div>
        </div>

        <div className="preference-section">
          <h3>Thresholds</h3>
          <div className="threshold-inputs">
            <label>
              Minimum PM2.5:
              <input
                type="number"
                value={preferences.alert_preferences.min_threshold || ''}
                onChange={e => setPreferences({
                  ...preferences,
                  alert_preferences: {
                    ...preferences.alert_preferences,
                    min_threshold: e.target.value ? parseFloat(e.target.value) : undefined,
                  },
                })}
              />
              µg/m³
            </label>
            <label>
              Maximum PM2.5:
              <input
                type="number"
                value={preferences.alert_preferences.max_threshold || ''}
                onChange={e => setPreferences({
                  ...preferences,
                  alert_preferences: {
                    ...preferences.alert_preferences,
                    max_threshold: e.target.value ? parseFloat(e.target.value) : undefined,
                  },
                })}
              />
              µg/m³
            </label>
          </div>
        </div>

        <button type="submit" className="submit-btn" disabled={saving}>
          {saving ? 'Saving...' : 'Save Preferences'}
        </button>
      </form>
    </div>
  );
};

export default UserPreferences; 