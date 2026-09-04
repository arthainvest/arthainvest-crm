import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { loginUser } from '../services/api';
import '../styles/Login.css';

export default function Login({ onLoginSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [searchParams] = useSearchParams();
  // Set by the api.js response interceptor when a request comes back 401 mid-session - the
  // token expired (30 min by default, see backend/auth.py) and there's no refresh mechanism,
  // so this is the one place that tells the user why they landed back here instead of leaving
  // every form to fail with its own generic, unexplained error.
  const [error, setError] = useState(searchParams.get('expired') ? 'Your session expired - please log in again.' : '');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await loginUser(username, password);

      // Store token and user info
      localStorage.setItem('token', response.access_token);
      localStorage.setItem('userId', response.user_id);
      localStorage.setItem('username', response.username);
      localStorage.setItem('role', response.role);

      // Update app-level auth state, then redirect to dashboard
      onLoginSuccess?.();
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>ArthaInvest CRM</h1>
          <p>Welcome Back</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              disabled={loading}
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button
            type="submit"
            className="login-button"
            disabled={loading}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>

          <p style={{ textAlign: 'center', marginTop: 16 }}>
            <Link to="/forgot-password" style={{ color: '#667eea', fontSize: 14 }}>Forgot password?</Link>
          </p>
        </form>

        {process.env.NODE_ENV === 'development' && (
          <div className="login-footer">
            <p>Test Credentials:</p>
            <p><strong>Username:</strong> testuser</p>
            <p><strong>Password:</strong> 12345</p>
          </div>
        )}
      </div>
    </div>
  );
}
