import React, { useState, useEffect, useCallback } from 'react';
import { getMfHoldings, createMfHolding, updateMfHolding, deleteMfHolding } from '../services/api';
import '../styles/PortfolioTracking.css';

const STATUS_OPTIONS = ['Active', 'Paused', 'Stopped', 'Redeemed'];
const INVESTMENT_TYPES = ['SIP', 'Lumpsum', 'SWP'];

const emptyForm = {
  fund_name: '', folio_number: '', fund_category: '', investment_type: 'SIP',
  amount: '', frequency: 'Monthly', next_due_date: '', status: 'Active', goal: '',
};

export default function ContactMfHoldings({ token, contactId }) {
  const [holdings, setHoldings] = useState([]);
  const [showAdd, setShowAdd] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);

  const fetchHoldings = useCallback(async () => {
    try {
      const data = await getMfHoldings(token, { contactId });
      setHoldings(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching MF holdings:', error);
    }
  }, [token, contactId]);

  useEffect(() => {
    fetchHoldings();
  }, [fetchHoldings]);

  const openAdd = () => {
    setEditingId(null);
    setForm(emptyForm);
    setShowAdd(true);
  };

  const openEdit = (holding) => {
    setEditingId(holding.id);
    setForm({
      fund_name: holding.fund_name || '',
      folio_number: holding.folio_number || '',
      fund_category: holding.fund_category || '',
      investment_type: holding.investment_type || 'SIP',
      amount: holding.amount != null ? String(holding.amount) : '',
      frequency: holding.frequency || 'Monthly',
      next_due_date: holding.next_due_date || '',
      status: holding.status || 'Active',
      goal: holding.goal || '',
    });
    setShowAdd(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.fund_name.trim()) return;

    const payload = {
      ...form,
      amount: form.amount === '' ? null : Number(form.amount),
      next_due_date: form.next_due_date || null,
    };

    try {
      if (editingId) {
        await updateMfHolding(token, editingId, payload);
      } else {
        await createMfHolding(token, { contact_id: contactId, ...payload });
      }
      setShowAdd(false);
      setEditingId(null);
      setForm(emptyForm);
      fetchHoldings();
    } catch (error) {
      console.error('Error saving MF holding:', error);
      alert('Failed to save fund. Please try again.');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Remove this fund from the client\'s tracked portfolio?')) return;
    try {
      await deleteMfHolding(token, id);
      fetchHoldings();
    } catch (error) {
      console.error('Error deleting MF holding:', error);
      alert('Failed to delete. Please try again.');
    }
  };

  return (
    <div className="portfolio-block">
      <div className="portfolio-block-header">
        <span className="portfolio-block-title">📈 Mutual Fund Holdings</span>
        {!showAdd && (
          <button type="button" className="portfolio-add-btn" onClick={openAdd}>+ Add Fund</button>
        )}
      </div>

      {holdings.length === 0 && !showAdd && (
        <p className="portfolio-empty">No funds tracked yet.</p>
      )}

      {holdings.map((h) => (
        <div key={h.id} className="portfolio-row">
          <div className="portfolio-row-main">
            <span className="portfolio-row-name">{h.fund_name}</span>
            {h.fund_category && <span className="portfolio-row-tag">{h.fund_category}</span>}
            <span className={`portfolio-status-badge status-${(h.status || '').toLowerCase()}`}>{h.status}</span>
            <div className="portfolio-row-actions">
              <button type="button" onClick={() => openEdit(h)} title="Edit">✏️</button>
              <button type="button" onClick={() => handleDelete(h.id)} title="Delete">🗑️</button>
            </div>
          </div>
          <div className="portfolio-row-meta">
            <span>{h.investment_type}{h.amount != null ? ` · ₹${Number(h.amount).toLocaleString('en-IN')}` : ''}{h.frequency ? ` (${h.frequency})` : ''}</span>
            {h.next_due_date && <span>Next due: {new Date(h.next_due_date).toLocaleDateString('en-IN')}</span>}
            {h.goal && <span>Goal: {h.goal}</span>}
          </div>
        </div>
      ))}

      {showAdd && (
        <form className="portfolio-form" onSubmit={handleSubmit}>
          <div className="portfolio-form-grid">
            <input
              type="text" placeholder="Fund name *" required autoFocus
              value={form.fund_name}
              onChange={(e) => setForm({ ...form, fund_name: e.target.value })}
            />
            <input
              type="text" placeholder="Folio number"
              value={form.folio_number}
              onChange={(e) => setForm({ ...form, folio_number: e.target.value })}
            />
            <input
              type="text" placeholder="Category (Equity, Debt...)"
              value={form.fund_category}
              onChange={(e) => setForm({ ...form, fund_category: e.target.value })}
            />
            <select value={form.investment_type} onChange={(e) => setForm({ ...form, investment_type: e.target.value })}>
              {INVESTMENT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <input
              type="number" placeholder="Amount"
              value={form.amount}
              onChange={(e) => setForm({ ...form, amount: e.target.value })}
            />
            <input
              type="text" placeholder="Frequency (Monthly...)"
              value={form.frequency}
              onChange={(e) => setForm({ ...form, frequency: e.target.value })}
            />
            <input
              type="date" placeholder="Next due date"
              value={form.next_due_date}
              onChange={(e) => setForm({ ...form, next_due_date: e.target.value })}
            />
            <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
            <input
              type="text" placeholder="Goal (Retirement...)"
              value={form.goal}
              onChange={(e) => setForm({ ...form, goal: e.target.value })}
            />
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
