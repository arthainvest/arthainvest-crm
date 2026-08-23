import React, { useState, useEffect } from 'react';
import { getCampaigns, createCampaign, updateCampaign, deleteCampaign, syncMailchimp } from '../services/api';
import '../styles/Marketing.css';

const emptyCampaignForm = { name: '', type: 'Email', status: 'Active', recipients: '' };

export default function Marketing() {
  const [campaigns, setCampaigns] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [campaignForm, setCampaignForm] = useState(emptyCampaignForm);
  const [mailchimpSyncing, setMailchimpSyncing] = useState(false);

  const token = localStorage.getItem('token');

  const handleMailchimpSync = async () => {
    setMailchimpSyncing(true);
    try {
      const result = await syncMailchimp(token);
      alert(result.message);
    } catch (error) {
      console.error('Error syncing Mailchimp:', error);
      alert('Failed to sync with Mailchimp. Please try again.');
    } finally {
      setMailchimpSyncing(false);
    }
  };

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
    try {
      const data = await getCampaigns(token);
      setCampaigns(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching campaigns:', error);
    }
  };

  const handleNewCampaignClick = () => {
    setEditingId(null);
    setCampaignForm(emptyCampaignForm);
    setShowForm(true);
  };

  const handleEditClick = (campaign) => {
    setEditingId(campaign.id);
    setCampaignForm({
      name: campaign.name,
      type: campaign.type,
      status: campaign.status,
      recipients: campaign.recipients
    });
    setShowForm(true);
  };

  const handleSaveCampaign = async (e) => {
    e.preventDefault();
    if (!campaignForm.name.trim()) return;

    try {
      if (editingId) {
        await updateCampaign(token, editingId, {
          name: campaignForm.name,
          type: campaignForm.type,
          status: campaignForm.status,
          recipients: Number(campaignForm.recipients) || 0
        });
      } else {
        await createCampaign(token, {
          name: campaignForm.name,
          type: campaignForm.type,
          status: campaignForm.status,
          recipients: Number(campaignForm.recipients) || 0
        });
      }
      setShowForm(false);
      setCampaignForm(emptyCampaignForm);
      setEditingId(null);
      fetchCampaigns();
    } catch (error) {
      console.error('Error saving campaign:', error);
      alert('Failed to save campaign. Please try again.');
    }
  };

  const handleDeleteCampaign = async (id) => {
    if (!window.confirm('Are you sure you want to delete this campaign?')) return;
    try {
      await deleteCampaign(token, id);
      setCampaigns((prev) => prev.filter((c) => c.id !== id));
    } catch (error) {
      console.error('Error deleting campaign:', error);
      alert('Failed to delete campaign. Please try again.');
    }
  };

  const totalCampaigns = campaigns.length;
  const activeCampaigns = campaigns.filter((c) => c.status === 'Active').length;
  const totalRecipients = campaigns.reduce((sum, c) => sum + (c.recipients || 0), 0);
  const avgEngagement = totalCampaigns > 0
    ? Math.round(campaigns.reduce((sum, c) => sum + (c.engagement || 0), 0) / totalCampaigns)
    : 0;

  return (
    <div className="marketing-container">
      <div className="marketing-header">
        <h1>Marketing Campaigns</h1>
        <button className="btn-primary" onClick={handleNewCampaignClick}>+ New Campaign</button>
      </div>

      <div className="mailchimp-card">
        <div className="mailchimp-info">
          <span className="mailchimp-icon">🐒</span>
          <div>
            <h3>Email Marketing (Mailchimp)</h3>
            <p>Sync your contacts into a Mailchimp audience for email campaigns.</p>
          </div>
        </div>
        <button className="btn-secondary" onClick={handleMailchimpSync} disabled={mailchimpSyncing}>
          {mailchimpSyncing ? 'Syncing…' : 'Sync Contacts to Mailchimp'}
        </button>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{totalCampaigns}</div>
          <div className="stat-label">Total Campaigns</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{activeCampaigns}</div>
          <div className="stat-label">Active</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{totalRecipients.toLocaleString('en-IN')}</div>
          <div className="stat-label">Total Recipients</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{avgEngagement}%</div>
          <div className="stat-label">Avg Engagement</div>
        </div>
      </div>

      {campaigns.length === 0 ? (
        <p className="no-data">No campaigns yet. Create one to get started.</p>
      ) : (
        <div className="campaigns-grid">
          {campaigns.map(campaign => (
            <div key={campaign.id} className={`campaign-card ${campaign.status.toLowerCase()}`}>
              <div className="campaign-header">
                <h3>{campaign.name}</h3>
                <span className={`status-badge ${campaign.status.toLowerCase()}`}>{campaign.status}</span>
              </div>

              <div className="campaign-info">
                <p><strong>Type:</strong> {campaign.type}</p>
                <p><strong>Recipients:</strong> {campaign.recipients}</p>
                <p><strong>Engagement:</strong> {campaign.engagement}%</p>
              </div>

              <div className="campaign-progress">
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${campaign.progress}%` }}></div>
                </div>
                <p className="progress-text">{campaign.progress}% Complete</p>
              </div>

              <div className="campaign-actions">
                <button className="btn-small" onClick={() => handleEditClick(campaign)}>Edit</button>
                <button className="btn-small delete" onClick={() => handleDeleteCampaign(campaign.id)}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingId ? 'Edit Campaign' : 'New Campaign'}</h2>
              <button className="btn-close" onClick={() => setShowForm(false)}>×</button>
            </div>

            <form onSubmit={handleSaveCampaign}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Campaign Name *</label>
                  <input
                    type="text"
                    required
                    value={campaignForm.name}
                    onChange={(e) => setCampaignForm({ ...campaignForm, name: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Type</label>
                  <select
                    value={campaignForm.type}
                    onChange={(e) => setCampaignForm({ ...campaignForm, type: e.target.value })}
                  >
                    <option value="Email">Email</option>
                    <option value="WhatsApp">WhatsApp</option>
                    <option value="SMS">SMS</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Status</label>
                  <select
                    value={campaignForm.status}
                    onChange={(e) => setCampaignForm({ ...campaignForm, status: e.target.value })}
                  >
                    <option value="Active">Active</option>
                    <option value="Completed">Completed</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Recipients</label>
                  <input
                    type="number"
                    min="0"
                    value={campaignForm.recipients}
                    onChange={(e) => setCampaignForm({ ...campaignForm, recipients: e.target.value })}
                  />
                </div>
              </div>
              <div className="modal-actions">
                <button type="submit" className="btn-primary">
                  {editingId ? 'Save Changes' : 'Create Campaign'}
                </button>
                <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
