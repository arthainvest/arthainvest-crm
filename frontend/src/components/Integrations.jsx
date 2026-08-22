import React, { useState, useEffect } from 'react';
import { getIntegrations, toggleIntegration } from '../services/api';
import '../styles/Integrations.css';

export default function Integrations() {
  const [integrations, setIntegrations] = useState([]);
  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchIntegrations();
  }, []);

  const fetchIntegrations = async () => {
    try {
      const data = await getIntegrations(token);
      setIntegrations(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching integrations:', error);
    }
  };

  const handleToggle = async (integration) => {
    const nextConnected = !integration.connected;
    // Optimistic update, reverted below if the request fails
    setIntegrations((prev) => prev.map((i) =>
      i.id === integration.id ? { ...i, connected: nextConnected, last_sync: nextConnected ? 'now' : 'never' } : i
    ));
    try {
      const updated = await toggleIntegration(token, integration.id, nextConnected);
      setIntegrations((prev) => prev.map((i) => (i.id === integration.id ? updated : i)));
    } catch (error) {
      console.error('Error toggling integration:', error);
      setIntegrations((prev) => prev.map((i) => (i.id === integration.id ? integration : i)));
      alert('Failed to update integration. Please try again.');
    }
  };

  return (
    <div className="integrations-container">
      <div className="integrations-header">
        <h1>Integrations</h1>
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
              <p className="last-sync">Last sync: {integration.last_sync}</p>
            )}

            <div className="integration-actions">
              <button
                className={`btn-action ${integration.connected ? 'disconnect' : 'connect'}`}
                onClick={() => handleToggle(integration)}
              >
                {integration.connected ? 'Disconnect' : 'Connect'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
