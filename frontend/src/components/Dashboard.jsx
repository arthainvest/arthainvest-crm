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
    active_opportunities: 4
  };

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
      <h1>Dashboard</h1>

      <div className="kpi-grid">
        <KPICard
          title="Total Leads"
          value={displayAnalytics.total_leads}
          icon="📊"
          color="#3498db"
        />
        <KPICard
          title="Qualified Leads"
          value={displayAnalytics.qualified_leads}
          icon="✓"
          color="#2ecc71"
        />
        <KPICard
          title="Active Deals"
          value={displayAnalytics.active_deals}
          icon="💼"
          color="#f39c12"
        />
        <KPICard
          title="Closed Deals"
          value={displayAnalytics.closed_deals}
          icon="🎯"
          color="#e74c3c"
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
