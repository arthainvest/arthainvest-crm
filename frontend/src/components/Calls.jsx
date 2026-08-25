import React, { useState, useEffect } from 'react';
import {
  getCallsList, createCall, deleteCall, assignCall, getTeam, getCallsByEmployee, getCommunicationLog,
  getActivities, getDialerQueue, updateDialerStatus, deleteDialerItem, getLeads, getContactsList
} from '../services/api';
import '../styles/Calls.css';

const emptyCallForm = { name: '', phone: '', minutes: '', seconds: '', type: 'Outbound', outcome: '', call_date: '', team_member_id: '', linkTo: '' };

// Grouped together like Kylas groups Call Logs/Emails/WhatsApp under one nav item - Calls
// stays the real, feature-rich page; Emails/WhatsApp are read-only send-history log views.
const LOG_TABS = [
  { id: 'calls', label: '📞 Calls', title: 'Calls' },
  { id: 'emails', label: '✉️ Emails', title: 'Emails' },
  { id: 'whatsapp', label: '💬 WhatsApp', title: 'WhatsApp' },
  { id: 'activities', label: '🔔 Activities', title: 'Activities' },
  { id: 'dialer', label: '🎯 Dialer', title: 'My Call Dialer' },
];

const ACTIVITY_CHANNELS = ['All', 'Call', 'Email', 'WhatsApp', 'SMS'];

