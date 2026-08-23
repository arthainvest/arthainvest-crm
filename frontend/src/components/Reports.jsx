import React, { useState, useEffect } from 'react';
import {
  getSalesAnalytics, getContactsAnalytics, getCallsAnalytics,
  getCampaigns, getTeamAnalytics, getSettings, updateSettings
} from '../services/api';
import '../styles/Reports.css';

const REPORT_PERIODS = ['This Month', 'Last Month', 'Last Quarter', 'This Year'];
const ROLE_LABELS = { admin: 'Admin', team_lead: 'Team Leader', location_head: 'Location Head', employee: 'Employee' };

export default function Reports() {
  const [activeTab, setActiveTab] = useState('sales');
  const [salesData, setSalesData] = useState(null);
  const [contactsData, setContactsData] = useState(null);
  const [callsData, setCallsData] = useState(null);
  const [campaigns, setCampaigns] = useState([]);
  const [teamStats, setTeamStats] = useState([]);
  const [reportPeriod, setReportPeriod] = useState('This Month');
  const [showSettings, setShowSettings] = useState(false);
  const [savingSettings, setSavingSettings] = useState(false);
  const token = localStorage.getItem('token');

  useEffect(() => {
    getSalesAnalytics(token)
      .then(setSalesData)
      .catch((error) => console.error('Error fetching sales analytics:', error));
    getContactsAnalytics(token)
      .then(setContactsData)
      .catch((error) => console.error('Error fetching contacts analytics:', error));
    getCallsAnalytics(token)
      .then(setCallsData)
      .catch((error) => console.error('Error fetching calls analytics:', error));
    getCampaigns(token)
      .then((data) => setCampaigns(Array.isArray(data) ? data : []))
      .catch((error) => console.error('Error fetching campaigns:', error));
    getTeamAnalytics(token)
      .then((data) => setTeamStats(Array.isArray(data) ? data : []))
      .catch((error) => console.error('Error fetching team analytics:', error));
    getSettings(token)
      .then((data) => { if (data.default_report_period) setReportPeriod(data.default_report_period); })
      .catch((error) => console.error('Error fetching settings:', error));
  }, [token]);

  const handleSaveReportPeriod = async () => {
    setSavingSettings(true);
    try {
      await updateSettings(token, { default_report_period: reportPeriod });
      setShowSettings(false);
    } catch (error) {
      console.error('Error saving report settings:', error);
      alert('Failed to save report settings. Please try again.');
    } finally {
      setSavingSettings(false);
    }
  };

  const fmtStat = (v, isRevenue) => {
    if (v === null || v === undefined) return '—';
    return isRevenue ? `₹${Number(v).toLocaleString('en-IN')}` : v;
  };

  const maxRecipients = Math.max(1, ...campaigns.map((c) => c.recipients || 0));

  const reportTabs = [
    { id: 'sales', label: 'Sales', icon: '📊' },
    { id: 'contacts', label: 'Contacts', icon: '👥' },
    { id: 'calls', label: 'Calls', icon: '☎️' }
  ];

  const placeholderMetrics = [
    { label: 'Total Revenue', value: '…' },
    { label: 'Deals Closed', value: '…' },
    { label: 'Win Rate', value: '…' },
    { label: 'Avg Deal Size', value: '…' }
  ];

  // All three tabs now use real data, computed from actual leads/deals/contacts/calls.
  const salesMetrics = salesData ? [
    { label: 'Total Revenue', value: `₹${salesData.total_revenue.toLocaleString('en-IN')}` },
    { label: 'Deals Closed', value: String(salesData.deals_closed) },
    { label: 'Win Rate', value: `${salesData.win_rate}%` },
    { label: 'Avg Deal Size', value: `₹${salesData.avg_deal_value.toLocaleString('en-IN')}` }
  ] : placeholderMetrics;

  const contactMetrics = contactsData ? [
    { label: 'Total Contacts', value: String(contactsData.total_contacts) },
    { label: 'Active Contacts', value: String(contactsData.active_contacts) },
    { label: 'Avg Response Time', value: contactsData.avg_response_time_hours != null ? `${contactsData.avg_response_time_hours} hrs` : 'N/A' },
    { label: 'Conversion Rate', value: `${contactsData.conversion_rate}%` }
  ] : placeholderMetrics;

  const callMetrics = callsData ? [
    { label: 'Total Calls', value: String(callsData.total_calls) },
    { label: 'Avg Call Duration', value: callsData.avg_duration },
    { label: 'Call Success Rate', value: `${callsData.call_success_rate}%` },
    { label: 'Calls This Month', value: String(callsData.calls_this_month) }
  ] : placeholderMetrics;

  const getMetrics = () => {
    switch(activeTab) {
      case 'contacts': return contactMetrics;
      case 'calls': return callMetrics;
      default: return salesMetrics;
    }
  };

  return (
    <div className="reports-container">
      <div className="reports-header">
        <h1>Reports</h1>
        <div className="reports-header-actions">
          <button className="btn-secondary" onClick={() => setShowSettings(true)}>⚙️ Report Settings</button>
          <button className="btn-primary">📊 Export Report</button>
        </div>
      </div>

      <div className="tab-navigation">
        {reportTabs.map(tab => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      <div className="metrics-grid">
        {getMetrics().map((metric, idx) => (
          <div key={idx} className="metric-card">
            <div className="metric-value">{metric.value}</div>
            <div className="metric-label">{metric.label}</div>
          </div>
        ))}
      </div>

      <div className="chart-container">
        <h3>Performance Trend</h3>
        <p className="placeholder">📈 Chart visualization - Integration with Chart.js pending</p>
        <div style={{ height: '300px', background: '#1976d2', borderRadius: '8px', opacity: 0.1 }}></div>
      </div>

      <div className="chart-container">
        <h3>Campaign Performance</h3>
        {campaigns.length === 0 ? (
          <p className="placeholder">No campaigns yet - create one in Marketing to see performance here.</p>
        ) : (
          <div className="campaign-perf-list">
            {campaigns.map((c) => (
              <div key={c.id} className="campaign-perf-row">
                <div className="campaign-perf-name">{c.name}</div>
                <div className="campaign-perf-bars">
                  <div className="campaign-perf-bar-track">
                    <div className="campaign-perf-bar recipients" style={{ width: `${(c.recipients / maxRecipients) * 100}%` }}></div>
                  </div>
                  <div className="campaign-perf-bar-track">
                    <div className="campaign-perf-bar opens" style={{ width: `${(c.opens / maxRecipients) * 100}%` }}></div>
                  </div>
                  <div className="campaign-perf-bar-track">
                    <div className="campaign-perf-bar clicks" style={{ width: `${(c.clicks / maxRecipients) * 100}%` }}></div>
                  </div>
                </div>
                <div className="campaign-perf-legend">
                  <span><i className="dot recipients"></i>{c.recipients} sent</span>
                  <span><i className="dot opens"></i>{c.opens} opened</span>
                  <span><i className="dot clicks"></i>{c.clicks} clicked</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="chart-container">
        <h3>Team Productivity</h3>
        {teamStats.length === 0 ? (
          <p className="placeholder">No team members yet - add some in Team to see productivity here.</p>
        ) : (
          <div className="team-productivity-table-wrapper">
            <table className="team-productivity-table">
              <thead>
                <tr>
                  <th>Team Member</th>
                  <th>Role</th>
                  <th>Calls</th>
                  <th>Deals Closed</th>
                  <th>Revenue</th>
                  <th>Conversion Rate</th>
                </tr>
              </thead>
              <tbody>
                {teamStats.map((m) => (
                  <tr key={m.id}>
                    <td>{m.name}</td>
                    <td>{ROLE_LABELS[m.role] || m.role}</td>
                    <td>{fmtStat(m.calls)}</td>
                    <td>{fmtStat(m.deals_closed)}</td>
                    <td>{fmtStat(m.revenue, true)}</td>
                    <td>{m.conversion_rate === null || m.conversion_rate === undefined ? '—' : `${m.conversion_rate}%`}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="report-controls">
        <label>Date Range:</label>
        <select value={reportPeriod} onChange={(e) => setReportPeriod(e.target.value)}>
          {REPORT_PERIODS.map((p) => <option key={p}>{p}</option>)}
        </select>
      </div>

      {showSettings && (
        <div className="modal-overlay" onClick={() => setShowSettings(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Report Settings</h2>
              <button className="btn-close" onClick={() => setShowSettings(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>Default Date Range</label>
                <select value={reportPeriod} onChange={(e) => setReportPeriod(e.target.value)}>
                  {REPORT_PERIODS.map((p) => <option key={p}>{p}</option>)}
                </select>
              </div>
            </div>
            <div className="modal-actions">
              <button className="btn-primary" onClick={handleSaveReportPeriod} disabled={savingSettings}>
                {savingSettings ? 'Saving…' : 'Save'}
              </button>
              <button className="btn-secondary" onClick={() => setShowSettings(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
