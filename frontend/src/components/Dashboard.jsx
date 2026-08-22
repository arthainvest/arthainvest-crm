import React, { useState, useEffect } from 'react';
import { getDashboardAnalytics, getLeads, getDeals } from '../services/api';
import '../styles/Dashboard.css';

export default function Dashboard() {
  const mockAnalytics = {
    total_leads: 5,
    qualified_leads: 0,
    active_deals: 4,
    closed_deals: 0,
    pipeline_value: 345000,
    avg_deal_value: 8600,
    conversion_rate: 0,
    active_opportunities: 4,
    total_contacts: 1247,
    total_deals_value: 25000000,
    conversion_rate_pct: 32,
    active_campaigns: 12
  };

  const loanStages = [
    { label: 'Deals Closed (This Month)', count: 18, value: 4500000 },
    { label: 'In Progress', count: 12, value: 3200000 },
    { label: 'Rejected', count: 5, value: 850000 },
    { label: 'On Hold', count: 7, value: 1550000 },
    { label: 'Login/Sanction', count: 22, value: 6500000 },
    { label: 'Disbursed', count: 14, value: 4200000 }
  ];

  const pipelineStatus = [
    { label: 'New Leads', count: 15 },
    { label: 'Contacted', count: 12 },
    { label: 'Interested', count: 8 },
    { label: 'Proposal', count: 5 }
  ];

  const formatINR = (n) => `₹${n.toLocaleString('en-IN')}`;

  const mockLeads = [
    { id: 1, name: 'Neha Singh', company: 'Startup Fund', status: 'New', lead_tier: 'Premium', ai_score: 85 },
    { id: 2, name: 'Vikram Reddy', company: 'Tech Park', status: 'Contacted', lead_tier: 'Gold', ai_score: 72 },
    { id: 3, name: 'Anjali Desai', company: 'Retail Chain', status: 'Interested', lead_tier: 'Silver', ai_score: 65 },
    { id: 4, name: 'Amit Patel', company: 'Manufacturing', status: 'Qualified', lead_tier: 'Silver', ai_score: 58 },
    { id: 5, name: 'Priya Kapoor', company: 'Digital Ventures', status: 'New', lead_tier: 'Premium', ai_score: 80 }
  ];

  const [analytics, setAnalytics] = useState(mockAnalytics);
  const [recentLeads, setRecentLeads] = useState(mockLeads);
  const [loading, setLoading] = useState(false);
  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [analyticsData, leadsData] = await Promise.all([
        getDashboardAnalytics(token),
        getLeads(token),
      ]);

      if (analyticsData && leadsData) {
        setAnalytics(analyticsData);
        setRecentLeads(leadsData.slice(0, 5));
      } else {
        setAnalytics(mockAnalytics);
        setRecentLeads(mockLeads.slice(0, 5));
      }
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setAnalytics(mockAnalytics);
      setRecentLeads(mockLeads.slice(0, 5));
    } finally {
      setLoading(false);
    }
  };

  // Always show data - use mock if loading or no analytics
  const displayAnalytics = analytics || mockAnalytics;
  const displayLeads = (recentLeads && recentLeads.length > 0) ? recentLeads : mockLeads.slice(0, 5);

  return (
    <div className="dashboard-container">
      <h1>📊 Dashboard</h1>

      <div className="growth-grid">
        <GrowthCard title="Total Contacts" value={displayAnalytics.total_contacts.toLocaleString('en-IN')} trend="↑ 12% from last month" />
        <GrowthCard title="Total Deals" value={formatINR(displayAnalytics.total_deals_value)} trend="↑ 8% from last month" />
        <GrowthCard title="Conversion Rate" value={`${displayAnalytics.conversion_rate_pct}%`} trend="↑ 2% from last month" />
        <GrowthCard title="Active Campaigns" value={displayAnalytics.active_campaigns} trend="Running on LinkedIn & WhatsApp" />
      </div>

      <div className="dashboard-section chart-panel">
        <h2>📈 Sales Performance</h2>
        <div className="chart-placeholder">
          Sales chart - will show real-time data once a payment gateway integration is connected
        </div>
      </div>

      <div className="dashboard-section">
        <h2>Loan Pipeline</h2>
        <div className="stage-grid">
          {loanStages.map((stage) => (
            <div key={stage.label} className="stage-card">
              <div className="stage-label">{stage.label.toUpperCase()}</div>
              <div className="stage-count">{stage.count}</div>
              <div className="stage-value">{formatINR(stage.value)}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="dashboard-section">
        <h2>Pipeline Status</h2>
        <div className="pipeline-status-grid">
          {pipelineStatus.map((s) => (
            <div key={s.label} className="pipeline-status-card">
              <h3>{s.label}</h3>
              <div className="pipeline-status-row">
                <span>Count</span>
                <strong>{s.count}</strong>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="kpi-grid">
        <KPICard
          title="Total Leads"
          value={displayAnalytics.total_leads}
          icon="📊"
          color="#1976d2"
        />
        <KPICard
          title="Qualified Leads"
          value={displayAnalytics.qualified_leads}
          icon="✓"
          color="#1976d2"
        />
        <KPICard
          title="Active Deals"
          value={displayAnalytics.active_deals}
          icon="💼"
          color="#1976d2"
        />
        <KPICard
          title="Closed Deals"
          value={displayAnalytics.closed_deals}
          icon="🎯"
          color="#1976d2"
        />
      </div>

      <div className="dashboard-section">
        <h2>Recent Leads</h2>
        {displayLeads && displayLeads.length > 0 ? (
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
              {displayLeads.map((lead) => (
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

function GrowthCard({ title, value, trend }) {
  return (
    <div className="growth-card">
      <div className="growth-title">{title}</div>
      <div className="growth-value">{value}</div>
      <div className="growth-trend">{trend}</div>
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
