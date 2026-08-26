import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSettings, updateSettings, getTeam, getMyTeamMember } from '../services/api';
import { applyTheme } from '../utils/theme';
import '../styles/Settings.css';

const ROLE_LABELS = {
  admin: 'Admin',
  team_lead: 'Team Leader',
  location_head: 'Location Head',
  business_manager: 'Business Manager',
  employee: 'Employee'
};
const ROLE_ORDER = ['admin', 'team_lead', 'location_head', 'business_manager', 'employee'];

const defaultSettings = {
  fullName: '',
  email: '',
  phone: '',
  company: '',
  timezone: 'IST',
  theme: 'light',
  notifications: true,
  emailNotifications: true,
  smsNotifications: false,
  gaTrackingId: ''
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
  smsNotifications: s.sms_notifications,
  gaTrackingId: s.ga_tracking_id || ''
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
  sms_notifications: s.smsNotifications,
  ga_tracking_id: s.gaTrackingId
});

export default function Settings() {
  const [settings, setSettings] = useState(defaultSettings);
  const [savedSettings, setSavedSettings] = useState(defaultSettings);
  const [saved, setSaved] = useState(false);
  const [teamMembers, setTeamMembers] = useState([]);
  const [myTeamMember, setMyTeamMember] = useState(null);
  const [myTeamMemberLoaded, setMyTeamMemberLoaded] = useState(false);
  const token = localStorage.getItem('token');
  const isAdmin = (localStorage.getItem('role') || '').toLowerCase() === 'admin';
  const navigate = useNavigate();

  useEffect(() => {
    fetchSettings();
    if (isAdmin) fetchTeamMembers();
    fetchMyTeamMember();
  }, []);

  const fetchMyTeamMember = async () => {
    try {
      const data = await getMyTeamMember(token);
      setMyTeamMember(data || null);
    } catch (error) {
      console.error('Error fetching linked team roster entry:', error);
    } finally {
      setMyTeamMemberLoaded(true);
    }
  };

  const fetchTeamMembers = async () => {
    try {
      const data = await getTeam(token);
      setTeamMembers(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching team members:', error);
    }
  };

  const fetchSettings = async () => {
    try {
      const data = await getSettings(token);
      const mapped = fromApi(data);
      setSettings(mapped);
      setSavedSettings(mapped);
      // The backend's saved preference is authoritative once loaded - it may differ from
      // whatever localStorage had at app boot (e.g. changed from another session).
      applyTheme(mapped.theme);
    } catch (error) {
      console.error('Error fetching settings:', error);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    const nextValue = type === 'checkbox' ? checked : value;
    setSettings({
      ...settings,
      [name]: nextValue
    });
    setSaved(false);
    // Live preview: apply immediately, not just on Save. Cancel Changes reverts it below.
    if (name === 'theme') applyTheme(nextValue);
  };

  const handleSave = async () => {
    try {
      const data = await updateSettings(token, toApi(settings));
      const mapped = fromApi(data);
      setSettings(mapped);
      setSavedSettings(mapped);
      applyTheme(mapped.theme);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
      // Saving Profile Information may have just synced the linked roster entry's
      // name/email/phone server-side - refresh so the "linked as" line reflects it.
      fetchMyTeamMember();
    } catch (error) {
      console.error('Error saving settings:', error);
      alert('Failed to save settings. Please try again.');
    }
  };

  const handleCancel = () => {
    setSettings(savedSettings);
    applyTheme(savedSettings.theme);
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
          {myTeamMemberLoaded && (
            myTeamMember ? (
              <p className="settings-section-hint settings-roster-link">
                🔗 Linked to the team roster as <strong>{myTeamMember.name}</strong> ({ROLE_LABELS[myTeamMember.role] || myTeamMember.role}).
                Saving here keeps that roster entry's name/email/phone in sync automatically.
              </p>
            ) : (
              <p className="settings-section-hint">
                Not yet listed on the team roster{isAdmin ? ' - add yourself from the Team page to appear in Reports and assignment dropdowns.' : ' - ask an Admin to add you to the team roster.'}
              </p>
            )
          )}
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

          <div className="form-group">
            <label>Google Analytics Tracking ID</label>
            <input
              type="text"
              name="gaTrackingId"
              value={settings.gaTrackingId}
              onChange={handleChange}
              placeholder="G-XXXXXXXXXX"
            />
          </div>
        </div>

        {isAdmin && (
          <div className="settings-section">
            <h2>Team &amp; Access</h2>
            <p className="settings-section-hint">
              Only Admin can add, edit, or remove team members - here's a quick summary of who's on the roster.
            </p>
            {teamMembers.length === 0 ? (
              <p className="settings-section-hint">No team members yet.</p>
            ) : (
              <div className="team-role-summary">
                {ROLE_ORDER.map((role) => {
                  const people = teamMembers.filter((m) => m.role === role);
                  return (
                    <div key={role} className="team-role-summary-row">
                      <span className="team-role-summary-label">{ROLE_LABELS[role]}</span>
                      <span className="team-role-summary-count">{people.length}</span>
                      <span className="team-role-summary-names">
                        {people.length > 0 ? people.map((p) => p.name).join(', ') : '—'}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
            <button type="button" className="btn-secondary team-manage-btn" onClick={() => navigate('/team')}>
              🧑‍🤝‍🧑 Manage Team →
            </button>
          </div>
        )}

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
