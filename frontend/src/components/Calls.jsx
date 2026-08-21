import React, { useState, useEffect } from 'react';
import '../styles/Calls.css';

export default function Calls() {
  const [calls, setCalls] = useState([]);
  const [stats, setStats] = useState({
    totalCalls: 0,
    inbound: 0,
    outbound: 0,
    avgDuration: '0m'
  });

  useEffect(() => {
    fetchCalls();
  }, []);

  const fetchCalls = async () => {
    try {
      const response = await fetch('/api/calls');
      const data = await response.json();
      setCalls(data);
      calculateStats(data);
    } catch (error) {
      console.error('Error fetching calls:', error);
      setCalls(mockCalls);
      calculateStats(mockCalls);
    }
  };

  const calculateStats = (callList) => {
    setStats({
      totalCalls: callList.length,
      inbound: callList.filter(c => c.type === 'Inbound').length,
      outbound: callList.filter(c => c.type === 'Outbound').length,
      avgDuration: '6m 8s'
    });
  };

  return (
    <div className="calls-container">
      <div className="calls-header">
        <h1>Calls</h1>
        <button className="btn-primary">+ Log Call</button>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{stats.totalCalls}</div>
          <div className="stat-label">Total Calls</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.inbound}</div>
          <div className="stat-label">Inbound</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.outbound}</div>
          <div className="stat-label">Outbound</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.avgDuration}</div>
          <div className="stat-label">Avg Duration</div>
        </div>
      </div>

      <div className="calls-table">
        <table>
          <thead>
            <tr>
              <th>Contact</th>
              <th>Phone</th>
              <th>Duration</th>
              <th>Type</th>
              <th>Outcome</th>
              <th>Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {calls.map(call => (
              <tr key={call.id}>
                <td><strong>{call.name}</strong></td>
                <td>{call.phone}</td>
                <td>{call.duration}</td>
                <td><span className={`badge-${call.type.toLowerCase()}`}>{call.type}</span></td>
                <td>{call.outcome}</td>
                <td>{call.date}</td>
                <td>
                  <button className="btn-small">View</button>
                  <button className="btn-small delete">Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const mockCalls = [
  {
    id: 1,
    name: 'Neha Singh',
    phone: '+91-9876543210',
    duration: '5m 20s',
    type: 'Outbound',
    outcome: 'Interested',
    date: '2026-08-21'
  },
  {
    id: 2,
    name: 'Vikram Reddy',
    phone: '+91-9876543211',
    duration: '3m 45s',
    type: 'Inbound',
    outcome: 'Not Interested',
    date: '2026-08-21'
  },
  {
    id: 3,
    name: 'Anjali Desai',
    phone: '+91-9876543212',
    duration: '8m 10s',
    type: 'Outbound',
    outcome: 'Meeting Scheduled',
    date: '2026-08-20'
  },
  {
    id: 4,
    name: 'Amit Patel',
    phone: '+91-9876543213',
    duration: '6m 50s',
    type: 'Outbound',
    outcome: 'Follow-up Needed',
    date: '2026-08-20'
  }
];
