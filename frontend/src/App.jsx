import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import Contacts from './components/Contacts';
import LeadsList from './components/LeadsList';
import Pipeline from './components/Pipeline';
import Calls from './components/Calls';
import Marketing from './components/Marketing';
import WhatsAppInbox from './components/WhatsAppInbox';
import Automations from './components/Automations';
import Team from './components/Team';
import Reports from './components/Reports';
import Integrations from './components/Integrations';
import Settings from './components/Settings';
import Navigation from './components/Navigation';
import { applyTheme, getStoredTheme } from './utils/theme';
import { getSettings } from './services/api';
import './App.css';

// Injects the Google Analytics gtag.js script once a tracking ID is configured in Settings.
// A no-op when unset - real analytics only load once the user provides a real ID.
const injectGoogleAnalytics = (trackingId) => {
  if (!trackingId || document.getElementById('ga-gtag-script')) return;
  const script = document.createElement('script');
  script.id = 'ga-gtag-script';
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${trackingId}`;
  document.head.appendChild(script);
  const inline = document.createElement('script');
  inline.text = `window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', '${trackingId}');`;
  document.head.appendChild(inline);
};

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    applyTheme(getStoredTheme());
    const token = localStorage.getItem('token');
    setIsLoggedIn(!!token);
    setLoading(false);
    if (token) {
      getSettings(token)
        .then((data) => injectGoogleAnalytics(data.ga_tracking_id))
        .catch((error) => console.error('Error fetching settings for GA:', error));
    }
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
              <Route path="/whatsapp" element={<WhatsAppInbox />} />
              <Route path="/automations" element={<Automations />} />
              <Route path="/team" element={<Team />} />
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
