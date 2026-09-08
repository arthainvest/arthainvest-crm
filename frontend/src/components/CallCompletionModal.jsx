import React, { useState } from 'react';
import { completeCall, uploadCallRecording } from '../services/api';
import '../styles/CallCompletionModal.css';

const STATUS_OPTIONS = [
  { value: 'completed', label: 'Completed' },
  { value: 'no_answer', label: 'No Answer' },
  { value: 'busy', label: 'Busy' },
  { value: 'failed', label: 'Failed' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'unknown', label: 'Unknown' },
];

const OUTCOME_OPTIONS = [
  'Interested', 'Not Interested', 'Meeting Scheduled', 'Follow-up Needed',
];

// Shown after every click-to-call dial (see Contacts.jsx/LeadsList.jsx's handleCall) - fills
// in what happened on the SAME call record dial_call already created as status='initiated',
// rather than creating a second call for one dial attempt.
export default function CallCompletionModal({ token, callId, customerName, onClose, onSaved }) {
  const [status, setStatus] = useState('completed');
  const [minutes, setMinutes] = useState('');
  const [seconds, setSeconds] = useState('');
  const [outcome, setOutcome] = useState('');
  const [notes, setNotes] = useState('');
  const [followUpDate, setFollowUpDate] = useState('');
  const [recordingFile, setRecordingFile] = useState(null);
  const [saving, setSaving] = useState(false);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const durationSeconds = (Number(minutes) || 0) * 60 + (Number(seconds) || 0);
      await completeCall(token, callId, {
        status,
        duration_seconds: durationSeconds,
        outcome: status === 'completed' ? (outcome || null) : null,
        notes: notes || null,
        follow_up_date: followUpDate || null,
      });
      if (recordingFile) {
        await uploadCallRecording(token, callId, recordingFile);
      }
      onSaved();
    } catch (error) {
      console.error('Error completing call:', error);
      alert(error?.response?.data?.detail || 'Failed to save call outcome. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content call-completion-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Complete Call{customerName ? ` — ${customerName}` : ''}</h2>
          <button className="btn-close" onClick={onClose}>×</button>
        </div>
        <form onSubmit={handleSave}>
          <div className="modal-body">
            <p className="call-completion-hint">
              This is not automatically recorded — a phone dialer call can't be captured by the server.
              Log what happened below.
            </p>
            <div className="form-group">
              <label>Call Status</label>
              <select value={status} onChange={(e) => setStatus(e.target.value)}>
                {STATUS_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Minutes</label>
                <input type="number" min="0" value={minutes} onChange={(e) => setMinutes(e.target.value)} />
              </div>
              <div className="form-group">
                <label>Seconds</label>
                <input type="number" min="0" max="59" value={seconds} onChange={(e) => setSeconds(e.target.value)} />
              </div>
            </div>
            {status === 'completed' && (
              <div className="form-group">
                <label>Outcome</label>
                <select value={outcome} onChange={(e) => setOutcome(e.target.value)}>
                  <option value="">-- Select --</option>
                  {OUTCOME_OPTIONS.map((o) => <option key={o} value={o}>{o}</option>)}
                </select>
              </div>
            )}
            <div className="form-group">
              <label>Notes</label>
              <textarea rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="What did the customer say?" />
            </div>
            <div className="form-group">
              <label>Follow-up Date</label>
              <input type="date" value={followUpDate} onChange={(e) => setFollowUpDate(e.target.value)} />
            </div>
            <div className="form-group">
              <label>Recording (optional — upload if your phone recorded it)</label>
              <input type="file" accept="audio/*" onChange={(e) => setRecordingFile(e.target.files?.[0] || null)} />
            </div>
          </div>
          <div className="modal-actions">
            <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
            <button type="button" className="btn-secondary" onClick={onClose} disabled={saving}>Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
}
