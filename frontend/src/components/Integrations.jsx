import React, { useState, useEffect } from 'react';
import {
  getIntegrations, toggleIntegration, getIntegrationsStatus,
  getLinkedInConnectUrl, getGoogleConnectUrl, disconnectGoogle,
  exportToGoogleSheets, importFromGoogleSheets,
  getZapierWebhooks, createZapierWebhook, deleteZapierWebhook,
  getSlackWebhooks, createSlackWebhook, deleteSlackWebhook
} from '../services/api';
import '../styles/Integrations.css';

// These rows reflect real server-side configuration or a real OAuth connection - checked
// against actual env vars / stored tokens by GET /api/integrations/status, not a DB boolean
// anyone (or any bug) could flip to say anything. Their Connect/Disconnect button (if any)
// does something real instead of just toggling a flag.
const REAL_STATUS_INTEGRATIONS = new Set([
  'WhatsApp Business API', 'Twilio', 'Email Service', 'Mailchimp', 'Claude AI', 'LinkedIn',
  'Google Sheets', 'Gmail', 'Google Calendar', 'Zapier', 'Slack'
]);
// Sheets, Gmail send, and Calendar sync all ride on one connected Google account - the same
// Connect/Disconnect button and OAuth flow serves all three rows.
const GOOGLE_ACCOUNT_INTEGRATIONS = new Set(['Google Sheets', 'Gmail', 'Google Calendar']);
// These five have no user-facing "connect" action at all - they're wired up (or not) purely
// by which env vars are set on the server, so there's nothing to click here.
const ENV_ONLY_INTEGRATIONS = new Set(['WhatsApp Business API', 'Twilio', 'Email Service', 'Mailchimp', 'Claude AI']);

