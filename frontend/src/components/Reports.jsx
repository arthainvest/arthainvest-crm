import React, { useState } from 'react';
import '../styles/Reports.css';

export default function Reports() {
  const [activeTab, setActiveTab] = useState('sales');

  const reportTabs = [
    { id: 'sales', label: 'Sales', icon: '📊' },
    { id: 'contacts', label: 'Contacts', icon: '👥' },
    { id: 'calls', label: 'Calls', icon: '☎️' }
  ];

  const salesMetrics = [
    { label: 'Total Revenue', value: '₹5,25,000' },
    { label: 'Deals Closed', value: '8' },
    { label: 'Win Rate', value: '68%' },
    { label: 'Avg Deal Size', value: '₹65,625' }
  ];

  const contactMetrics = [
    { label: 'Total Contacts', value: '127' },
    { label: 'Active Contacts', value: '85' },
    { label: 'Avg Response Time', value: '2.5 hrs' },
    { label: 'Conversion Rate', value: '42%' }
  ];

  const callMetrics = [
    { label: 'Total Calls', value: '456' },
    { label: 'Avg Call Duration', value: '6m 15s' },
    { label: 'Call Success Rate', value: '62%' },
    { label: 'Calls This Month', value: '128' }
  ];

  const getMetrics = () => {
    switch(activeTab) {
      case 'contacts': return contactMetrics;
      case 'calls': return callMetrics;
      default: return salesMetrics;
    }
  };

  return (
    <div className="reports-container">
      <div className="reports-header">
        <h1>Reports</h1>
        <button className="btn-primary">📊 Export Report</button>
      </div>

      <div className="tab-navigation">
        {reportTabs.map(tab => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      <div className="metrics-grid">
        {getMetrics().map((metric, idx) => (
          <div key={idx} className="metric-card">
            <div className="metric-value">{metric.value}</div>
            <div className="metric-label">{metric.label}</div>
          </div>
        ))}
      </div>

      <div className="chart-container">
        <h3>Performance Trend</h3>
        <p className="placeholder">📈 Chart visualization - Integration with Chart.js pending</p>
        <div style={{ height: '300px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', borderRadius: '8px', opacity: 0.1 }}></div>
      </div>

      <div className="report-controls">
        <label>Date Range:</label>
        <select>
          <option>This Month</option>
          <option>Last Month</option>
          <option>Last Quarter</option>
          <option>This Year</option>
        </select>
      </div>
    </div>
  );
}
