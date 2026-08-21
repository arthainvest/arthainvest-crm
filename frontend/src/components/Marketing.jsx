import React, { useState, useEffect } from 'react';
import '../styles/Marketing.css';

export default function Marketing() {
  const [campaigns, setCampaigns] = useState([]);

  useEffect(() => {
    setCampaigns(mockCampaigns);
  }, []);

  return (
    <div className="marketing-container">
      <div className="marketing-header">
        <h1>Marketing Campaigns</h1>
        <button className="btn-primary">+ New Campaign</button>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">3</div>
          <div className="stat-label">Total Campaigns</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">1</div>
          <div className="stat-label">Active</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">6,700</div>
          <div className="stat-label">Total Recipients</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">38%</div>
          <div className="stat-label">Avg Engagement</div>
        </div>
      </div>

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
              <button className="btn-small">Edit</button>
              <button className="btn-small">View Stats</button>
              <button className="btn-small delete">Delete</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

const mockCampaigns = [
  {
    id: 1,
    name: 'Insurance Awareness',
    type: 'Email',
    status: 'Active',
    recipients: 3000,
    opens: 1200,
    clicks: 450,
    engagement: 45,
    progress: 65
  },
  {
    id: 2,
    name: 'Health Insurance Promotion',
    type: 'WhatsApp',
    status: 'Completed',
    recipients: 2500,
    opens: 2000,
    clicks: 800,
    engagement: 32,
    progress: 100
  },
  {
    id: 3,
    name: 'Q3 Product Launch',
    type: 'Email',
    status: 'Completed',
    recipients: 1200,
    opens: 600,
    clicks: 180,
    engagement: 30,
    progress: 100
  }
];