export default function Calls() {
  const [activeTab, setActiveTab] = useState('calls');
  const [calls, setCalls] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [callForm, setCallForm] = useState(emptyCallForm);
  const [teamMembers, setTeamMembers] = useState([]);
  const [employeeStats, setEmployeeStats] = useState([]);
  const [emailLog, setEmailLog] = useState([]);
  const [whatsappLog, setWhatsappLog] = useState([]);
  const [activities, setActivities] = useState([]);
  const [activityChannel, setActivityChannel] = useState('All');
  const [dialerTeamMemberId, setDialerTeamMemberId] = useState('');
  const [dialerQueue, setDialerQueue] = useState([]);
  const [dialerLoading, setDialerLoading] = useState(false);
  const [leads, setLeads] = useState([]);
  const [contacts, setContacts] = useState([]);
  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchCalls();
    fetchTeamMembers();
    fetchEmployeeStats();
    fetchEmailLog();
    fetchWhatsappLog();
    fetchActivities('All');
    fetchLeadsAndContacts();
  }, []);

  const fetchLeadsAndContacts = async () => {
    try {
      const [leadsData, contactsData] = await Promise.all([getLeads(token), getContactsList(token)]);
      setLeads(Array.isArray(leadsData) ? leadsData : []);
      setContacts(Array.isArray(contactsData) ? contactsData : []);
    } catch (error) {
      console.error('Error fetching leads/contacts for call linking:', error);
    }
  };

  // Default the Dialer tab to the first team member once the roster loads
  useEffect(() => {
    if (!dialerTeamMemberId && teamMembers.length > 0) {
      setDialerTeamMemberId(String(teamMembers[0].id));
    }
  }, [teamMembers, dialerTeamMemberId]);

  useEffect(() => {
    if (activeTab === 'dialer' && dialerTeamMemberId) {
      fetchDialerQueue(dialerTeamMemberId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, dialerTeamMemberId]);

  const fetchActivities = async (channel) => {
    try {
      const data = await getActivities(token, channel === 'All' ? null : channel);
      setActivities(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching activities:', error);
    }
  };

  const handleActivityChannelChange = (channel) => {
    setActivityChannel(channel);
    fetchActivities(channel);
  };

  const fetchDialerQueue = async (teamMemberId) => {
    setDialerLoading(true);
    try {
      const data = await getDialerQueue(token, teamMemberId);
      setDialerQueue(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching dial queue:', error);
    } finally {
      setDialerLoading(false);
    }
  };

  const handleDialerCall = (item) => {
    if (item.phone) window.location.href = `tel:${item.phone}`;
  };

  const handleDialerMark = async (item, status) => {
    try {
      await updateDialerStatus(token, item.id, status);
      setDialerQueue((prev) => prev.filter((q) => q.id !== item.id));
    } catch (error) {
      console.error('Error updating dial queue item:', error);
      alert('Failed to update. Please try again.');
    }
  };

  const handleDialerRemove = async (item) => {
    try {
      await deleteDialerItem(token, item.id);
      setDialerQueue((prev) => prev.filter((q) => q.id !== item.id));
    } catch (error) {
      console.error('Error removing dial queue item:', error);
      alert('Failed to remove. Please try again.');
    }
  };

  const fetchEmailLog = async () => {
    try {
      const data = await getCommunicationLog(token, 'Email');
      setEmailLog(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching email log:', error);
    }
  };

  const fetchWhatsappLog = async () => {
    try {
      const data = await getCommunicationLog(token, 'WhatsApp');
      setWhatsappLog(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching WhatsApp log:', error);
    }
  };

  const fetchCalls = async () => {
    try {
      const data = await getCallsList(token);
      setCalls(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching calls:', error);
    }
  };

  const fetchTeamMembers = async () => {
    try {
      const data = await getTeam(token);
      setTeamMembers(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching team members:', error);
    }
  };

  const fetchEmployeeStats = async () => {
    try {
      const data = await getCallsByEmployee(token);
      setEmployeeStats(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching per-employee call stats:', error);
    }
  };

  const handleAssignChange = async (callId, teamMemberIdRaw) => {
    const teamMemberId = teamMemberIdRaw ? Number(teamMemberIdRaw) : null;
    const previous = calls.find((c) => c.id === callId);
    setCalls((prev) => prev.map((c) => (c.id === callId
      ? { ...c, team_member_id: teamMemberId, team_member_name: teamMembers.find((m) => m.id === teamMemberId)?.name || null }
      : c)));
    try {
      await assignCall(token, callId, teamMemberId);
      fetchEmployeeStats();
    } catch (error) {
      console.error('Error assigning call:', error);
      if (previous) {
        setCalls((prev) => prev.map((c) => (c.id === callId ? previous : c)));
      }
      alert('Failed to assign call. Please try again.');
    }
  };

  const stats = {
    totalCalls: calls.length,
    inbound: calls.filter(c => c.type === 'Inbound').length,
    outbound: calls.filter(c => c.type === 'Outbound').length,
    avgDuration: calls.length > 0
      ? formatSeconds(Math.round(calls.reduce((sum, c) => sum + (c.duration_seconds || 0), 0) / calls.length))
      : '0m 0s'
  };

  function formatSeconds(total) {
    const m = Math.floor(total / 60);
    const s = total % 60;
    return `${m}m ${s}s`;
  }

  const handleLogCallClick = () => {
    setCallForm({ ...emptyCallForm, call_date: new Date().toISOString().slice(0, 10) });
    setShowForm(true);
  };

  const handleSaveCall = async (e) => {
    e.preventDefault();
    if (!callForm.name.trim()) return;

    const duration_seconds = (Number(callForm.minutes) || 0) * 60 + (Number(callForm.seconds) || 0);
    const [linkType, linkId] = callForm.linkTo ? callForm.linkTo.split('-') : [null, null];

    try {
      await createCall(token, {
        name: callForm.name,
        phone: callForm.phone,
        duration_seconds,
        type: callForm.type,
        outcome: callForm.outcome,
        call_date: callForm.call_date,
        team_member_id: callForm.team_member_id ? Number(callForm.team_member_id) : null,
        lead_id: linkType === 'lead' ? Number(linkId) : null,
        contact_id: linkType === 'contact' ? Number(linkId) : null
      });
      setShowForm(false);
      setCallForm(emptyCallForm);
      fetchCalls();
      fetchEmployeeStats();
    } catch (error) {
      console.error('Error logging call:', error);
      alert('Failed to log call. Please try again.');
    }
  };

  const handleDeleteCall = async (id) => {
    if (!window.confirm('Delete this call log?')) return;
    try {
      await deleteCall(token, id);
      setCalls((prev) => prev.filter((c) => c.id !== id));
      fetchEmployeeStats();
    } catch (error) {
      console.error('Error deleting call:', error);
      alert('Failed to delete call. Please try again.');
    }
  };

  return (
    <div className="calls-container">
      <div className="calls-header">
        <h1>{LOG_TABS.find((t) => t.id === activeTab)?.title || 'Calls'}</h1>
        {activeTab === 'calls' && (
          <button className="btn-primary" onClick={handleLogCallClick}>+ Log Call</button>
        )}
      </div>

      <div className="log-tab-navigation">
        {LOG_TABS.map((tab) => (
          <button
            key={tab.id}
            className={`log-tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'emails' && (
        <div className="calls-table">
          <table>
            <thead>
              <tr>
                <th>To</th>
                <th>Subject</th>
                <th>Status</th>
                <th>Sent</th>
              </tr>
            </thead>
            <tbody>
              {emailLog.length === 0 ? (
                <tr><td colSpan="4" className="no-data">No emails sent yet - use the Email button on Contacts/Leads, or a Renewal Reminder.</td></tr>
              ) : emailLog.map((entry) => (
                <tr key={entry.id}>
                  <td>{entry.recipient}</td>
                  <td>{entry.subject || '-'}</td>
                  <td><span className={`badge-${entry.status.toLowerCase()}`}>{entry.status}</span></td>
                  <td>{new Date(entry.created_at).toLocaleString('en-IN')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'whatsapp' && (
        <div className="calls-table">
          <table>
            <thead>
              <tr>
                <th>To</th>
                <th>Message</th>
                <th>Status</th>
                <th>Sent</th>
              </tr>
            </thead>
            <tbody>
              {whatsappLog.length === 0 ? (
                <tr><td colSpan="4" className="no-data">No WhatsApp messages sent yet via the WhatsApp Business API - only real API sends are logged here, not wa.me link fallbacks (the browser handles those, so this server never sees them).</td></tr>
              ) : whatsappLog.map((entry) => (
                <tr key={entry.id}>
                  <td>{entry.recipient}</td>
                  <td className="log-message-cell">{entry.message}</td>
                  <td><span className={`badge-${entry.status.toLowerCase()}`}>{entry.status}</span></td>
                  <td>{new Date(entry.created_at).toLocaleString('en-IN')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'activities' && (
        <div className="calls-table">
          <div className="activity-channel-filter">
            {ACTIVITY_CHANNELS.map((ch) => (
              <button
                key={ch}
                type="button"
                className={`log-tab-btn ${activityChannel === ch ? 'active' : ''}`}
                onClick={() => handleActivityChannelChange(ch)}
              >
                {ch}
              </button>
            ))}
          </div>
          <table>
            <thead>
              <tr>
                <th>Channel</th>
                <th>Contact</th>
                <th>Linked To</th>
                <th>Detail</th>
                <th>Outcome</th>
                <th>When</th>
              </tr>
            </thead>
            <tbody>
              {activities.length === 0 ? (
                <tr><td colSpan="6" className="no-data">No activity yet across calls, email, WhatsApp or SMS.</td></tr>
              ) : activities.map((a) => (
                <tr key={a.id}>
                  <td><span className={`badge-${a.channel.toLowerCase()}`}>{a.channel}</span></td>
                  <td>{a.contact || '-'}</td>
                  <td>
                    {a.lead_name ? `📈 ${a.lead_name}` : a.contact_name ? `👥 ${a.contact_name}` : '-'}
                  </td>
                  <td className="log-message-cell">{a.detail || '-'}</td>
                  <td>{a.outcome || '-'}</td>
                  <td>{new Date(a.timestamp).toLocaleString('en-IN')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'dialer' && (
        <div className="dialer-tab">
          <div className="form-group dialer-member-select">
            <label>Dial Queue For</label>
            <select value={dialerTeamMemberId} onChange={(e) => setDialerTeamMemberId(e.target.value)}>
              {teamMembers.map((m) => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </select>
            <span className="dialer-remaining">{dialerQueue.length} pending</span>
          </div>

          {dialerLoading ? (
            <p className="no-data">Loading queue…</p>
          ) : dialerQueue.length === 0 ? (
            <p className="no-data">No leads/contacts queued for this team member. Select leads on the Leads page and use "Assign to Dialer".</p>
          ) : (
            <div className="calls-table">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Phone</th>
                    <th>Source</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {dialerQueue.map((item) => (
                    <tr key={item.id}>
                      <td><strong>{item.name}</strong></td>
                      <td>{item.phone || '-'}</td>
                      <td>{item.lead_id ? 'Lead' : 'Contact'}</td>
                      <td className="dialer-actions">
                        <button className="btn-small" onClick={() => handleDialerCall(item)} title="Call">📞 Call</button>
                        <button className="btn-small" onClick={() => handleDialerMark(item, 'Called')} title="Mark Called">✅ Called</button>
                        <button className="btn-small" onClick={() => handleDialerMark(item, 'Skipped')} title="Skip">⏭️ Skip</button>
                        <button className="btn-small delete" onClick={() => handleDialerRemove(item)} title="Remove from queue">🗑️</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === 'calls' && (
      <>
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{stats.totalCalls}</div>
          <div className="stat-label">Total Calls</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.inbound}</div>
          <div className="stat-label">Inbound</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.outbound}</div>
          <div className="stat-label">Outbound</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.avgDuration}</div>
          <div className="stat-label">Avg Duration</div>
        </div>
      </div>

      {teamMembers.length > 0 && (
        <div className="employee-call-report">
          <h3>Calls by Employee</h3>
          <div className="calls-table">
            <table>
              <thead>
                <tr>
                  <th>Employee</th>
                  <th>Today Attempted</th>
                  <th>Today Connected</th>
                  <th>This Week Attempted</th>
                  <th>This Week Connected</th>
                  <th>This Month Attempted</th>
                  <th>This Month Connected</th>
                </tr>
              </thead>
              <tbody>
                {employeeStats.length === 0 ? (
                  <tr><td colSpan="7" className="no-data">No team members yet.</td></tr>
                ) : employeeStats.map((s) => (
                  <tr key={s.team_member_id}>
                    <td><strong>{s.name}</strong></td>
                    <td>{s.today_attempted}</td>
                    <td>{s.today_connected}</td>
                    <td>{s.week_attempted}</td>
                    <td>{s.week_connected}</td>
                    <td>{s.month_attempted}</td>
                    <td>{s.month_connected}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="calls-table">
        <table>
          <thead>
            <tr>
              <th>Contact</th>
              <th>Phone</th>
              <th>Linked To</th>
              <th>Duration</th>
              <th>Type</th>
              <th>Outcome</th>
              <th>Date</th>
              <th>Employee</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {calls.length === 0 ? (
              <tr><td colSpan="9" className="no-data">No calls logged yet.</td></tr>
            ) : calls.map(call => (
              <tr key={call.id}>
                <td><strong>{call.name}</strong></td>
                <td>{call.phone}</td>
                <td>
                  {call.lead_name ? `📈 ${call.lead_name}` : call.contact_name ? `👥 ${call.contact_name}` : '-'}
                </td>
                <td>{call.duration}</td>
                <td><span className={`badge-${(call.type || '').toLowerCase()}`}>{call.type || 'Unknown'}</span></td>
                <td>{call.outcome || '-'}</td>
                <td>{call.call_date}</td>
                <td>
                  <select
                    className="employee-assign-select"
                    value={call.team_member_id || ''}
                    onChange={(e) => handleAssignChange(call.id, e.target.value)}
                    title="Employee who made/handled this call"
                  >
                    <option value="">Unassigned</option>
                    {teamMembers.map((m) => (
                      <option key={m.id} value={m.id}>{m.name}</option>
                    ))}
                  </select>
                </td>
                <td>
                  <button className="btn-small delete" onClick={() => handleDeleteCall(call.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Log Call</h2>
              <button className="btn-close" onClick={() => setShowForm(false)}>×</button>
            </div>

            <form onSubmit={handleSaveCall}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Contact Name *</label>
                  <input
                    type="text"
                    required
                    value={callForm.name}
                    onChange={(e) => setCallForm({ ...callForm, name: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Phone</label>
                  <input
                    type="tel"
                    value={callForm.phone}
                    onChange={(e) => setCallForm({ ...callForm, phone: e.target.value })}
                  />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Duration (minutes)</label>
                    <input
                      type="number"
                      min="0"
                      value={callForm.minutes}
                      onChange={(e) => setCallForm({ ...callForm, minutes: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Duration (seconds)</label>
                    <input
                      type="number"
                      min="0"
                      max="59"
                      value={callForm.seconds}
                      onChange={(e) => {
                        const raw = e.target.value;
                        const clamped = raw === '' ? '' : Math.min(59, Math.max(0, Number(raw) || 0));
                        setCallForm({ ...callForm, seconds: clamped });
                      }}
                    />
                  </div>
                </div>
                <div className="form-group">
                  <label>Type</label>
                  <select
                    value={callForm.type}
                    onChange={(e) => setCallForm({ ...callForm, type: e.target.value })}
                  >
                    <option value="Outbound">Outbound</option>
                    <option value="Inbound">Inbound</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Outcome</label>
                  <select
                    value={callForm.outcome}
                    onChange={(e) => setCallForm({ ...callForm, outcome: e.target.value })}
                  >
                    <option value="">-- Select --</option>
                    <option value="No Answer">No Answer (not connected)</option>
                    <option value="Not Connected">Not Connected / Busy</option>
                    <option value="Interested">Interested</option>
                    <option value="Not Interested">Not Interested</option>
                    <option value="Meeting Scheduled">Meeting Scheduled</option>
                    <option value="Follow-up Needed">Follow-up Needed</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Date</label>
                  <input
                    type="date"
                    value={callForm.call_date}
                    onChange={(e) => setCallForm({ ...callForm, call_date: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Made / Handled By</label>
                  <select
                    value={callForm.team_member_id}
                    onChange={(e) => setCallForm({ ...callForm, team_member_id: e.target.value })}
                  >
                    <option value="">-- Unassigned --</option>
                    {teamMembers.map((m) => (
                      <option key={m.id} value={m.id}>{m.name}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Link to Lead/Contact (optional)</label>
                  <select
                    value={callForm.linkTo}
                    onChange={(e) => setCallForm({ ...callForm, linkTo: e.target.value })}
                  >
                    <option value="">-- Not linked --</option>
                    {leads.length > 0 && (
                      <optgroup label="Leads">
                        {leads.map((l) => (
                          <option key={`lead-${l.id}`} value={`lead-${l.id}`}>{l.name}</option>
                        ))}
                      </optgroup>
                    )}
                    {contacts.length > 0 && (
                      <optgroup label="Contacts">
                        {contacts.map((c) => (
                          <option key={`contact-${c.id}`} value={`contact-${c.id}`}>{c.name}</option>
                        ))}
                      </optgroup>
                    )}
                  </select>
                </div>
              </div>
              <div className="modal-actions">
                <button type="submit" className="btn-primary">Save Call</button>
                <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
      </>
      )}
    </div>
  );
}
