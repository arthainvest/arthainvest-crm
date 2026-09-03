import React, { useState, useEffect, useCallback } from 'react';
import {
  getAutomations, createAutomation, updateAutomation, deleteAutomation,
  getAutomationEnrollments, enrollGroupInAutomation, stopAutomationEnrollment,
  getGroups, createGroup
} from '../services/api';
import '../styles/Automations.css';

const emptyStep = () => ({ wait_minutes: 0, message_type: 'text', template_name: '', body: '' });
const emptyForm = { name: '', trigger_type: 'manual', group_id: '', steps: [emptyStep()] };

const TRIGGER_LABELS = {
  manual: 'Manual / group broadcast',
  new_lead: 'New lead (recorded, not yet auto-fired)',
  group_join: 'Joins a group (recorded, not yet auto-fired)'
};

const ENROLLMENT_STATUS_LABEL = {
  active: 'Active', completed: 'Completed', stopped: 'Stopped'
};

function formatWait(minutes) {
  if (!minutes) return 'Immediately';
  if (minutes < 60) return `${minutes}m later`;
  if (minutes < 1440) return `${Math.round(minutes / 60)}h later`;
  return `${Math.round(minutes / 1440)}d later`;
}

function formatWhen(ts) {
  if (!ts) return '—';
  const d = new Date(ts.includes('T') ? ts : ts.replace(' ', 'T'));
  if (Number.isNaN(d.getTime())) return ts;
  return d.toLocaleString([], { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
}

export default function Automations() {
  const token = localStorage.getItem('token');

  const [automations, setAutomations] = useState([]);
  const [groups, setGroups] = useState([]);

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);

  const [showGroupForm, setShowGroupForm] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');

  const [enrollTargets, setEnrollTargets] = useState({}); // automationId -> selected group_id
  const [enrollBusy, setEnrollBusy] = useState(null);

  const [showEnrollments, setShowEnrollments] = useState(false);
  const [enrollmentsAutomation, setEnrollmentsAutomation] = useState(null);
  const [enrollments, setEnrollments] = useState([]);

  const [error, setError] = useState(null);

  const fetchAutomations = useCallback(async () => {
    try {
      const data = await getAutomations(token);
      setAutomations(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching automations:', err);
      setError('Failed to load automations.');
    }
  }, [token]);

  const fetchGroups = useCallback(async () => {
    try {
      const data = await getGroups(token);
      setGroups(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching groups:', err);
    }
  }, [token]);

  useEffect(() => {
    fetchAutomations();
    fetchGroups();
  }, [fetchAutomations, fetchGroups]);

  const handleNewClick = () => {
    setEditingId(null);
    setForm(emptyForm);
    setShowForm(true);
  };

  const handleEditClick = (automation) => {
    setEditingId(automation.id);
    setForm({
      name: automation.name,
      trigger_type: automation.trigger_type,
      group_id: automation.group_id || '',
      steps: automation.steps.length ? automation.steps.map((s) => ({
        wait_minutes: s.wait_minutes, message_type: s.message_type,
        template_name: s.template_name || '', body: s.body || ''
      })) : [emptyStep()]
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this automation? Anyone currently enrolled in it will stop receiving further steps.')) return;
    try {
      await deleteAutomation(token, id);
      fetchAutomations();
    } catch (err) {
      console.error('Error deleting automation:', err);
      alert('Failed to delete automation.');
    }
  };

  const handleToggleStatus = async (automation) => {
    try {
      await updateAutomation(token, automation.id, { status: automation.status === 'active' ? 'paused' : 'active' });
      fetchAutomations();
    } catch (err) {
      console.error('Error updating automation status:', err);
      alert('Failed to update automation status.');
    }
  };

  const handleStepChange = (index, field, value) => {
    setForm((prev) => {
      const steps = [...prev.steps];
      steps[index] = { ...steps[index], [field]: value };
      return { ...prev, steps };
    });
  };

  const addStep = () => setForm((prev) => ({ ...prev, steps: [...prev.steps, emptyStep()] }));

  const removeStep = (index) => setForm((prev) => ({ ...prev, steps: prev.steps.filter((_, i) => i !== index) }));

  const handleSave = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    if (form.steps.length === 0) {
      alert('Add at least one step.');
      return;
    }
    for (const step of form.steps) {
      if (step.message_type === 'text' && !step.body.trim()) {
        alert('Every text step needs a message body.');
        return;
      }
      if (step.message_type === 'template' && !step.template_name.trim()) {
        alert('Every template step needs a template name.');
        return;
      }
    }

    const payload = {
      name: form.name.trim(),
      trigger_type: form.trigger_type,
      group_id: form.group_id ? Number(form.group_id) : null,
      steps: form.steps.map((s) => ({
        wait_minutes: Number(s.wait_minutes) || 0,
        message_type: s.message_type,
        template_name: s.message_type === 'template' ? s.template_name.trim() : null,
        body: s.message_type === 'text' ? s.body.trim() : null
      }))
    };

    setSaving(true);
    try {
      if (editingId) {
        await updateAutomation(token, editingId, payload);
      } else {
        await createAutomation(token, payload);
      }
      setShowForm(false);
      setForm(emptyForm);
      setEditingId(null);
      fetchAutomations();
    } catch (err) {
      console.error('Error saving automation:', err);
      alert('Failed to save automation.');
    } finally {
      setSaving(false);
    }
  };

  const handleCreateGroup = async (e) => {
    e.preventDefault();
    if (!newGroupName.trim()) return;
    try {
      const group = await createGroup(token, { name: newGroupName.trim() });
      setNewGroupName('');
      setShowGroupForm(false);
      await fetchGroups();
      setForm((prev) => ({ ...prev, group_id: group.id }));
    } catch (err) {
      console.error('Error creating group:', err);
      alert('Failed to create group - the name may already be taken.');
    }
  };

  const handleEnrollGroup = async (automation) => {
    const groupId = enrollTargets[automation.id];
    if (!groupId) {
      alert('Choose a group to enroll first.');
      return;
    }
    setEnrollBusy(automation.id);
    try {
      const result = await enrollGroupInAutomation(token, automation.id, groupId);
      alert(result.message);
    } catch (err) {
      console.error('Error enrolling group:', err);
      alert('Failed to enroll group. Does this automation have any steps yet?');
    } finally {
      setEnrollBusy(null);
    }
  };

  const handleViewEnrollments = async (automation) => {
    setEnrollmentsAutomation(automation);
    setShowEnrollments(true);
    try {
      const data = await getAutomationEnrollments(token, automation.id);
      setEnrollments(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching enrollments:', err);
      setEnrollments([]);
    }
  };

  const handleStopEnrollment = async (enrollmentId) => {
    try {
      await stopAutomationEnrollment(token, enrollmentId);
      const data = await getAutomationEnrollments(token, enrollmentsAutomation.id);
      setEnrollments(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error stopping enrollment:', err);
      alert('Failed to stop enrollment.');
    }
  };

  return (
    <div className="automations-container">
      <div className="automations-header">
        <div>
          <h1>Automations</h1>
          <p className="automations-subtitle">Drip sequences that send a series of messages over time to a group of leads/contacts.</p>
        </div>
        <button className="btn-primary" onClick={handleNewClick}>+ New Automation</button>
      </div>

      {error && <div className="automations-error">{error}</div>}

      <div className="automations-list">
        {automations.length === 0 ? (
          <p className="no-data">No automations yet. Create one to start a drip sequence (e.g. a festival greeting followed by a follow-up).</p>
        ) : automations.map((automation) => (
          <div key={automation.id} className="automation-card">
            <div className="automation-card-header">
              <div>
                <h3>{automation.name}</h3>
                <span className="automation-trigger">{TRIGGER_LABELS[automation.trigger_type] || automation.trigger_type}</span>
              </div>
              <span className={`automation-status ${automation.status}`}>{automation.status === 'active' ? 'Active' : 'Paused'}</span>
            </div>

            <div className="automation-steps-preview">
              {automation.steps.map((step, i) => (
                <div key={step.id || i} className="automation-step-chip">
                  <span className="step-wait">{formatWait(step.wait_minutes)}</span>
                  <span className="step-body">
                    {step.message_type === 'template' ? `📄 ${step.template_name}` : (step.body || '').slice(0, 60)}
                  </span>
                </div>
              ))}
            </div>

            <div className="automation-card-actions">
              <button className="btn-secondary" onClick={() => handleEditClick(automation)}>Edit</button>
              <button className="btn-secondary" onClick={() => handleToggleStatus(automation)}>
                {automation.status === 'active' ? 'Pause' : 'Resume'}
              </button>
              <button className="btn-secondary" onClick={() => handleViewEnrollments(automation)}>Enrollments</button>
              <button className="btn-danger" onClick={() => handleDelete(automation.id)}>Delete</button>
            </div>

            <div className="automation-enroll-row">
              <select
                value={enrollTargets[automation.id] || ''}
                onChange={(e) => setEnrollTargets((prev) => ({ ...prev, [automation.id]: e.target.value }))}
              >
                <option value="">Choose a group to enroll...</option>
                {groups.map((g) => (
                  <option key={g.id} value={g.id}>{g.name}</option>
                ))}
              </select>
              <button
                className="btn-primary enroll-btn"
                onClick={() => handleEnrollGroup(automation)}
                disabled={enrollBusy === automation.id}
              >
                {enrollBusy === automation.id ? 'Enrolling...' : 'Enroll Group'}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Create / Edit automation modal */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content automation-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingId ? 'Edit Automation' : 'New Automation'}</h2>
              <button className="btn-close" onClick={() => setShowForm(false)}>&times;</button>
            </div>
            <form onSubmit={handleSave}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Diwali Greeting Sequence"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Trigger</label>
                    <select value={form.trigger_type} onChange={(e) => setForm({ ...form, trigger_type: e.target.value })}>
                      <option value="manual">Manual / group broadcast</option>
                      <option value="new_lead">New lead</option>
                      <option value="group_join">Joins a group</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Target group (optional)</label>
                    <div className="group-picker-row">
                      <select value={form.group_id} onChange={(e) => setForm({ ...form, group_id: e.target.value })}>
                        <option value="">None</option>
                        {groups.map((g) => (
                          <option key={g.id} value={g.id}>{g.name}</option>
                        ))}
                      </select>
                      <button type="button" className="btn-secondary small" onClick={() => setShowGroupForm(true)}>+ New</button>
                    </div>
                  </div>
                </div>

                {form.trigger_type !== 'manual' && (
                  <p className="automation-trigger-hint">
                    Note: this trigger is recorded for reference, but nothing auto-enrolls a lead/contact yet -
                    use "Enroll Group" on the automations list to actually start it for now.
                  </p>
                )}

                <div className="steps-builder">
                  <div className="steps-builder-header">
                    <label>Steps (sent in order)</label>
                    <button type="button" className="btn-secondary small" onClick={addStep}>+ Add Step</button>
                  </div>

                  {form.steps.map((step, index) => (
                    <div key={index} className="step-editor">
                      <div className="step-editor-header">
                        <span className="step-number">Step {index + 1}</span>
                        {form.steps.length > 1 && (
                          <button type="button" className="btn-remove-step" onClick={() => removeStep(index)}>Remove</button>
                        )}
                      </div>
                      <div className="form-row">
                        <div className="form-group">
                          <label>Wait (minutes {index === 0 ? 'before sending' : 'after previous step'})</label>
                          <input
                            type="number"
                            min="0"
                            value={step.wait_minutes}
                            onChange={(e) => handleStepChange(index, 'wait_minutes', e.target.value)}
                          />
                        </div>
                        <div className="form-group">
                          <label>Message type</label>
                          <select value={step.message_type} onChange={(e) => handleStepChange(index, 'message_type', e.target.value)}>
                            <option value="text">Freeform text</option>
                            <option value="template">Approved template</option>
                          </select>
                        </div>
                      </div>
                      {step.message_type === 'text' ? (
                        <div className="form-group">
                          <label>Message</label>
                          <textarea
                            rows="2"
                            placeholder="Happy Diwali! Wishing you prosperity this year..."
                            value={step.body}
                            onChange={(e) => handleStepChange(index, 'body', e.target.value)}
                          />
                        </div>
                      ) : (
                        <div className="form-group">
                          <label>Template name</label>
                          <input
                            type="text"
                            placeholder="e.g. diwali_greeting"
                            value={step.template_name}
                            onChange={(e) => handleStepChange(index, 'template_name', e.target.value)}
                          />
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                <p className="automation-hint">
                  Freeform text only delivers to a customer who has messaged you in the last 24 hours - a template is
                  required for the first message otherwise. Template variables aren't supported inside automation
                  steps yet; use a template with no variables.
                </p>
              </div>
              <div className="modal-actions">
                <button type="submit" className="btn-primary" disabled={saving}>
                  {saving ? 'Saving...' : (editingId ? 'Save Changes' : 'Create Automation')}
                </button>
                <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Quick "new group" modal, reachable from the automation form */}
      {showGroupForm && (
        <div className="modal-overlay" onClick={() => setShowGroupForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>New Group</h2>
              <button className="btn-close" onClick={() => setShowGroupForm(false)}>&times;</button>
            </div>
            <form onSubmit={handleCreateGroup}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Group name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. SIP Clients"
                    value={newGroupName}
                    onChange={(e) => setNewGroupName(e.target.value)}
                  />
                </div>
              </div>
              <div className="modal-actions">
                <button type="submit" className="btn-primary">Create</button>
                <button type="button" className="btn-secondary" onClick={() => setShowGroupForm(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Enrollments viewer */}
      {showEnrollments && enrollmentsAutomation && (
        <div className="modal-overlay" onClick={() => setShowEnrollments(false)}>
          <div className="modal-content enrollments-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Enrollments - {enrollmentsAutomation.name}</h2>
              <button className="btn-close" onClick={() => setShowEnrollments(false)}>&times;</button>
            </div>
            <div className="modal-body">
              {enrollments.length === 0 ? (
                <p className="no-data">Nobody is enrolled in this automation yet. Use "Enroll Group" to start it for an audience.</p>
              ) : (
                <div className="enrollments-table-wrap">
                  <table className="enrollments-table">
                    <thead>
                      <tr>
                        <th>Lead / Contact</th>
                        <th>Progress</th>
                        <th>Status</th>
                        <th>Next step at</th>
                        <th></th>
                      </tr>
                    </thead>
                    <tbody>
                      {enrollments.map((en) => (
                        <tr key={en.id}>
                          <td>{en.entity_name || `${en.entity_type} #${en.entity_id}`}</td>
                          <td>{Math.min(en.current_step + 1, en.total_steps)} / {en.total_steps}</td>
                          <td><span className={`enrollment-status ${en.status}`}>{ENROLLMENT_STATUS_LABEL[en.status] || en.status}</span></td>
                          <td>{en.status === 'active' ? formatWhen(en.next_run_at) : '—'}</td>
                          <td>
                            {en.status === 'active' && (
                              <button className="btn-secondary small" onClick={() => handleStopEnrollment(en.id)}>Stop</button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
