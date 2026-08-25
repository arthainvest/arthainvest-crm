import React, { useState, useEffect } from 'react';
import { getCompanies, createCompany, updateCompany, deleteCompany, getCompanyContacts } from '../services/api';
import '../styles/Companies.css';

const emptyForm = { name: '', industry: '', city: '', phone: '', email: '', website: '', notes: '' };

// Kylas parity - a standalone company/organization directory. Contacts can link to a Company
// record (contacts.company_id, set from the Contacts page's inline "Linked company" dropdown);
// each row here expands to show who's linked, and the count updates live as links change.
export default function Companies() {
  const [companies, setCompanies] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [expandedId, setExpandedId] = useState(null);
  const [linkedContacts, setLinkedContacts] = useState([]);
  const [loadingContacts, setLoadingContacts] = useState(false);
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

  const toggleExpand = async (companyId) => {
    if (expandedId === companyId) {
      setExpandedId(null);
      return;
    }
    setExpandedId(companyId);
    setLoadingContacts(true);
    try {
      const data = await getCompanyContacts(token, companyId);
      setLinkedContacts(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to fetch linked contacts:', err);
      setLinkedContacts([]);
    } finally {
      setLoadingContacts(false);
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
    if (!window.confirm('Delete this company? Any contacts linked to it will become unlinked.')) return;
    try {
      await deleteCompany(token, id);
      setCompanies((prev) => prev.filter((c) => c.id !== id));
      if (expandedId === id) setExpandedId(null);
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
                <th></th>
                <th>Name</th>
                <th>Industry</th>
                <th>City</th>
                <th>Phone</th>
                <th>Email</th>
                <th>Website</th>
                <th>Contacts</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {companies.map((c) => (
                <React.Fragment key={c.id}>
                  <tr>
                    <td>
                      <button
                        type="button"
                        className="company-expand-toggle"
                        onClick={() => toggleExpand(c.id)}
                        title={expandedId === c.id ? 'Hide contacts' : 'Show linked contacts'}
                        disabled={!c.contact_count}
                      >
                        <span className={`expand-arrow ${expandedId === c.id ? 'open' : ''}`}>▸</span>
                      </button>
                    </td>
                    <td><strong>{c.name}</strong></td>
                    <td>{c.industry || '-'}</td>
                    <td>{c.city || '-'}</td>
                    <td>{c.phone || '-'}</td>
                    <td>{c.email || '-'}</td>
                    <td>{c.website ? <a href={c.website} target="_blank" rel="noopener noreferrer">{c.website}</a> : '-'}</td>
                    <td>
                      <span className="company-contact-count">{c.contact_count} contact{c.contact_count === 1 ? '' : 's'}</span>
                    </td>
                    <td>
                      <button className="btn-small" onClick={() => openEditModal(c)}>Edit</button>
                      <button className="btn-small delete" onClick={() => handleDelete(c.id)}>Delete</button>
                    </td>
                  </tr>
                  {expandedId === c.id && (
                    <tr className="company-contacts-row">
                      <td></td>
                      <td colSpan="8">
                        {loadingContacts ? (
                          <span className="no-data-inline">Loading…</span>
                        ) : linkedContacts.length === 0 ? (
                          <span className="no-data-inline">No contacts linked to this company.</span>
                        ) : (
                          <ul className="company-linked-contacts">
                            {linkedContacts.map((contact) => (
                              <li key={contact.id}>
                                <strong>{contact.name}</strong>
                                {contact.email && <span> · {contact.email}</span>}
                                {contact.phone && <span> · {contact.phone}</span>}
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
