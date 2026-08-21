import React, { useState, useEffect } from 'react';
import { getLeads, createLead, updateLead, deleteLead } from '../services/api';
import '../styles/LeadsList.css';

export default function LeadsList() {
  const mockLeads = [
    { id: 1, name: 'Neha Singh', company: 'Startup Fund', email: 'neha@startup.com', phone: '+91-9876543210', status: 'New', ai_score: 85 },
    { id: 2, name: 'Vikram Reddy', company: 'Tech Park', email: 'vikram@techpark.com', phone: '+91-9876543211', status: 'Contacted', ai_score: 72 },
    { id: 3, name: 'Anjali Desai', company: 'Retail Chain', email: 'anjali@retail.com', phone: '+91-9876543212', status: 'Interested', ai_score: 65 },
    { id: 4, name: 'Amit Patel', company: 'Manufacturing', email: 'amit@mfg.com', phone: '+91-9876543213', status: 'Qualified', ai_score: 58 },
    { id: 5, name: 'Priya Kapoor', company: 'Digital Ventures', email: 'priya@digital.com', phone: '+91-9876543214', status: 'New', ai_score: 80 }
  ];

  const [leads, setLeads] = useState(mockLeads);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    company: '',
    email: '',
    phone: '',
    product: '',
    source: '',
  });
  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchLeads();
  }, []);

  const fetchLeads = async () => {
    try {
      const data = await getLeads(token);
      if (Array.isArray(data) && data.length > 0) {
        setLeads(data);
      } else {
        setLeads(mockLeads);
      }
    } catch (err) {
      console.error('Failed to fetch leads:', err);
      setLeads(mockLeads);
    } finally {
      setLoading(false);
    }
  };

  const handleAddLead = async (e) => {
    e.preventDefault();
    try {
      await createLead(token, formData);
      setFormData({
        name: '',
        company: '',
        email: '',
        phone: '',
        product: '',
        source: '',
      });
      setShowModal(false);
      fetchLeads();
    } catch (err) {
      console.error('Failed to create lead:', err);
      alert('Error creating lead');
    }
  };

  const handleDeleteLead = async (id) => {
    if (window.confirm('Are you sure you want to delete this lead?')) {
      try {
        await deleteLead(token, id);
        fetchLeads();
      } catch (err) {
        console.error('Failed to delete lead:', err);
        alert('Error deleting lead');
      }
    }
  };

  const displayLeads = (leads && leads.length > 0) ? leads : mockLeads;

  return (
    <div className="leads-container">
      <div className="leads-header">
        <h1>Leads</h1>
        <button
          className="btn-primary"
          onClick={() => setShowModal(true)}
        >
          + New Lead
        </button>
      </div>

      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h2>Add New Lead</h2>
              <button
                className="modal-close"
                onClick={() => setShowModal(false)}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddLead}>
              <div className="form-group">
                <label>Name *</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                />
              </div>

              <div className="form-group">
                <label>Company</label>
                <input
                  type="text"
                  value={formData.company}
                  onChange={(e) =>
                    setFormData({ ...formData, company: e.target.value })
                  }
                />
              </div>

              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                />
              </div>

              <div className="form-group">
                <label>Phone</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) =>
                    setFormData({ ...formData, phone: e.target.value })
                  }
                />
              </div>

              <div className="form-group">
                <label>Product</label>
                <input
                  type="text"
                  value={formData.product}
                  onChange={(e) =>
                    setFormData({ ...formData, product: e.target.value })
                  }
                />
              </div>

              <div className="form-group">
                <label>Source</label>
                <input
                  type="text"
                  value={formData.source}
                  onChange={(e) =>
                    setFormData({ ...formData, source: e.target.value })
                  }
                />
              </div>

              <div className="modal-actions">
                <button type="submit" className="btn-primary">
                  Create Lead
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowModal(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {displayLeads && displayLeads.length > 0 ? (
        <table className="leads-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Company</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Status</th>
              <th>Score</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {displayLeads.map((lead) => (
              <tr key={lead.id}>
                <td>{lead.name}</td>
                <td>{lead.company || '-'}</td>
                <td>{lead.email || '-'}</td>
                <td>{lead.phone || '-'}</td>
                <td>
                  <span className={`status-badge ${lead.status}`}>
                    {lead.status}
                  </span>
                </td>
                <td>{lead.ai_score || '-'}</td>
                <td>
                  <button
                    className="btn-danger"
                    onClick={() => handleDeleteLead(lead.id)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="no-data">No leads yet. Create your first lead!</p>
      )}
    </div>
  );
}
