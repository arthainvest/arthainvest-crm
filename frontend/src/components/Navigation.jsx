import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/Navigation.css';

export default function Navigation({ onLogout }) {
  const navigate = useNavigate();
  const username = localStorage.getItem('username');

  const handleLogout = () => {
    localStorage.clear();
    onLogout();
    navigate('/login');
  };

  return (
    <nav className="navigation">
      <div className="nav-header">
        <h1 className="app-title">ArthaInvest</h1>
      </div>

      <div className="nav-links">
        <Link to="/dashboard" className="nav-link">
          <span className="icon">📊</span>
          <span>Dashboard</span>
        </Link>
        <Link to="/contacts" className="nav-link">
          <span className="icon">👥</span>
          <span>Contacts</span>
        </Link>
        <Link to="/leads" className="nav-link">
          <span className="icon">📈</span>
          <span>Leads</span>
        </Link>
        <Link to="/pipeline" className="nav-link">
          <span className="icon">💼</span>
          <span>Pipeline</span>
        </Link>
        <Link to="/calls" className="nav-link">
          <span className="icon">☎️</span>
          <span>Calls</span>
        </Link>
        <Link to="/marketing" className="nav-link">
          <span className="icon">📢</span>
          <span>Marketing</span>
        </Link>
        <Link to="/whatsapp" className="nav-link">
          <span className="icon">💬</span>
          <span>WhatsApp</span>
        </Link>
        <Link to="/automations" className="nav-link">
          <span className="icon">🔁</span>
          <span>Automations</span>
        </Link>
        <Link to="/team" className="nav-link">
          <span className="icon">🧑‍🤝‍🧑</span>
          <span>Team</span>
        </Link>
        <Link to="/reports" className="nav-link">
          <span className="icon">📋</span>
          <span>Reports</span>
        </Link>
        <Link to="/integrations" className="nav-link">
          <span className="icon">🔗</span>
          <span>Integrations</span>
        </Link>
        <Link to="/api-keys" className="nav-link">
          <span className="icon">🔑</span>
          <span>API Keys</span>
        </Link>
        <Link to="/settings" className="nav-link">
          <span className="icon">⚙️</span>
          <span>Settings</span>
        </Link>
      </div>

      <div className="nav-user">
        <div className="user-info">
          <p className="username">{username || 'User'}</p>
        </div>
        <button className="logout-button" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </nav>
  );
}
