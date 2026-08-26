import React, { useState, useEffect } from 'react';
import { getDashboardAnalytics, getLeads, getUpcomingRenewals, sendWhatsApp, sendEmailReal, getLoanStageDeals } from '../services/api';
import { LOAN_PRODUCTS } from '../constants/loanProducts';
import '../styles/Dashboard.css';

// Maps a Pipeline Status card's display label back to the real leads.status value GET
// /api/leads?status= expects - "New Leads" is a friendlier label than the raw "New".
const PIPELINE_STATUS_TO_LEAD_STATUS = {
  'New Leads': 'New', 'Contacted': 'Contacted', 'Interested': 'Interested', 'Qualified': 'Qualified'
};

const dealLabel = (deal) => {
  const productInfo = LOAN_PRODUCTS.find((p) => p.id === deal.loan_product);
  return `${productInfo?.name || deal.loan_product} · ₹${(deal.deal_value || 0).toLocaleString('en-IN')}`;
};

const URGENCY_LABELS = {
  overdue: 'Overdue',
  due_soon: 'Due Soon',
  upcoming: 'Upcoming'
};

const renewalMessage = (renewal) => {
  const dateStr = new Date(renewal.renewal_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' });
  const bankPart = renewal.bank ? ` with ${renewal.bank}` : '';
  return `Hi ${renewal.name}, this is a reminder that your policy/loan${bankPart} is due for renewal on ${dateStr}. Renewing on time keeps your coverage active with no gap. Reply here or call us and we'll take care of it for you. - ArthaInvest`;
};

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
  const [renewals, setRenewals] = useState([]);
  const [sendingReminder, setSendingReminder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedStage, setExpandedStage] = useState(null);
  const [stageDeals, setStageDeals] = useState([]);
  const [loadingStageDeals, setLoadingStageDeals] = useState(false);
  const [expandedStatus, setExpandedStatus] = useState(null);
  const [statusLeads, setStatusLeads] = useState([]);
  const [loadingStatusLeads, setLoadingStatusLeads] = useState(false);
  const token = localStorage.getItem('token');

  const toggleStage = async (label) => {
    if (expandedStage === label) {
      setExpandedStage(null);
      return;
    }
    setExpandedStage(label);
    setLoadingStageDeals(true);
    try {
      const data = await getLoanStageDeals(token, label);
      setStageDeals(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching loan stage deals:', err);
      setStageDeals([]);
    } finally {
      setLoadingStageDeals(false);
    }
  };

  const toggleStatus = async (label) => {
    if (expandedStatus === label) {
      setExpandedStatus(null);
      return;
    }
    setExpandedStatus(label);
    setLoadingStatusLeads(true);
    try {
      const data = await getLeads(token, PIPELINE_STATUS_TO_LEAD_STATUS[label] || label);
      setStatusLeads(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching leads for pipeline status:', err);
      setStatusLeads([]);
    } finally {
      setLoadingStatusLeads(false);
    }
  };

  const formatINR = (n) => `₹${Number(n || 0).toLocaleString('en-IN')}`;

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [analyticsData, leadsData, renewalsData] = await Promise.all([
        getDashboardAnalytics(token),
        getLeads(token),
        getUpcomingRenewals(token),
      ]);
      setAnalytics({ ...emptyAnalytics, ...(analyticsData || {}) });
      setRecentLeads(Array.isArray(leadsData) ? leadsData.slice(0, 5) : []);
      setRenewals(Array.isArray(renewalsData) ? renewalsData : []);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSendRenewalReminder = async (renewal, channel) => {
    const busyKey = `${renewal.id}-${channel}`;
    if (channel === 'whatsapp' && !renewal.phone) { alert('No phone number on file for this contact.'); return; }
    if (channel === 'email' && !renewal.email) { alert('No email on file for this contact.'); return; }

    setSendingReminder(busyKey);
    try {
      const message = renewalMessage(renewal);
      const result = channel === 'whatsapp'
        ? await sendWhatsApp(token, renewal.phone, message, { contactId: renewal.id })
        : await sendEmailReal(token, renewal.email, 'Your renewal is coming up', message, { contactId: renewal.id });

      if (result.configured) {
        alert(result.message);
      } else if (channel === 'whatsapp') {
        window.open(`https://wa.me/${renewal.phone.replace(/\D/g, '')}?text=${encodeURIComponent(message)}`, '_blank');
      } else {
        window.location.href = `mailto:${renewal.email}?subject=${encodeURIComponent('Your renewal is coming up')}&body=${encodeURIComponent(message)}`;
      }
    } catch (error) {
      console.error('Error sending renewal reminder:', error);
      alert('Failed to send reminder. Please try again.');
    } finally {
      setSendingReminder(null);
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

      <div className="dashboard-section">
        <h2>📅 Upcoming Renewals {renewals.length > 0 && `(${renewals.length})`}</h2>
        {loading ? (
          <p className="loading-text">Loading…</p>
        ) : renewals.length === 0 ? (
          <p>No renewals due in the next 30 days. Add a Renewal Date to a contact in Contacts to track it here.</p>
        ) : (
          <div className="renewals-table-wrapper">
            <table className="leads-table">
              <thead>
                <tr>
                  <th>Client</th>
                  <th>Bank/Insurer</th>
                  <th>Amount</th>
                  <th>Renewal Date</th>
                  <th>Status</th>
                  <th>Send Reminder</th>
                </tr>
              </thead>
              <tbody>
                {renewals.map((r) => (
                  <tr key={r.id}>
                    <td>{r.name}</td>
                    <td>{r.bank || '-'}</td>
                    <td>{r.amount != null ? formatINR(r.amount) : '-'}</td>
                    <td>{new Date(r.renewal_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</td>
                    <td>
                      <span className={`renewal-urgency-badge urgency-${r.urgency}`}>
                        {URGENCY_LABELS[r.urgency]}{r.urgency === 'overdue' ? ` ${Math.abs(r.days_until_renewal)}d` : ` ${r.days_until_renewal}d`}
                      </span>
                    </td>
                    <td className="renewal-reminder-actions">
                      <button
                        className="btn-renewal-reminder whatsapp"
                        onClick={() => handleSendRenewalReminder(r, 'whatsapp')}
                        disabled={sendingReminder === `${r.id}-whatsapp`}
                      >
                        {sendingReminder === `${r.id}-whatsapp` ? '…' : '💬 WhatsApp'}
                      </button>
                      <button
                        className="btn-renewal-reminder email"
                        onClick={() => handleSendRenewalReminder(r, 'email')}
                        disabled={sendingReminder === `${r.id}-email`}
                      >
                        {sendingReminder === `${r.id}-email` ? '…' : '📧 Email'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
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
              <div key={stage.label} className="stage-card-wrapper">
                <button type="button" className="stage-card" onClick={() => toggleStage(stage.label)}>
                  <div className="stage-label">{stage.label.toUpperCase()}</div>
                  <div className="stage-count">{stage.count}</div>
                  <div className="stage-value">{formatINR(stage.value)}</div>
                </button>
                {expandedStage === stage.label && (
                  <div className="stage-drilldown">
                    {loadingStageDeals ? (
                      <p className="no-data-inline">Loading…</p>
                    ) : stageDeals.length === 0 ? (
                      <p className="no-data-inline">No deals in this bucket.</p>
                    ) : (
                      <ul className="drilldown-list">
                        {stageDeals.map((d) => (
                          <li key={d.id}>{dealLabel(d)} <span className="drilldown-status">{d.assigned_team_member_name || 'Unassigned'}</span></li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
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
              <div key={s.label} className="pipeline-status-card-wrapper">
                <button type="button" className="pipeline-status-card" onClick={() => toggleStatus(s.label)}>
                  <h3>{s.label}</h3>
                  <div className="pipeline-status-row">
                    <span>Count</span>
                    <strong>{s.count}</strong>
                  </div>
                </button>
                {expandedStatus === s.label && (
                  <div className="stage-drilldown">
                    {loadingStatusLeads ? (
                      <p className="no-data-inline">Loading…</p>
                    ) : statusLeads.length === 0 ? (
                      <p className="no-data-inline">No leads in this status.</p>
                    ) : (
                      <ul className="drilldown-list">
                        {statusLeads.map((l) => (
                          <li key={l.id}>{l.name} <span className="drilldown-status">{l.phone || '-'}</span></li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
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
