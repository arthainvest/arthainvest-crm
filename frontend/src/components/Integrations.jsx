import React, { useState, useEffect } from 'react';
import '../styles/Integrations.css';

export default function Integrations() {
  const [integrations, setIntegrations] = useState([]);

  useEffect(() => {
    setIntegrations(mockIntegrations);
  }, []);

  const toggleIntegration = (id) => {
    setIntegrations(integrations.map(int =>
      int.id === id
        ? { ...int, connected: !int.connected, lastSync: !int.connected ? 'now' : 'never' }
        : int
    ));
  };

  return (
    <div className="integrations-container">
      <div className="integrations-header">
        <h1>Integrations</h1>
        <button className="btn-primary">+ Add Integration</button>
      </div>

      <p className="integrations-subtitle">Connect your favorite tools to ArthaInvest CRM</p>

      <div className="integrations-grid">
        {integrations.map(integration => (
          <div key={integration.id} className="integration-card">
            <div className="integration-header">
              <div className="integration-logo">{integration.logo}</div>
              <h3>{integration.name}</h3>
            </div>

            <p className="integration-description">{integration.description}</p>

            <div className="integration-status">
              <div className={`status-indicator ${integration.connected ? 'connected' : 'disconnected'}`}></div>
              <span className={`status-text ${integration.connected ? 'connected' : 'disconnected'}`}>
                {integration.connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>

            {integration.connected && (
              <p className="last-sync">Last sync: {integration.lastSync}</p>
            )}

            <div className="integration-actions">
              <button
                className={`btn-action ${integration.connected ? 'disconnect' : 'connect'}`}
                onClick={() => toggleIntegration(integration.id)}
              >
                {integration.connected ? 'Disconnect' : 'Connect'}
              </button>
              <button className="btn-action configure">Configure</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

const mockIntegrations = [
  {
    id: 1,
    name: 'Gmail',
    logo: '📧',
    description: 'Sync emails and contacts from Gmail',
    connected: true,
    lastSync: '2 hours ago'
  },
  {
    id: 2,
    name: 'Google Calendar',
    logo: '📅',
    description: 'Sync meetings and schedule',
    connected: true,
    lastSync: '5 mins ago'
  },
  {
    id: 3,
    name: 'Zapier',
    logo: '⚡',
    description: 'Connect with 1000+ apps via Zapier',
    connected: true,
    lastSync: '3 days ago'
  },
  {
    id: 4,
    name: 'Slack',
    logo: '💬',
    description: 'Send notifications to Slack',
    connected: false,
    lastSync: 'never'
  },
  {
    id: 5,
    name: 'HubSpot',
    logo: '🎯',
    description: 'Two-way sync with HubSpot',
    connected: true,
    lastSync: '5 mins ago'
  }
];