export default function Integrations() {
  const [integrations, setIntegrations] = useState([]);
  const [realStatus, setRealStatus] = useState({});
  const [linkedInConnecting, setLinkedInConnecting] = useState(false);
  const [googleConnecting, setGoogleConnecting] = useState(false);
  const [googleDisconnecting, setGoogleDisconnecting] = useState(false);
  const [sheetsSpreadsheetId, setSheetsSpreadsheetId] = useState('');
  const [sheetsBusy, setSheetsBusy] = useState(false);
  const [zapierWebhooks, setZapierWebhooks] = useState([]);
  const [zapierUrl, setZapierUrl] = useState('');
  const [zapierEventType, setZapierEventType] = useState('all');
  const [zapierBusy, setZapierBusy] = useState(false);
  const [slackWebhooks, setSlackWebhooks] = useState([]);
  const [slackUrl, setSlackUrl] = useState('');
  const [slackEventType, setSlackEventType] = useState('all');
  const [slackBusy, setSlackBusy] = useState(false);
  const token = localStorage.getItem('token');
  // Same export boundary as Contacts/Leads' own Export button - bulk data leaving the CRM
  // stays admin-only, whether it's a CSV download or a push to an external Google Sheet.
  const isAdmin = (localStorage.getItem('role') || '').toLowerCase() === 'admin';

  useEffect(() => {
    fetchIntegrations();
    fetchRealStatus();
    fetchZapierWebhooks();
    fetchSlackWebhooks();

    // Google's OAuth redirect lands back here with ?google=connected|error - same pattern
    // Marketing.jsx already uses for LinkedIn's redirect. Surface it once, then clean the URL.
    const params = new URLSearchParams(window.location.search);
    const googleResult = params.get('google');
    if (googleResult === 'connected') {
      alert('Google account connected successfully.');
      window.history.replaceState({}, '', window.location.pathname);
      fetchRealStatus();
    } else if (googleResult === 'error') {
      alert('Google connection failed - please try again.');
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, []);

  const fetchIntegrations = async () => {
    try {
      const data = await getIntegrations(token);
      setIntegrations(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching integrations:', error);
    }
  };

  const fetchRealStatus = async () => {
    try {
      const data = await getIntegrationsStatus(token);
      setRealStatus(data || {});
    } catch (error) {
      console.error('Error fetching integration status:', error);
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

  const handleConnectLinkedIn = async () => {
    setLinkedInConnecting(true);
    try {
      const result = await getLinkedInConnectUrl(token);
      if (result.configured && result.auth_url) {
        window.location.href = result.auth_url;
        return;
      }
      alert(result.message);
    } catch (error) {
      console.error('Error starting LinkedIn connect:', error);
      alert('Failed to start LinkedIn connection. Please try again.');
    } finally {
      setLinkedInConnecting(false);
    }
  };

  const handleConnectGoogle = async () => {
    setGoogleConnecting(true);
    try {
      const result = await getGoogleConnectUrl(token);
      if (result.configured && result.auth_url) {
        window.location.href = result.auth_url;
        return;
      }
      alert(result.message);
    } catch (error) {
      console.error('Error starting Google connect:', error);
      alert('Failed to start Google connection. Please try again.');
    } finally {
      setGoogleConnecting(false);
    }
  };

  const handleDisconnectGoogle = async () => {
    setGoogleDisconnecting(true);
    try {
      await disconnectGoogle(token);
      await fetchRealStatus();
    } catch (error) {
      console.error('Error disconnecting Google:', error);
      alert('Failed to disconnect Google. Please try again.');
    } finally {
      setGoogleDisconnecting(false);
    }
  };

  const handleSheetsExport = async (entity) => {
    if (!sheetsSpreadsheetId.trim()) {
      alert('Paste the spreadsheet ID first (the part of the sheet URL between /d/ and /edit).');
      return;
    }
    setSheetsBusy(true);
    try {
      const result = await exportToGoogleSheets(token, sheetsSpreadsheetId.trim(), 'Sheet1', entity);
      alert(result.message);
    } catch (error) {
      console.error('Error exporting to Google Sheets:', error);
      alert('Export failed. Please try again.');
    } finally {
      setSheetsBusy(false);
    }
  };

  const handleSheetsImport = async () => {
    if (!sheetsSpreadsheetId.trim()) {
      alert('Paste the spreadsheet ID first (the part of the sheet URL between /d/ and /edit).');
      return;
    }
    setSheetsBusy(true);
    try {
      const result = await importFromGoogleSheets(token, sheetsSpreadsheetId.trim(), 'Sheet1');
      alert(result.message);
    } catch (error) {
      console.error('Error importing from Google Sheets:', error);
      alert('Import failed. Please try again.');
    } finally {
      setSheetsBusy(false);
    }
  };

  const fetchZapierWebhooks = async () => {
    try {
      const data = await getZapierWebhooks(token);
      setZapierWebhooks(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching Zapier webhooks:', error);
    }
  };

  const handleAddZapierWebhook = async () => {
    if (!zapierUrl.trim()) {
      alert('Paste the Zapier "Catch Hook" URL first.');
      return;
    }
    setZapierBusy(true);
    try {
      await createZapierWebhook(token, zapierUrl.trim(), zapierEventType);
      setZapierUrl('');
      await Promise.all([fetchZapierWebhooks(), fetchRealStatus()]);
    } catch (error) {
      console.error('Error adding Zapier webhook:', error);
      alert('Failed to add webhook. Please check the URL and try again.');
    } finally {
      setZapierBusy(false);
    }
  };

  const handleDeleteZapierWebhook = async (webhookId) => {
    setZapierBusy(true);
    try {
      await deleteZapierWebhook(token, webhookId);
      await Promise.all([fetchZapierWebhooks(), fetchRealStatus()]);
    } catch (error) {
      console.error('Error deleting Zapier webhook:', error);
      alert('Failed to remove webhook. Please try again.');
    } finally {
      setZapierBusy(false);
    }
  };

  const fetchSlackWebhooks = async () => {
    try {
      const data = await getSlackWebhooks(token);
      setSlackWebhooks(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching Slack webhooks:', error);
    }
  };

  const handleAddSlackWebhook = async () => {
    if (!slackUrl.trim()) {
      alert('Paste the Slack Incoming Webhook URL first.');
      return;
    }
    setSlackBusy(true);
    try {
      await createSlackWebhook(token, slackUrl.trim(), slackEventType);
      setSlackUrl('');
      await Promise.all([fetchSlackWebhooks(), fetchRealStatus()]);
    } catch (error) {
      console.error('Error adding Slack webhook:', error);
      alert('Failed to add webhook. Please check the URL and try again.');
    } finally {
      setSlackBusy(false);
    }
  };

  const handleDeleteSlackWebhook = async (webhookId) => {
    setSlackBusy(true);
    try {
      await deleteSlackWebhook(token, webhookId);
      await Promise.all([fetchSlackWebhooks(), fetchRealStatus()]);
    } catch (error) {
      console.error('Error deleting Slack webhook:', error);
      alert('Failed to remove webhook. Please try again.');
    } finally {
      setSlackBusy(false);
    }
  };

  return (
    <div className="integrations-container">
      <div className="integrations-header">
        <h1>Integrations</h1>
      </div>

      <p className="integrations-subtitle">Connect your favorite tools to ArthaInvest CRM</p>

      <div className="integrations-grid">
        {integrations.map(integration => {
          const isReal = REAL_STATUS_INTEGRATIONS.has(integration.name);
          const isEnvOnly = ENV_ONLY_INTEGRATIONS.has(integration.name);
          const isLinkedIn = integration.name === 'LinkedIn';
          const isGoogleSheets = integration.name === 'Google Sheets';
          const isGoogleAccountRow = GOOGLE_ACCOUNT_INTEGRATIONS.has(integration.name);
          const isZapier = integration.name === 'Zapier';
          const isSlack = integration.name === 'Slack';
          const status = realStatus[integration.name];
          // For the seven real rows, the actual configured/connected state overrides the
          // cosmetic DB toggle entirely - that toggle can no longer say anything different.
          const connected = isReal ? Boolean(status?.configured) : integration.connected;

          return (
            <div key={integration.id} className="integration-card">
              <div className="integration-header">
                <div className="integration-logo">{integration.logo}</div>
                <h3>{integration.name}</h3>
              </div>

              <p className="integration-description">{integration.description}</p>

              <div className="integration-status">
                <div className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}></div>
                <span className={`status-text ${connected ? 'connected' : 'disconnected'}`}>
                  {connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>

              {isReal && connected && status?.detail && (
                <p className="last-sync">{status.detail}</p>
              )}
              {!isReal && connected && (
                <p className="last-sync">Last sync: {integration.last_sync}</p>
              )}

              <div className="integration-actions">
                {isEnvOnly ? (
                  <span className="integration-env-note">
                    {connected ? 'Configured on the server' : 'Set the required keys in the server .env to enable this'}
                  </span>
                ) : isLinkedIn ? (
                  connected ? (
                    <span className="integration-env-note">Connected - manage from the Marketing tab</span>
                  ) : (
                    <button className="btn-action connect" onClick={handleConnectLinkedIn} disabled={linkedInConnecting}>
                      {linkedInConnecting ? 'Connecting…' : 'Connect'}
                    </button>
                  )
                ) : isGoogleAccountRow ? (
                  connected ? (
                    <button className="btn-action disconnect" onClick={handleDisconnectGoogle} disabled={googleDisconnecting}>
                      {googleDisconnecting ? 'Disconnecting…' : 'Disconnect'}
                    </button>
                  ) : (
                    <button className="btn-action connect" onClick={handleConnectGoogle} disabled={googleConnecting}>
                      {googleConnecting ? 'Connecting…' : 'Connect'}
                    </button>
                  )
                ) : isZapier || isSlack ? (
                  <span className="integration-env-note">Add a webhook URL below to connect</span>
                ) : (
                  <button
                    className={`btn-action ${integration.connected ? 'disconnect' : 'connect'}`}
                    onClick={() => handleToggle(integration)}
                  >
                    {integration.connected ? 'Disconnect' : 'Connect'}
                  </button>
                )}
              </div>

              {isGoogleSheets && connected && (
                <div className="integration-sheets-sync">
                  <input
                    type="text"
                    placeholder="Spreadsheet ID (from the sheet's URL)"
                    value={sheetsSpreadsheetId}
                    onChange={(e) => setSheetsSpreadsheetId(e.target.value)}
                  />
                  <div className="integration-sheets-sync-actions">
                    {isAdmin && (
                      <>
                        <button className="btn-secondary small" onClick={() => handleSheetsExport('contacts')} disabled={sheetsBusy}>
                          Export Contacts
                        </button>
                        <button className="btn-secondary small" onClick={() => handleSheetsExport('leads')} disabled={sheetsBusy}>
                          Export Leads
                        </button>
                      </>
                    )}
                    <button className="btn-secondary small" onClick={handleSheetsImport} disabled={sheetsBusy}>
                      Import Leads
                    </button>
                  </div>
                </div>
              )}

              {isZapier && (
                <div className="integration-sheets-sync">
                  {zapierWebhooks.map((hook) => (
                    <div key={hook.id} className="zapier-webhook-row">
                      <div className="zapier-webhook-info">
                        <span className="zapier-webhook-url" title={hook.url}>{hook.url}</span>
                        <span className="zapier-webhook-meta">
                          {hook.event_type}
                          {hook.last_status ? ` · last: ${hook.last_status}` : ' · not fired yet'}
                        </span>
                      </div>
                      <button
                        className="btn-action disconnect"
                        onClick={() => handleDeleteZapierWebhook(hook.id)}
                        disabled={zapierBusy}
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                  <input
                    type="text"
                    placeholder="Zapier Catch Hook URL"
                    value={zapierUrl}
                    onChange={(e) => setZapierUrl(e.target.value)}
                  />
                  <div className="integration-sheets-sync-actions">
                    <select value={zapierEventType} onChange={(e) => setZapierEventType(e.target.value)}>
                      <option value="all">All events</option>
                      <option value="lead.created">Lead created</option>
                      <option value="deal.closed">Deal closed</option>
                    </select>
                    <button className="btn-secondary small" onClick={handleAddZapierWebhook} disabled={zapierBusy}>
                      Add webhook
                    </button>
                  </div>
                </div>
              )}

              {isSlack && (
                <div className="integration-sheets-sync">
                  {slackWebhooks.map((hook) => (
                    <div key={hook.id} className="zapier-webhook-row">
                      <div className="zapier-webhook-info">
                        <span className="zapier-webhook-url" title={hook.url}>{hook.url}</span>
                        <span className="zapier-webhook-meta">
                          {hook.event_type}
                          {hook.last_status ? ` · last: ${hook.last_status}` : ' · not fired yet'}
                        </span>
                      </div>
                      <button
                        className="btn-action disconnect"
                        onClick={() => handleDeleteSlackWebhook(hook.id)}
                        disabled={slackBusy}
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                  <input
                    type="text"
                    placeholder="Slack Incoming Webhook URL"
                    value={slackUrl}
                    onChange={(e) => setSlackUrl(e.target.value)}
                  />
                  <div className="integration-sheets-sync-actions">
                    <select value={slackEventType} onChange={(e) => setSlackEventType(e.target.value)}>
                      <option value="all">All events</option>
                      <option value="lead.created">Lead created</option>
                      <option value="deal.closed">Deal closed</option>
                    </select>
                    <button className="btn-secondary small" onClick={handleAddSlackWebhook} disabled={slackBusy}>
                      Add webhook
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
