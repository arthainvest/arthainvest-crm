import React, { useState, useEffect } from 'react';
import '../styles/Settings.css';

export default function Settings() {
  const [settings, setSettings] = useState({
    fullName: 'Test User',
    email: 'testuser@example.com',
    phone: '+91-9876543210',
    company: '',
    timezone: 'IST',
    theme: 'light',
    notifications: true,
    emailNotifications: true,
    smsNotifications: false
  });

  const [saved, setSaved] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSettings({
      ...settings,
      [name]: type === 'checkbox' ? checked : value
    });
    setSaved(false);
  };

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
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
              <option>IST (India Standard Time)</option>
              <option>UTC</option>
              <option>EST</option>
              <option>PST</option>
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
          <button className="btn-secondary">Cancel Changes</button>
          {saved && <span className="save-message">✓ Settings saved!</span>}
        </div>
      </div>
    </div>
  );
}
