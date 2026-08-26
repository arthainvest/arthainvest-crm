import React, { useState, useEffect } from 'react';
import {
  getQuotations, createQuotation, updateQuotation, deleteQuotation, sendQuotation,
  getLeads, getContactsList, getDeals
} from '../services/api';
import { LOAN_PRODUCTS } from '../constants/loanProducts';
import '../styles/Quotations.css';

const STATUS_OPTIONS = ['Draft', 'Sent', 'Accepted', 'Rejected'];
const emptyItem = () => ({ description: '', amount: '' });

const emptyForm = {
  recipientType: 'lead',
  recipientId: '',
  dealId: '',
  title: '',
  validUntil: '',
  notes: '',
  items: [emptyItem()],
};

const statusClass = (status) => (status || '').toLowerCase();

const formatCurrency = (n) => `₹${(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;

export default function Quotations() {
  const [quotations, setQuotations] = useState([]);
  const [leads, setLeads] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [deals, setDeals] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [sendingId, setSendingId] = useState(null);
  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchQuotations();
    fetchLeads();
    fetchContacts();
    fetchDeals();
  }, []);

  const fetchQuotations = async () => {
    try {
      const data = await getQuotations(token);
      setQuotations(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to fetch quotations:', err);
    }
  };

  const fetchLeads = async () => {
    try {
      const data = await getLeads(token);
      setLeads(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to fetch leads:', err);
    }
  };

  const fetchContacts = async () => {
    try {
      const data = await getContactsList(token);
      setContacts(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to fetch contacts:', err);
    }
  };

  const fetchDeals = async () => {
    try {
      const data = await getDeals(token);
      setDeals(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to fetch deals:', err);
    }
  };

  // Deals carry no name of their own (just lead_id + loan_product + deal_value) - cross-
  // reference the matching lead to build a readable label, same approach as Pipeline.jsx.
  const dealLabel = (deal) => {
    const lead = leads.find((l) => l.id === deal.lead_id);
    const productInfo = LOAN_PRODUCTS.find((p) => p.id === deal.loan_product);
    return `${lead?.name || `Lead #${deal.lead_id}`} - ${productInfo?.name || deal.loan_product} (₹${(deal.deal_value || 0).toLocaleString('en-IN')})`;
  };

  const openAddModal = () => {
    setEditingId(null);
    setForm(emptyForm);
    setShowModal(true);
  };

  const openEditModal = (q) => {
    setEditingId(q.id);
    setForm({
      recipientType: q.contact_id ? 'contact' : 'lead',
      recipientId: String(q.contact_id || q.lead_id || ''),
      dealId: q.deal_id ? String(q.deal_id) : '',
      title: q.title || '',
      validUntil: q.valid_until || '',
      notes: q.notes || '',
      items: q.items.length > 0
        ? q.items.map((i) => ({ description: i.description, amount: String(i.amount) }))
        : [emptyItem()],
    });
    setShowModal(true);
  };

  const updateItem = (index, field, value) => {
    setForm((prev) => {
      const items = [...prev.items];
      items[index] = { ...items[index], [field]: value };
      return { ...prev, items };
    });
  };

  const addItemRow = () => {
    setForm((prev) => ({ ...prev, items: [...prev.items, emptyItem()] }));
  };

  const removeItemRow = (index) => {
    setForm((prev) => ({ ...prev, items: prev.items.filter((_, i) => i !== index) }));
  };

  const grandTotal = form.items.reduce((sum, item) => sum + (Number(item.amount) || 0), 0);

  const handleSave = async (e) => {
    e.preventDefault();
    if (!form.title.trim() || !form.recipientId) return;

    const payload = {
      lead_id: form.recipientType === 'lead' ? Number(form.recipientId) : null,
      contact_id: form.recipientType === 'contact' ? Number(form.recipientId) : null,
      deal_id: form.dealId ? Number(form.dealId) : null,
      title: form.title,
      valid_until: form.validUntil || null,
      notes: form.notes || null,
      items: form.items
        .filter((i) => i.description.trim())
        .map((i) => ({ description: i.description, amount: Number(i.amount) || 0 })),
    };

    try {
      if (editingId) {
        await updateQuotation(token, editingId, payload);
      } else {
        await createQuotation(token, payload);
      }
      setShowModal(false);
      fetchQuotations();
    } catch (err) {
      console.error('Failed to save quotation:', err);
      alert('Failed to save quotation. Please try again.');
    }
  };

  const handleStatusChange = async (id, status) => {
    const previous = quotations.find((q) => q.id === id);
    setQuotations((prev) => prev.map((q) => (q.id === id ? { ...q, status } : q)));
    try {
      await updateQuotation(token, id, { status });
    } catch (err) {
      console.error('Failed to update quotation status:', err);
      if (previous) setQuotations((prev) => prev.map((q) => (q.id === id ? previous : q)));
      alert('Failed to update status. Please try again.');
    }
  };

  const handleSend = async (id) => {
    setSendingId(id);
    try {
      const result = await sendQuotation(token, id);
      alert(result.message);
      fetchQuotations();
    } catch (err) {
      console.error('Failed to send quotation:', err);
      alert('Failed to send quotation. Please try again.');
    } finally {
      setSendingId(null);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this quotation?')) return;
    try {
      await deleteQuotation(token, id);
      setQuotations((prev) => prev.filter((q) => q.id !== id));
    } catch (err) {
      console.error('Failed to delete quotation:', err);
      alert('Failed to delete quotation. Please try again.');
    }
  };

  const recipientOptions = form.recipientType === 'lead' ? leads : contacts;

  return (
    <div className="quotations-container">
      <div className="quotations-header">
        <h1>Quotations</h1>
        <button className="btn-primary" onClick={openAddModal}>+ New Quotation</button>
      </div>

      {quotations.length === 0 ? (
        <p className="no-data">No quotations yet. Create one to send a formal price quote to a lead or contact.</p>
      ) : (
        <div className="quotations-table">
          <table>
            <thead>
              <tr>
                <th>Quotation #</th>
                <th>Title</th>
                <th>To</th>
                <th>Deal</th>
                <th>Grand Total</th>
                <th>Status</th>
                <th>Valid Until</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {quotations.map((q) => (
                <tr key={q.id}>
                  <td><strong>{q.quotation_number}</strong></td>
                  <td>{q.title}</td>
                  <td>{q.contact_name || q.lead_name || '-'}</td>
                  <td className="quotation-deal-cell">
                    {q.deal_label || '-'}
                    {q.company_name && <div className="quotation-company-sub">🏢 {q.company_name}</div>}
                    {q.assigned_team_member_name && <div className="quotation-company-sub">🧑‍🤝‍🧑 {q.assigned_team_member_name}</div>}
                  </td>
                  <td>{formatCurrency(q.grand_total)}</td>
                  <td>
                    <select
                      className={`quotation-status-select status-${statusClass(q.status)}`}
                      value={q.status}
                      onChange={(e) => handleStatusChange(q.id, e.target.value)}
                    >
                      {STATUS_OPTIONS.map((s) => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
                  </td>
                  <td>{q.valid_until || '-'}</td>
                  <td className="quotation-actions">
                    <button className="btn-small" onClick={() => openEditModal(q)}>Edit</button>
                    <button className="btn-small" onClick={() => handleSend(q.id)} disabled={sendingId === q.id}>
                      {sendingId === q.id ? 'Sending…' : '✉️ Send'}
                    </button>
                    <button className="btn-small delete" onClick={() => handleDelete(q.id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content quotation-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingId ? 'Edit Quotation' : 'New Quotation'}</h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={handleSave}>
              <div className="form-row">
                <div className="form-group">
                  <label>Recipient Type</label>
                  <select
                    value={form.recipientType}
                    onChange={(e) => setForm({ ...form, recipientType: e.target.value, recipientId: '' })}
                  >
                    <option value="lead">Lead</option>
                    <option value="contact">Contact</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>{form.recipientType === 'lead' ? 'Lead' : 'Contact'} *</label>
                  <select
                    required
                    value={form.recipientId}
                    onChange={(e) => setForm({ ...form, recipientId: e.target.value })}
                  >
                    <option value="">-- Select --</option>
                    {recipientOptions.map((r) => (
                      <option key={r.id} value={r.id}>{r.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>Link to Deal (optional)</label>
                <select
                  value={form.dealId}
                  onChange={(e) => setForm({ ...form, dealId: e.target.value })}
                >
                  <option value="">-- Not linked to a deal --</option>
                  {deals.map((d) => (
                    <option key={d.id} value={d.id}>{dealLabel(d)}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Title *</label>
                <input type="text" required placeholder="e.g. Home Loan Quotation" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
              </div>

              <div className="form-group">
                <label>Valid Until</label>
                <input type="date" value={form.validUntil} onChange={(e) => setForm({ ...form, validUntil: e.target.value })} />
              </div>

              <div className="form-group">
                <label>Line Items</label>
                <div className="quotation-items-editor">
                  {form.items.map((item, index) => (
                    <div className="quotation-item-row" key={index}>
                      <input
                        type="text"
                        placeholder="Description"
                        value={item.description}
                        onChange={(e) => updateItem(index, 'description', e.target.value)}
                      />
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        placeholder="Amount"
                        value={item.amount}
                        onChange={(e) => updateItem(index, 'amount', e.target.value)}
                      />
                      <button
                        type="button"
                        className="quotation-item-remove"
                        onClick={() => removeItemRow(index)}
                        disabled={form.items.length === 1}
                        title="Remove item"
                      >
                        🗑️
                      </button>
                    </div>
                  ))}
                </div>
                <button type="button" className="btn-secondary quotation-add-item" onClick={addItemRow}>+ Add Line Item</button>
                <div className="quotation-grand-total">Grand Total: <strong>{formatCurrency(grandTotal)}</strong></div>
              </div>

              <div className="form-group">
                <label>Notes</label>
                <textarea rows="3" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
              </div>

              <div className="modal-actions">
                <button type="submit" className="btn-primary">{editingId ? 'Save Changes' : 'Create Quotation'}</button>
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
