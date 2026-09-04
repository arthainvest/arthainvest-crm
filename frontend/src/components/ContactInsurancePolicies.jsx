import React, { useState, useEffect, useCallback } from 'react';
import { getInsurancePolicies, createInsurancePolicy, updateInsurancePolicy, deleteInsurancePolicy } from '../services/api';
import '../styles/PortfolioTracking.css';

const STATUS_OPTIONS = ['Active', 'Lapsed', 'Renewed', 'Cancelled', 'Matured', 'Claimed'];
const POLICY_TYPES = ['Health', 'Life', 'Motor', 'Term', 'ULIP', 'Other'];

const emptyForm = {
  policy_type: 'Health', policy_number: '', insurer: '', sum_assured: '',
  premium_amount: '', premium_frequency: 'Annual', renewal_date: '', status: 'Active',
};

export default function ContactInsurancePolicies({ token, contactId }) {
  const [policies, setPolicies] = useState([]);
  const [showAdd, setShowAdd] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);

  const fetchPolicies = useCallback(async () => {
    try {
      const data = await getInsurancePolicies(token, { contactId });
      setPolicies(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching insurance policies:', error);
    }
  }, [token, contactId]);

  useEffect(() => {
    fetchPolicies();
  }, [fetchPolicies]);

  const openAdd = () => {
    setEditingId(null);
    setForm(emptyForm);
    setShowAdd(true);
  };

  const openEdit = (policy) => {
    setEditingId(policy.id);
    setForm({
      policy_type: policy.policy_type || 'Health',
      policy_number: policy.policy_number || '',
      insurer: policy.insurer || '',
      sum_assured: policy.sum_assured != null ? String(policy.sum_assured) : '',
      premium_amount: policy.premium_amount != null ? String(policy.premium_amount) : '',
      premium_frequency: policy.premium_frequency || 'Annual',
      renewal_date: policy.renewal_date || '',
      status: policy.status || 'Active',
    });
    setShowAdd(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const payload = {
      ...form,
      sum_assured: form.sum_assured === '' ? null : Number(form.sum_assured),
      premium_amount: form.premium_amount === '' ? null : Number(form.premium_amount),
      renewal_date: form.renewal_date || null,
    };

    try {
      if (editingId) {
        await updateInsurancePolicy(token, editingId, payload);
      } else {
        await createInsurancePolicy(token, { contact_id: contactId, ...payload });
      }
      setShowAdd(false);
      setEditingId(null);
      setForm(emptyForm);
      fetchPolicies();
    } catch (error) {
      console.error('Error saving insurance policy:', error);
      alert('Failed to save policy. Please try again.');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Remove this policy from the client\'s tracked record?')) return;
    try {
      await deleteInsurancePolicy(token, id);
      fetchPolicies();
    } catch (error) {
      console.error('Error deleting insurance policy:', error);
      alert('Failed to delete. Please try again.');
    }
  };

  return (
    <div className="portfolio-block">
      <div className="portfolio-block-header">
        <span className="portfolio-block-title">🛡️ Insurance Policies</span>
        {!showAdd && (
          <button type="button" className="portfolio-add-btn" onClick={openAdd}>+ Add Policy</button>
        )}
      </div>

      {policies.length === 0 && !showAdd && (
        <p className="portfolio-empty">No policies tracked yet.</p>
      )}

      {policies.map((p) => (
        <div key={p.id} className="portfolio-row">
          <div className="portfolio-row-main">
            <span className="portfolio-row-name">{p.policy_type}{p.insurer ? ` · ${p.insurer}` : ''}</span>
            {p.policy_number && <span className="portfolio-row-tag">{p.policy_number}</span>}
            <span className={`portfolio-status-badge status-${(p.status || '').toLowerCase()}`}>{p.status}</span>
            <div className="portfolio-row-actions">
              <button type="button" onClick={() => openEdit(p)} title="Edit">✏️</button>
              <button type="button" onClick={() => handleDelete(p.id)} title="Delete">🗑️</button>
            </div>
          </div>
          <div className="portfolio-row-meta">
            {p.premium_amount != null && (
              <span>Premium: ₹{Number(p.premium_amount).toLocaleString('en-IN')}{p.premium_frequency ? ` (${p.premium_frequency})` : ''}</span>
            )}
            {p.sum_assured != null && <span>Sum assured: ₹{Number(p.sum_assured).toLocaleString('en-IN')}</span>}
            {p.renewal_date && <span>Renews: {new Date(p.renewal_date).toLocaleDateString('en-IN')}</span>}
          </div>
        </div>
      ))}

      {showAdd && (
        <form className="portfolio-form" onSubmit={handleSubmit}>
          <div className="portfolio-form-grid">
            <select value={form.policy_type} onChange={(e) => setForm({ ...form, policy_type: e.target.value })} autoFocus>
              {POLICY_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <input
              type="text" placeholder="Insurer"
              value={form.insurer}
              onChange={(e) => setForm({ ...form, insurer: e.target.value })}
            />
            <input
              type="text" placeholder="Policy number"
              value={form.policy_number}
              onChange={(e) => setForm({ ...form, policy_number: e.target.value })}
            />
            <input
              type="number" placeholder="Sum assured"
              value={form.sum_assured}
              onChange={(e) => setForm({ ...form, sum_assured: e.target.value })}
            />
            <input
              type="number" placeholder="Premium amount"
              value={form.premium_amount}
              onChange={(e) => setForm({ ...form, premium_amount: e.target.value })}
            />
            <input
              type="text" placeholder="Frequency (Annual...)"
              value={form.premium_frequency}
              onChange={(e) => setForm({ ...form, premium_frequency: e.target.value })}
            />
            <input
              type="date" placeholder="Renewal date"
              value={form.renewal_date}
              onChange={(e) => setForm({ ...form, renewal_date: e.target.value })}
            />
            <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div className="portfolio-form-actions">
            <button type="submit" className="btn-secondary small">{editingId ? 'Save' : 'Add'}</button>
            <button type="button" className="btn-secondary small" onClick={() => { setShowAdd(false); setEditingId(null); }}>Cancel</button>
          </div>
        </form>
      )}
    </div>
  );
}
