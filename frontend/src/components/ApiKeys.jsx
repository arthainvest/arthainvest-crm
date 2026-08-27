import React, { useState, useEffect, useCallback } from 'react';
import { getApiKeys, createApiKey, revokeApiKey, API_URL } from '../services/api';
import '../styles/ApiKeys.css';

function formatDate(ts) {
  if (!ts) return null;
  const d = new Date(ts.includes('T') ? ts : ts.replace(' ', 'T'));
  if (Number.isNaN(d.getTime())) return ts;
  return d.toLocaleString([], { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export default function ApiKeys() {
  const token = localStorage.getItem('token');

  const [keys, setKeys] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [createdKey, setCreatedKey] = useState(null); // { name, api_key } - shown once
  const [copied, setCopied] = useState(false);

  const fetchKeys = useCallback(async () => {
    try {
      const data = await getApiKeys(token);
      setKeys(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching API keys:', error);
    }
  }, [token]);

  useEffect(() => {
    fetchKeys();
  }, [fetchKeys]);

  const openCreateModal = () => {
    setNewKeyName('');
    setCreatedKey(null);
    setCopied(false);
    setShowCreateModal(true);
  };

  const closeCreateModal = () => {
    setShowCreateModal(false);
    if (createdKey) fetchKeys();
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    try {
      const result = await createApiKey(token, newKeyName.trim());
      setCreatedKey(result);
    } catch (error) {
      console.error('Error creating API key:', error);
      alert('Failed to create API key. Please try again.');
    }
  };

  const handleCopy = async () => {
    if (!createdKey) return;
    try {
      await navigator.clipboard.writeText(createdKey.api_key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Clipboard copy failed:', error);
      alert('Could not copy automatically - please select and copy the key manually.');
    }
  };

  const handleRevoke = async (key) => {
    if (!window.confirm(`Revoke "${key.name}"? Any external system using this key will stop working immediately.`)) return;
    try {
      await revokeApiKey(token, key.id);
      fetchKeys();
    } catch (error) {
      console.error('Error revoking API key:', error);
      alert('Failed to revoke API key. Please try again.');
    }
  };

  const activeKeys = keys.filter((k) => !k.revoked_at);
  const revokedKeys = keys.filter((k) => k.revoked_at);

  return (
    <div className="apikeys-container">
      <div className="apikeys-header">
        <div>
          <h1>API Keys</h1>
          <p className="apikeys-subtitle">Let external tools - a website form, a click-to-WhatsApp ad landing page, a Google Sheet, Zapier - create leads in this CRM without a login.</p>
        </div>
        <button className="btn-primary" onClick={openCreateModal}>+ New API Key</button>
      </div>

      <div className="apikeys-howto">
        <h4>How to use a key</h4>
        <p>Give an external system this key in an <code>X-API-Key</code> header, and have it send a <code>POST</code> request to:</p>
        <div className="apikeys-code-block">POST {API_URL}/api/public/leads</div>
        <p className="apikeys-howto-example">Example body: <code>{'{ "name": "Jane Doe", "phone": "9876543210", "source": "Facebook Ad" }'}</code></p>
      </div>

      <div className="apikeys-list">
        {activeKeys.length === 0 && revokedKeys.length === 0 ? (
          <p className="no-data">No API keys yet. Create one to let an external tool add leads into this CRM.</p>
        ) : (
          <div className="table-wrap">
            <table className="apikeys-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Key</th>
                  <th>Created</th>
                  <th>Last used</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {activeKeys.map((key) => (
                  <tr key={key.id}>
                    <td>{key.name}</td>
                    <td><code>{key.key_prefix}…</code></td>
                    <td>{formatDate(key.created_at)}</td>
                    <td>{formatDate(key.last_used_at) || <span className="apikeys-muted">Never used</span>}</td>
                    <td><span className="apikey-status active">Active</span></td>
                    <td><button className="btn-danger" onClick={() => handleRevoke(key)}>Revoke</button></td>
                  </tr>
                ))}
                {revokedKeys.map((key) => (
                  <tr key={key.id} className="apikeys-row-revoked">
                    <td>{key.name}</td>
                    <td><code>{key.key_prefix}…</code></td>
                    <td>{formatDate(key.created_at)}</td>
                    <td>{formatDate(key.last_used_at) || <span className="apikeys-muted">Never used</span>}</td>
                    <td><span className="apikey-status revoked">Revoked {formatDate(key.revoked_at)}</span></td>
                    <td></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showCreateModal && (
        <div className="modal-overlay" onClick={closeCreateModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{createdKey ? 'API Key Created' : 'New API Key'}</h2>
              <button className="btn-close" onClick={closeCreateModal}>×</button>
            </div>

            {!createdKey ? (
              <form onSubmit={handleCreate}>
                <div className="modal-body">
                  <div className="form-group">
                    <label>Name *</label>
                    <input
                      type="text"
                      required
                      autoFocus
                      placeholder="e.g. Landing Page Form"
                      value={newKeyName}
                      onChange={(e) => setNewKeyName(e.target.value)}
                    />
                  </div>
                </div>
                <div className="modal-actions">
                  <button type="submit" className="btn-primary">Create Key</button>
                  <button type="button" className="btn-secondary" onClick={closeCreateModal}>Cancel</button>
                </div>
              </form>
            ) : (
              <div className="modal-body">
                <p className="apikeys-warning">
                  ⚠️ Copy this key now - for your security, it will never be shown again. If you lose it, revoke this key and create a new one.
                </p>
                <div className="apikeys-reveal-row">
                  <code className="apikeys-reveal-key">{createdKey.api_key}</code>
                  <button type="button" className="btn-secondary" onClick={handleCopy}>{copied ? 'Copied!' : 'Copy'}</button>
                </div>
                <div className="modal-actions">
                  <button type="button" className="btn-primary" onClick={closeCreateModal}>Done</button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
