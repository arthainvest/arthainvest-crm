import React, { useState, useEffect } from 'react';
import { getSettings, updateSettings } from '../services/api';
import '../styles/Settings.css';

const defaultSettings = {
  fullName: '',
  email: '',
  phone: '',
  company: '',
  timezone: 'IST',
  theme: 'light',
  notifications: true,
  emailNotifications: true,
  smsNotifications: false
};

const fromApi = (s) => ({
  fullName: s.full_name || '',
  email: s.email || '',
  phone: s.phone || '',
  company: s.company || '',
  timezone: s.timezone,
  theme: s.theme,
  notifications: s.notifications,
  emailNotifications: s.email_notifications,
  smsNotifications: s.sms_notifications
});

const toApi = (s) => ({
  full_name: s.fullName,
  email: s.email,
  phone: s.phone,
  company: s.company,
  timezone: s.timezone,
  theme: s.theme,
  notifications: s.notifications,
  email_notifications: s.emailNotifications,
  sms_notifications: s.smsNotifications
});

export default function Settings() {
  const [settings, setSettings] = useState(defaultSettings);
  const [savedSettings, setSavedSettings] = useState(defaultSettings);
  const [saved, setSaved] = useState(false);
  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const data = await getSettings(token);
      const mapped = fromApi(data);
      setSettings(mapped);
      setSavedSettings(mapped);
    } catch (error) {
      console.error('Error fetching settings:', error);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSettings({
      ...settings,
      [name]: type === 'checkbox' ? checked : value
    });
    setSaved(false);
  };

  const handleSave = async () => {
    try {
      const data = await updateSettings(token, toApi(settings));
      const mapped = fromApi(data);
      setSettings(mapped);
      setSavedSettings(mapped);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error('Error saving settings:', error);
      alert('Failed to save settings. Please try again.');
    }
  };

  const handleCancel = () => {
    setSettings(savedSettings);
    setSaved(false);
  };

  return (
    <div className="settings-container">
      <div className="settings-header">
        <h1>Settings</h1>
        <p>Manage your account and preferences</p>
      </div>

      <div className="settings-content">
        <div className="settings-section">
          <h2>Profile Information</h2>
          <div className="form-group">
            <label>Full Name</label>
            <input
              type="text"
              name="fullName"
              value={settings.fullName}
              onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label>Email Address</label>
            <input
              type="email"
              name="email"
              value={settings.email}
              onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label>Phone Number</label>
            <input
              type="tel"
              name="phone"
              value={settings.phone}
              onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label>Company</label>
            <input
              type="text"
              name="company"
              value={settings.company}
              onChange={handleChange}
              placeholder="Your company name"
            />
          </div>
        </div>

        <div className="settings-section">
          <h2>Preferences</h2>
          <div className="form-group">
            <label>Timezone</label>
            <select name="timezone" value={settings.timezone} onChange={handleChange}>
              <option value="IST">IST (India Standard Time)</option>
              <option value="UTC">UTC</option>
              <option value="EST">EST</option>
              <option value="PST">PST</option>
            </select>
          </div>

          <div className="form-group">
            <label>Theme</label>
            <select name="theme" value={settings.theme} onChange={handleChange}>
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="auto">Auto</option>
            </select>
          </div>
        </div>

        <div className="settings-section">
          <h2>Notifications</h2>
          <div className="checkbox-group">
            <label>
              <input
                type="checkbox"
                name="notifications"
                checked={settings.notifications}
                onChange={handleChange}
              />
              Enable all notifications
            </label>
          </div>

          <div className="checkbox-group">
            <label>
              <input
                type="checkbox"
                name="emailNotifications"
                checked={settings.emailNotifications}
                onChange={handleChange}
              />
              Email notifications
            </label>
          </div>

          <div className="checkbox-group">
            <label>
              <input
                type="checkbox"
                name="smsNotifications"
                checked={settings.smsNotifications}
                onChange={handleChange}
              />
              SMS notifications
            </label>
          </div>
        </div>

        <div className="settings-actions">
          <button className="btn-primary" onClick={handleSave}>
            💾 Save Settings
          </button>
          <button className="btn-secondary" onClick={handleCancel}>Cancel Changes</button>
          {saved && <span className="save-message">✓ Settings saved!</span>}
        </div>
      </div>
    </div>
  );
}
