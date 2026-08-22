import React, { useState, useEffect } from 'react';
import { getCallsList, createCall, deleteCall } from '../services/api';
import '../styles/Calls.css';

const emptyCallForm = { name: '', phone: '', minutes: '', seconds: '', type: 'Outbound', outcome: '', call_date: new Date().toISOString().slice(0, 10) };

export default function Calls() {
  const [calls, setCalls] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [callForm, setCallForm] = useState(emptyCallForm);
  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchCalls();
  }, []);

  const fetchCalls = async () => {
    try {
      const data = await getCallsList(token);
      setCalls(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching calls:', error);
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
    setCallForm(emptyCallForm);
    setShowForm(true);
  };

  const handleSaveCall = async (e) => {
    e.preventDefault();
    if (!callForm.name.trim()) return;

    const duration_seconds = (Number(callForm.minutes) || 0) * 60 + (Number(callForm.seconds) || 0);

    try {
      await createCall(token, {
        name: callForm.name,
        phone: callForm.phone,
        duration_seconds,
        type: callForm.type,
        outcome: callForm.outcome,
        call_date: callForm.call_date
      });
      setShowForm(false);
      setCallForm(emptyCallForm);
      fetchCalls();
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
    } catch (error) {
      console.error('Error deleting call:', error);
      alert('Failed to delete call. Please try again.');
    }
  };

  return (
    <div className="calls-container">
      <div className="calls-header">
        <h1>Calls</h1>
        <button className="btn-primary" onClick={handleLogCallClick}>+ Log Call</button>
      </div>

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

      <div className="calls-table">
        <table>
          <thead>
            <tr>
              <th>Contact</th>
              <th>Phone</th>
              <th>Duration</th>
              <th>Type</th>
              <th>Outcome</th>
              <th>Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {calls.length === 0 ? (
              <tr><td colSpan="7" className="no-data">No calls logged yet.</td></tr>
            ) : calls.map(call => (
              <tr key={call.id}>
                <td><strong>{call.name}</strong></td>
                <td>{call.phone}</td>
                <td>{call.duration}</td>
                <td><span className={`badge-${(call.type || '').toLowerCase()}`}>{call.type || 'Unknown'}</span></td>
                <td>{call.outcome || '-'}</td>
                <td>{call.call_date}</td>
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
                      onChange={(e) => setCallForm({ ...callForm, seconds: e.target.value })}
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
              </div>
              <div className="modal-actions">
                <button type="submit" className="btn-primary">Save Call</button>
                <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
