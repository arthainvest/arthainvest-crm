import React, { useState, useEffect } from 'react';
import { getTeam, createTeamMember, updateTeamMember, deleteTeamMember, getTeamAnalytics } from '../services/api';
import '../styles/Team.css';

const ROLE_LABELS = {
  admin: 'Admin',
  team_lead: 'Team Leader',
  location_head: 'Location Head',
  employee: 'Employee'
};

const ROLE_ORDER = ['admin', 'team_lead', 'location_head', 'employee'];

const emptyForm = { name: '', role: 'employee', email: '', phone: '' };

export default function Team() {
  const [members, setMembers] = useState([]);
  const [productivity, setProductivity] = useState({});
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);

  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchTeam();
  }, []);

  const fetchTeam = async () => {
    try {
      const [teamData, statsData] = await Promise.all([
        getTeam(token),
        getTeamAnalytics(token)
      ]);
      setMembers(Array.isArray(teamData) ? teamData : []);
      const statsById = {};
      (Array.isArray(statsData) ? statsData : []).forEach((s) => { statsById[s.id] = s; });
      setProductivity(statsById);
    } catch (error) {
      console.error('Error fetching team:', error);
    }
  };

  const handleAddClick = () => {
    setEditingId(null);
    setForm(emptyForm);
    setShowForm(true);
  };

  const handleEditClick = (member) => {
    setEditingId(member.id);
    setForm({ name: member.name, role: member.role, email: member.email || '', phone: member.phone || '' });
    setShowForm(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    try {
      if (editingId) {
        await updateTeamMember(token, editingId, form);
      } else {
        await createTeamMember(token, form);
      }
      setShowForm(false);
      setForm(emptyForm);
      setEditingId(null);
      fetchTeam();
    } catch (error) {
      console.error('Error saving team member:', error);
      alert('Failed to save team member. Please try again.');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Remove this team member?')) return;
    try {
      await deleteTeamMember(token, id);
      setMembers((prev) => prev.filter((m) => m.id !== id));
    } catch (error) {
      console.error('Error deleting team member:', error);
      alert('Failed to remove team member. Please try again.');
    }
  };

  const groupedByRole = ROLE_ORDER.map((role) => ({
    role,
    label: ROLE_LABELS[role],
    people: members.filter((m) => m.role === role)
  })).filter((g) => g.people.length > 0);

  const fmt = (v, isRevenue) => {
    if (v === null || v === undefined) return '—';
    return isRevenue ? `₹${Number(v).toLocaleString('en-IN')}` : v;
  };

  return (
    <div className="team-container">
      <div className="team-header">
        <h1>Team Management</h1>
        <button className="btn-primary" onClick={handleAddClick}>+ Add Team Member</button>
      </div>

      {members.length === 0 ? (
        <p className="no-data">No team members yet. Add one to get started.</p>
      ) : (
        groupedByRole.map((group) => (
          <div key={group.role} className="team-role-section">
            <h2>{group.label}{group.people.length > 1 ? 's' : ''}</h2>
            <div className="team-grid">
              {group.people.map((member) => {
                const stats = productivity[member.id];
                return (
                  <div key={member.id} className="team-card">
                    <div className="team-card-header">
                      <div className="team-avatar">{member.name.charAt(0)}</div>
                      <div>
                        <h3>{member.name}</h3>
                        <span className="team-role-badge">{ROLE_LABELS[member.role] || member.role}</span>
                      </div>
                    </div>
                    <div className="team-contact-info">
                      {member.email && <p>📧 {member.email}</p>}
                      {member.phone && <p>📱 {member.phone}</p>}
                    </div>
                    <div className="team-stats">
                      <div className="team-stat">
                        <span className="team-stat-value">{fmt(stats?.calls)}</span>
                        <span className="team-stat-label">Calls</span>
                      </div>
                      <div className="team-stat">
                        <span className="team-stat-value">{fmt(stats?.deals_closed)}</span>
                        <span className="team-stat-label">Closed</span>
                      </div>
                      <div className="team-stat">
                        <span className="team-stat-value">{fmt(stats?.revenue, true)}</span>
                        <span className="team-stat-label">Revenue</span>
                      </div>
                    </div>
                    <div className="team-card-actions">
                      <button className="btn-small" onClick={() => handleEditClick(member)}>Edit</button>
                      <button className="btn-small delete" onClick={() => handleDelete(member.id)}>Remove</button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))
      )}

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingId ? 'Edit Team Member' : 'Add Team Member'}</h2>
              <button className="btn-close" onClick={() => setShowForm(false)}>×</button>
            </div>
            <form onSubmit={handleSave}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Name *</label>
                  <input
                    type="text"
                    required
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Role</label>
                  <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                    {ROLE_ORDER.map((role) => (
                      <option key={role} value={role}>{ROLE_LABELS[role]}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Email</label>
                  <input
                    type="email"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Phone</label>
                  <input
                    type="tel"
                    value={form.phone}
                    onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  />
                </div>
              </div>
              <div className="modal-actions">
                <button type="submit" className="btn-primary">{editingId ? 'Save Changes' : 'Add Member'}</button>
                <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
