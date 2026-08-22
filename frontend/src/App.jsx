import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import Contacts from './components/Contacts';
import LeadsList from './components/LeadsList';
import Pipeline from './components/Pipeline';
import Calls from './components/Calls';
import Marketing from './components/Marketing';
import Reports from './components/Reports';
import Integrations from './components/Integrations';
import Settings from './components/Settings';
import Navigation from './components/Navigation';
import { applyTheme, getStoredTheme } from './utils/theme';
import './App.css';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    applyTheme(getStoredTheme());
    const token = localStorage.getItem('token');
    setIsLoggedIn(!!token);
    setLoading(false);
  }, []);

  if (loading) {
    return <div className="app-loading">Loading...</div>;
  }

  return (
    <Router>
      {isLoggedIn ? (
        <div className="app-container">
          <Navigation onLogout={() => setIsLoggedIn(false)} />
          <div className="main-content">
            <Routes>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/contacts" element={<Contacts />} />
              <Route path="/leads" element={<LeadsList />} />
              <Route path="/pipeline" element={<Pipeline />} />
              <Route path="/calls" element={<Calls />} />
              <Route path="/marketing" element={<Marketing />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/integrations" element={<Integrations />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<Navigate to="/dashboard" />} />
            </Routes>
          </div>
        </div>
      ) : (
        <Routes>
          <Route path="/login" element={<Login onLoginSuccess={() => setIsLoggedIn(true)} />} />
          <Route path="*" element={<Navigate to="/login" />} />
        </Routes>
      )}
    </Router>
  );
}

export default App;
