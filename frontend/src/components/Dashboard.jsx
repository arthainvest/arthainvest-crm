import React, { useState, useEffect } from 'react';
import { getDashboardAnalytics, getLeads } from '../services/api';
import '../styles/Dashboard.css';

const emptyAnalytics = {
  total_leads: 0,
  qualified_leads: 0,
  active_deals: 0,
  closed_deals: 0,
  total_contacts: 0,
  total_deals_value: 0,
  conversion_rate_pct: 0,
  active_campaigns: 0,
  loan_stages: [],
  pipeline_status: []
};

export default function Dashboard() {
  const [analytics, setAnalytics] = useState(emptyAnalytics);
  const [recentLeads, setRecentLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const token = localStorage.getItem('token');

  const formatINR = (n) => `₹${Number(n || 0).toLocaleString('en-IN')}`;

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [analyticsData, leadsData] = await Promise.all([
        getDashboardAnalytics(token),
        getLeads(token),
      ]);
      setAnalytics({ ...emptyAnalytics, ...(analyticsData || {}) });
      setRecentLeads(Array.isArray(leadsData) ? leadsData.slice(0, 5) : []);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard-container">
      <h1>📊 Dashboard</h1>

      <div className="growth-grid">
        <GrowthCard title="Total Contacts" value={analytics.total_contacts.toLocaleString('en-IN')} />
        <GrowthCard title="Total Deals Value" value={formatINR(analytics.total_deals_value)} />
        <GrowthCard title="Conversion Rate" value={`${analytics.conversion_rate_pct}%`} />
        <GrowthCard title="Active Campaigns" value={analytics.active_campaigns} />
      </div>

      <div className="dashboard-section chart-panel">
        <h2>📈 Sales Performance</h2>
        <div className="chart-placeholder">
          Sales chart - will show real-time data once a payment gateway integration is connected
        </div>
      </div>

      <div className="dashboard-section">
        <h2>Loan Pipeline</h2>
        {loading ? (
          <p className="loading-text">Loading…</p>
        ) : (
          <div className="stage-grid">
            {analytics.loan_stages.map((stage) => (
              <div key={stage.label} className="stage-card">
                <div className="stage-label">{stage.label.toUpperCase()}</div>
                <div className="stage-count">{stage.count}</div>
                <div className="stage-value">{formatINR(stage.value)}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="dashboard-section">
        <h2>Pipeline Status</h2>
        {loading ? (
          <p className="loading-text">Loading…</p>
        ) : (
          <div className="pipeline-status-grid">
            {analytics.pipeline_status.map((s) => (
              <div key={s.label} className="pipeline-status-card">
                <h3>{s.label}</h3>
                <div className="pipeline-status-row">
                  <span>Count</span>
                  <strong>{s.count}</strong>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="kpi-grid">
        <KPICard title="Total Leads" value={analytics.total_leads} icon="📊" color="#1976d2" />
        <KPICard title="Qualified Leads" value={analytics.qualified_leads} icon="✓" color="#1976d2" />
        <KPICard title="Active Deals" value={analytics.active_deals} icon="💼" color="#1976d2" />
        <KPICard title="Closed Deals" value={analytics.closed_deals} icon="🎯" color="#1976d2" />
      </div>

      <div className="dashboard-section">
        <h2>Recent Leads</h2>
        {recentLeads.length > 0 ? (
          <table className="leads-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Company</th>
                <th>Status</th>
                <th>Tier</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              {recentLeads.map((lead) => (
                <tr key={lead.id}>
                  <td>{lead.name}</td>
                  <td>{lead.company || '-'}</td>
                  <td>
                    <span className={`status-badge ${lead.status}`}>
                      {lead.status}
                    </span>
                  </td>
                  <td>{lead.lead_tier || '-'}</td>
                  <td>{lead.ai_score || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No leads yet</p>
        )}
      </div>
    </div>
  );
}

function GrowthCard({ title, value }) {
  return (
    <div className="growth-card">
      <div className="growth-title">{title}</div>
      <div className="growth-value">{value}</div>
    </div>
  );
}

function KPICard({ title, value, icon, color }) {
  return (
    <div className="kpi-card" style={{ borderLeftColor: color }}>
      <div className="kpi-icon">{icon}</div>
      <div className="kpi-content">
        <h3>{title}</h3>
        <p className="kpi-value">{value}</p>
      </div>
    </div>
  );
}
