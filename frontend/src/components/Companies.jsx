import React, { useState, useEffect } from 'react';
import { getCompanies, createCompany, updateCompany, deleteCompany } from '../services/api';
import '../styles/Companies.css';

const emptyForm = { name: '', industry: '', city: '', phone: '', email: '', website: '', notes: '' };

// Kylas parity - a standalone company/organization directory, separate from Contacts.
// Not yet linked to individual Contacts; ArthaInvest deals mostly with individual clients,
// so this stays optional metadata rather than a required relationship for now.
export default function Companies() {
  const [companies, setCompanies] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      const data = await getCompanies(token);
      setCompanies(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to fetch companies:', err);
    }
  };

  const openAddModal = () => {
    setEditingId(null);
    setForm(emptyForm);
    setShowModal(true);
  };

  const openEditModal = (company) => {
    setEditingId(company.id);
    setForm({
      name: company.name || '',
      industry: company.industry || '',
      city: company.city || '',
      phone: company.phone || '',
      email: company.email || '',
      website: company.website || '',
      notes: company.notes || '',
    });
    setShowModal(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    try {
      if (editingId) {
        await updateCompany(token, editingId, form);
      } else {
        await createCompany(token, form);
      }
      setShowModal(false);
      fetchCompanies();
    } catch (err) {
      console.error('Failed to save company:', err);
      alert('Failed to save company. Please try again.');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this company?')) return;
    try {
      await deleteCompany(token, id);
      setCompanies((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      console.error('Failed to delete company:', err);
      alert('Failed to delete company. Please try again.');
    }
  };

  return (
    <div className="companies-container">
      <div className="companies-header">
        <h1>Companies</h1>
        <button className="btn-primary" onClick={openAddModal}>+ New Company</button>
      </div>

      {companies.length === 0 ? (
        <p className="no-data">No companies yet. Add one to start linking employers/organizations to your work.</p>
      ) : (
        <div className="companies-table">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Industry</th>
                <th>City</th>
                <th>Phone</th>
                <th>Email</th>
                <th>Website</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {companies.map((c) => (
                <tr key={c.id}>
                  <td><strong>{c.name}</strong></td>
                  <td>{c.industry || '-'}</td>
                  <td>{c.city || '-'}</td>
                  <td>{c.phone || '-'}</td>
                  <td>{c.email || '-'}</td>
                  <td>{c.website ? <a href={c.website} target="_blank" rel="noopener noreferrer">{c.website}</a> : '-'}</td>
                  <td>
                    <button className="btn-small" onClick={() => openEditModal(c)}>Edit</button>
                    <button className="btn-small delete" onClick={() => handleDelete(c.id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingId ? 'Edit Company' : 'Add New Company'}</h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={handleSave}>
              <div className="form-group">
                <label>Name *</label>
                <input type="text" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Industry</label>
                <input type="text" value={form.industry} onChange={(e) => setForm({ ...form, industry: e.target.value })} />
              </div>
              <div className="form-group">
                <label>City</label>
                <input type="text" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Phone</label>
                <input type="tel" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Website</label>
                <input type="text" placeholder="https://..." value={form.website} onChange={(e) => setForm({ ...form, website: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Notes</label>
                <textarea rows="3" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
              </div>
              <div className="modal-actions">
                <button type="submit" className="btn-primary">{editingId ? 'Save Changes' : 'Create Company'}</button>
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
