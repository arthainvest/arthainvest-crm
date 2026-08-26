import React, { useState, useEffect } from 'react';
import {
  getSalesAnalytics, getContactsAnalytics, getCallsAnalytics,
  getCampaigns, getTeamAnalytics, getSettings, updateSettings, getLeadSourceROI,
  getLeads, getContactsList, getCallsList, getTasksByTeamMember, getMeetingsByTeamMember, getDeals
} from '../services/api';
import { LOAN_PRODUCTS } from '../constants/loanProducts';
import '../styles/Reports.css';

const REPORT_PERIODS = ['This Month', 'Last Month', 'Last Quarter', 'This Year'];
const ROLE_LABELS = { admin: 'Admin', team_lead: 'Team Leader', location_head: 'Location Head', business_manager: 'Business Manager', employee: 'Employee' };
const dealLabel = (deal) => {
  const productInfo = LOAN_PRODUCTS.find((p) => p.id === deal.loan_product);
  return `${productInfo?.name || deal.loan_product} · ₹${(deal.deal_value || 0).toLocaleString('en-IN')}`;
};

export default function Reports() {
  const [activeTab, setActiveTab] = useState('sales');
  const [salesData, setSalesData] = useState(null);
  const [contactsData, setContactsData] = useState(null);
  const [callsData, setCallsData] = useState(null);
  const [campaigns, setCampaigns] = useState([]);
  const [teamStats, setTeamStats] = useState([]);
  const [leadSources, setLeadSources] = useState([]);
  const [reportPeriod, setReportPeriod] = useState('This Month');
  const [showSettings, setShowSettings] = useState(false);
  const [savingSettings, setSavingSettings] = useState(false);
  const token = localStorage.getItem('token');

  // Drill-down: Lead Source ROI row -> the actual leads from that source
  const [expandedSource, setExpandedSource] = useState(null);
  const [sourceLeads, setSourceLeads] = useState([]);
  const [loadingSourceLeads, setLoadingSourceLeads] = useState(false);

  // Drill-down: Team Productivity row -> that member's actual leads + contacts
  const [expandedMemberId, setExpandedMemberId] = useState(null);
  const [memberLeads, setMemberLeads] = useState([]);
  const [memberContacts, setMemberContacts] = useState([]);
  const [memberCalls, setMemberCalls] = useState([]);
  const [memberTasks, setMemberTasks] = useState([]);
  const [memberMeetings, setMemberMeetings] = useState([]);
  const [memberDeals, setMemberDeals] = useState([]);
  const [loadingMemberDrilldown, setLoadingMemberDrilldown] = useState(false);

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
    getLeadSourceROI(token)
      .then((data) => setLeadSources(Array.isArray(data) ? data : []))
      .catch((error) => console.error('Error fetching lead source ROI:', error));
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

  const toggleSourceExpand = async (source) => {
    if (expandedSource === source) {
      setExpandedSource(null);
      return;
    }
    setExpandedSource(source);
    setLoadingSourceLeads(true);
    try {
      const data = await getLeads(token, null, { source });
      setSourceLeads(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching leads for source drill-down:', error);
      setSourceLeads([]);
    } finally {
      setLoadingSourceLeads(false);
    }
  };

  const toggleMemberExpand = async (member) => {
    if (expandedMemberId === member.id) {
      setExpandedMemberId(null);
      return;
    }
    setExpandedMemberId(member.id);
    setLoadingMemberDrilldown(true);
    try {
      const [leadsData, contactsData, callsData, tasksData, meetingsData, dealsData] = await Promise.all([
        getLeads(token, null, { assignedTeamMemberId: member.id }),
        getContactsList(token, { assignedTeamMemberId: member.id }),
        getCallsList(token, { teamMemberId: member.id }),
        getTasksByTeamMember(token, member.id),
        getMeetingsByTeamMember(token, member.id),
        getDeals(token, 'closed', { assignedTeamMemberId: member.id }),
      ]);
      setMemberLeads(Array.isArray(leadsData) ? leadsData : []);
      setMemberContacts(Array.isArray(contactsData) ? contactsData : []);
      setMemberCalls(Array.isArray(callsData) ? callsData : []);
      setMemberTasks(Array.isArray(tasksData) ? tasksData : []);
      setMemberMeetings(Array.isArray(meetingsData) ? meetingsData : []);
      setMemberDeals(Array.isArray(dealsData) ? dealsData : []);
    } catch (error) {
      console.error('Error fetching drill-down data for team member:', error);
      setMemberLeads([]);
      setMemberContacts([]);
      setMemberCalls([]);
      setMemberTasks([]);
      setMemberMeetings([]);
      setMemberDeals([]);
    } finally {
      setLoadingMemberDrilldown(false);
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

  const csvEscape = (field) => `"${String(field).replace(/"/g, '""')}"`;

  const handleExportReport = () => {
    const lines = [];
    const tabLabel = reportTabs.find((t) => t.id === activeTab)?.label || 'Sales';

    lines.push(csvEscape(`${tabLabel} Report - ${reportPeriod}`));
    lines.push('');
    lines.push('Metric,Value');
    getMetrics().forEach((m) => lines.push(`${csvEscape(m.label)},${csvEscape(m.value)}`));
    lines.push('');

    lines.push('Lead Source ROI');
    lines.push('Source,Leads,Converted to Deal,Conversion Rate,Pipeline Value,Closed Value');
    leadSources.forEach((s) => lines.push([
      csvEscape(s.source), csvEscape(s.total_leads), csvEscape(s.total_deals), csvEscape(`${s.conversion_rate}%`),
      csvEscape(s.total_deal_value), csvEscape(s.closed_deal_value)
    ].join(',')));
    lines.push('');

    lines.push('Team Productivity');
    lines.push('Team Member,Role,Calls,Deals Closed,Revenue,Conversion Rate,Tasks Completed,Meetings Conducted');
    teamStats.forEach((m) => lines.push([
      csvEscape(m.name), csvEscape(ROLE_LABELS[m.role] || m.role),
      csvEscape(fmtStat(m.calls)), csvEscape(fmtStat(m.deals_closed)), csvEscape(fmtStat(m.revenue, true)),
      csvEscape(m.conversion_rate == null ? '—' : `${m.conversion_rate}%`),
      csvEscape(fmtStat(m.tasks_completed)), csvEscape(fmtStat(m.meetings_conducted))
    ].join(',')));
    lines.push('');

    lines.push('Campaign Performance');
    lines.push('Campaign,Recipients,Opens,Clicks');
    campaigns.forEach((c) => lines.push([csvEscape(c.name), csvEscape(c.recipients), csvEscape(c.opens), csvEscape(c.clicks)].join(',')));

    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${tabLabel.toLowerCase()}-report-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="reports-container">
      <div className="reports-header">
        <h1>Reports</h1>
        <div className="reports-header-actions">
          <button className="btn-secondary" onClick={() => setShowSettings(true)}>⚙️ Report Settings</button>
          <button className="btn-primary" onClick={handleExportReport}>📊 Export Report</button>
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
        <h3>Lead Source ROI</h3>
        <p className="lead-source-note">
          Conversion and pipeline value by lead source - not cost-adjusted ROI, since nothing
          in the CRM tracks what a source actually costs (ad spend, portal fee, referral payout).
        </p>
        {leadSources.length === 0 ? (
          <p className="placeholder">No leads yet.</p>
        ) : (
          <div className="team-productivity-table-wrapper">
            <table className="team-productivity-table">
              <thead>
                <tr>
                  <th></th>
                  <th>Source</th>
                  <th>Leads</th>
                  <th>Converted to Deal</th>
                  <th>Conversion Rate</th>
                  <th>Pipeline Value</th>
                  <th>Closed Value</th>
                </tr>
              </thead>
              <tbody>
                {leadSources.map((s) => (
                  <React.Fragment key={s.source}>
                    <tr className="drilldown-row" onClick={() => toggleSourceExpand(s.source)}>
                      <td>
                        <span className={`expand-arrow ${expandedSource === s.source ? 'open' : ''}`}>▸</span>
                      </td>
                      <td>{s.source}</td>
                      <td>{s.total_leads}</td>
                      <td>{s.total_deals}</td>
                      <td>{s.conversion_rate}%</td>
                      <td>₹{Number(s.total_deal_value).toLocaleString('en-IN')}</td>
                      <td>₹{Number(s.closed_deal_value).toLocaleString('en-IN')}</td>
                    </tr>
                    {expandedSource === s.source && (
                      <tr className="drilldown-detail-row">
                        <td></td>
                        <td colSpan="6">
                          {loadingSourceLeads ? (
                            <span className="no-data-inline">Loading…</span>
                          ) : sourceLeads.length === 0 ? (
                            <span className="no-data-inline">No leads found for this source.</span>
                          ) : (
                            <ul className="drilldown-list">
                              {sourceLeads.map((lead) => (
                                <li key={lead.id}>
                                  <strong>{lead.name}</strong>
                                  <span className={`drilldown-status status-${(lead.status || '').toLowerCase().replace(/\s+/g, '-')}`}>{lead.status}</span>
                                  {lead.phone && <span> · {lead.phone}</span>}
                                </li>
                              ))}
                            </ul>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
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
                  <th></th>
                  <th>Team Member</th>
                  <th>Role</th>
                  <th>Calls</th>
                  <th>Deals Closed</th>
                  <th>Revenue</th>
                  <th>Conversion Rate</th>
                  <th>Tasks Completed</th>
                  <th>Meetings Conducted</th>
                </tr>
              </thead>
              <tbody>
                {teamStats.map((m) => (
                  <React.Fragment key={m.id}>
                    <tr className="drilldown-row" onClick={() => toggleMemberExpand(m)}>
                      <td>
                        <span className={`expand-arrow ${expandedMemberId === m.id ? 'open' : ''}`}>▸</span>
                      </td>
                      <td>{m.name}</td>
                      <td>{ROLE_LABELS[m.role] || m.role}</td>
                      <td>{fmtStat(m.calls)}</td>
                      <td>{fmtStat(m.deals_closed)}</td>
                      <td>{fmtStat(m.revenue, true)}</td>
                      <td>{m.conversion_rate === null || m.conversion_rate === undefined ? '—' : `${m.conversion_rate}%`}</td>
                      <td>{fmtStat(m.tasks_completed)}</td>
                      <td>{fmtStat(m.meetings_conducted)}</td>
                    </tr>
                    {expandedMemberId === m.id && (
                      <tr className="drilldown-detail-row">
                        <td></td>
                        <td colSpan="8">
                          {loadingMemberDrilldown ? (
                            <span className="no-data-inline">Loading…</span>
                          ) : (
                            <div className="drilldown-groups">
                              <div className="drilldown-group">
                                <h4>Leads ({memberLeads.length})</h4>
                                {memberLeads.length === 0 ? (
                                  <span className="no-data-inline">No leads assigned to {m.name}.</span>
                                ) : (
                                  <ul className="drilldown-list">
                                    {memberLeads.map((lead) => (
                                      <li key={lead.id}>
                                        <strong>{lead.name}</strong>
                                        <span className={`drilldown-status status-${(lead.status || '').toLowerCase().replace(/\s+/g, '-')}`}>{lead.status}</span>
                                      </li>
                                    ))}
                                  </ul>
                                )}
                              </div>
                              <div className="drilldown-group">
                                <h4>Contacts ({memberContacts.length})</h4>
                                {memberContacts.length === 0 ? (
                                  <span className="no-data-inline">No contacts assigned to {m.name}.</span>
                                ) : (
                                  <ul className="drilldown-list">
                                    {memberContacts.map((contact) => (
                                      <li key={contact.id}>
                                        <strong>{contact.name}</strong>
                                        {contact.phone && <span> · {contact.phone}</span>}
                                      </li>
                                    ))}
                                  </ul>
                                )}
                              </div>
                              <div className="drilldown-group">
                                <h4>Calls ({memberCalls.length})</h4>
                                {memberCalls.length === 0 ? (
                                  <span className="no-data-inline">No calls logged by {m.name}.</span>
                                ) : (
                                  <ul className="drilldown-list">
                                    {memberCalls.map((call) => (
                                      <li key={call.id}>
                                        <strong>{call.lead_name || call.contact_name || call.name || 'Unknown'}</strong>
                                        <span className="drilldown-status">{call.outcome || 'No outcome'}</span>
                                      </li>
                                    ))}
                                  </ul>
                                )}
                              </div>
                              <div className="drilldown-group">
                                <h4>Tasks Completed ({memberTasks.filter((t) => t.completed).length})</h4>
                                {memberTasks.filter((t) => t.completed).length === 0 ? (
                                  <span className="no-data-inline">No completed tasks for {m.name}.</span>
                                ) : (
                                  <ul className="drilldown-list">
                                    {memberTasks.filter((t) => t.completed).map((task) => (
                                      <li key={task.id}>
                                        <strong>{task.title}</strong>
                                        <span> · due {task.due_date}</span>
                                      </li>
                                    ))}
                                  </ul>
                                )}
                              </div>
                              <div className="drilldown-group">
                                <h4>Meetings Conducted ({memberMeetings.filter((mt) => mt.status === 'Conducted').length})</h4>
                                {memberMeetings.filter((mt) => mt.status === 'Conducted').length === 0 ? (
                                  <span className="no-data-inline">No conducted meetings for {m.name}.</span>
                                ) : (
                                  <ul className="drilldown-list">
                                    {memberMeetings.filter((mt) => mt.status === 'Conducted').map((meeting) => (
                                      <li key={meeting.id}>
                                        <strong>{meeting.title}</strong>
                                        <span> · {meeting.meeting_date}</span>
                                      </li>
                                    ))}
                                  </ul>
                                )}
                              </div>
                              <div className="drilldown-group">
                                <h4>Deals Closed ({memberDeals.length})</h4>
                                {memberDeals.length === 0 ? (
                                  <span className="no-data-inline">No closed deals for {m.name}.</span>
                                ) : (
                                  <ul className="drilldown-list">
                                    {memberDeals.map((deal) => (
                                      <li key={deal.id}>
                                        <strong>{dealLabel(deal)}</strong>
                                        {deal.company_name && <span> · {deal.company_name}</span>}
                                      </li>
                                    ))}
                                  </ul>
                                )}
                              </div>
                            </div>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
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
