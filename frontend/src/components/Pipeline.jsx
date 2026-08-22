import React, { useState, useEffect } from 'react';
import { getDeals } from '../services/api';
import '../styles/Pipeline.css';

const FolderIcon = () => (
  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
    <path d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
  </svg>
);

export default function Pipeline() {
  const mockDeals = [
    {
      id: 1,
      name: 'Neha Singh',
      company: 'Startup Fund',
      value: 5,
      phone: '+91-9876543210',
      loanProduct: 'LAP',
      stage: 'New',
      probability: 30,
      processStatus: 'Login'
    },
    {
      id: 2,
      name: 'Vikram Reddy',
      company: 'Tech Park',
      value: 10,
      phone: '+91-9876543211',
      loanProduct: 'Business',
      stage: 'Qualified',
      probability: 50,
      processStatus: 'Hold'
    },
    {
      id: 3,
      name: 'Anjali Desai',
      company: 'Retail Chain',
      value: 8,
      phone: '+91-9876543212',
      loanProduct: 'Home',
      stage: 'Proposal',
      probability: 70,
      processStatus: 'Sanction'
    },
    {
      id: 4,
      name: 'Amit Patel',
      company: 'Manufacturing',
      value: 15,
      phone: '+91-9876543213',
      loanProduct: 'Project',
      stage: 'Negotiation',
      probability: 60,
      processStatus: 'Disbursed'
    }
  ];

  const PROCESS_STATUS_OPTIONS = ['Login', 'Sanction', 'Hold', 'Disbursed'];

  const [deals, setDeals] = useState(mockDeals);
  const [showForm, setShowForm] = useState(false);
  const [showDigi, setShowDigi] = useState(false);
  const [selectedDeal, setSelectedDeal] = useState(null);
  const [uploadedDocs, setUploadedDocs] = useState({});
  const [formData, setFormData] = useState({
    name: '',
    company: '',
    value: '',
    phone: '',
    loanProduct: 'LAP',
    stage: 'New',
    probability: 30,
    description: ''
  });

  const LOAN_PRODUCTS = [
    { id: 'LAP', name: 'Loan Against Property', icon: '🏠', rate: '10-15%' },
    { id: 'OD', name: 'Overdraft', icon: '💰', rate: '12-18%' },
    { id: 'CC', name: 'Credit Card', icon: '💳', rate: '20-25%' },
    { id: 'Home', name: 'Home Loan', icon: '🏡', rate: '7-10%' },
    { id: 'Business', name: 'Business Loan', icon: '🏢', rate: '11-16%' },
    { id: 'Project', name: 'Project Loan', icon: '🏗️', rate: '10-14%' }
  ];

  const LOAN_DOCUMENTS = {
    LAP: ['PAN Card', 'Aadhar Card', 'Property Deed', 'Property Tax Receipt', 'Bank Statement', 'Income Proof', 'Identity Proof', 'Address Proof'],
    OD: ['PAN Card', 'Aadhar Card', 'Bank Statement', 'Income Proof', 'Trade License', 'ITR', 'Balance Sheet'],
    CC: ['PAN Card', 'Aadhar Card', 'Bank Statement', 'Income Proof', 'Employment Letter', 'Address Proof'],
    Home: ['PAN Card', 'Aadhar Card', 'Property Documents', 'Valuation Report', 'Bank Statement', 'Income Proof', 'ITR', 'Marriage Certificate'],
    Business: ['PAN Card', 'Aadhar Card', 'Business Registration', 'GST Certificate', 'ITR', 'Balance Sheet', 'P&L', 'Bank Statement', 'Auditor Report'],
    Project: ['PAN Card', 'Aadhar Card', 'Project Plan', 'Project License', 'Technical Approval', 'Cost Estimate', 'Bank Statement', 'Professional Qualifications', 'Experience Certificate', 'Financial Statements']
  };

  const STAGES = ['New', 'Qualified', 'Proposal', 'Negotiation', 'Closed'];

  const token = localStorage.getItem('token');

  // Backend deals only carry {id, lead_id, deal_value, stage, probability, expected_close_date,
  // created_at} - no name/company/phone/loanProduct/processStatus, stage is lowercase, and
  // probability is a 0-1 fraction. Normalize into the shape the rest of this component expects.
  const normalizeDeal = (d) => ({
    id: d.id,
    name: d.name || `Lead #${d.lead_id}`,
    company: d.company || '—',
    value: d.value ?? Math.round((d.deal_value ?? 0) / 1000),
    phone: d.phone || '—',
    loanProduct: d.loanProduct || 'LAP',
    stage: STAGES.find((s) => s.toLowerCase() === String(d.stage).toLowerCase()) || 'New',
    probability: d.probability > 1 ? Math.round(d.probability) : Math.round((d.probability ?? 0) * 100),
    processStatus: d.processStatus || 'Login'
  });

  useEffect(() => {
    fetchDeals();
  }, []);

  const fetchDeals = async () => {
    try {
      const data = await getDeals(token);
      if (Array.isArray(data) && data.length > 0) {
        setDeals(data.map(normalizeDeal));
      } else {
        setDeals(mockDeals);
      }
    } catch (error) {
      console.error('Error fetching deals:', error);
      setDeals(mockDeals);
    }
  };

  const handleAddDeal = () => {
    if (formData.name && formData.company && formData.value) {
      const newDeal = {
        id: deals.length + 1,
        ...formData,
        value: parseInt(formData.value)
      };
      setDeals([...deals, newDeal]);
      setFormData({
        name: '',
        company: '',
        value: '',
        phone: '',
        loanProduct: 'LAP',
        stage: 'New',
        probability: 30,
        description: ''
      });
      setShowForm(false);
    }
  };

  const handleDigiLocker = (deal) => {
    setSelectedDeal(deal);
    if (!uploadedDocs[deal.id]) {
      setUploadedDocs({
        ...uploadedDocs,
        [deal.id]: {}
      });
    }
    setShowDigi(true);
  };

  const handleDocumentCheck = (dealId, doc) => {
    setUploadedDocs({
      ...uploadedDocs,
      [dealId]: {
        ...uploadedDocs[dealId],
        [doc]: !uploadedDocs[dealId]?.[doc]
      }
    });
  };

  const getDocumentProgress = (dealId) => {
    const docs = uploadedDocs[dealId] || {};
    const total = (LOAN_DOCUMENTS[selectedDeal.loanProduct] || []).length;
    const completed = Object.values(docs).filter(v => v).length;
    return { completed, total, percentage: Math.round((completed / total) * 100) };
  };

  const handleProcessStatusChange = (dealId, newStatus) => {
    setDeals((prev) => prev.map((d) => (d.id === dealId ? { ...d, processStatus: newStatus } : d)));
  };

  const getDealsByStage = (stage) => {
    if (!deals || !Array.isArray(deals)) {
      return mockDeals.filter(d => d.stage === stage);
    }
    return deals.filter(d => d.stage === stage);
  };

  const getLoanProductInfo = (productId) => {
    return LOAN_PRODUCTS.find(p => p.id === productId);
  };

  return (
    <div className="pipeline-container">
      <div className="pipeline-header">
        <h1>Pipeline</h1>
        <button className="btn-primary" onClick={() => setShowForm(true)}>+ New Deal</button>
      </div>

      {/* Kanban Board */}
      <div className="kanban-board">
        {STAGES.map(stage => (
          <div key={stage} className="kanban-column">
            <h3>{stage} ({getDealsByStage(stage).length})</h3>
            <div className="deals-list">
              {getDealsByStage(stage).map(deal => {
                const loanInfo = getLoanProductInfo(deal.loanProduct);
                return (
                  <div key={deal.id} className="deal-card">
                    <div className="card-title">
                      <strong>{deal.name}</strong>
                      <span className="close">×</span>
                    </div>

                    <div className="deal-phone">📱 {deal.phone}</div>

                    <div className="deal-info">
                      <p>{deal.company}</p>
                      <div className="deal-status">
                        <span className={`status-badge stage-${stage.toLowerCase()}`}>{stage}</span>
                        <span className={`loan-badge`}>{loanInfo?.icon} {deal.loanProduct}</span>
                      </div>
                    </div>

                    <div className="deal-value">
                      <div>₹{deal.value}K</div>
                      <div>{deal.probability}%</div>
                    </div>

                    <div className="progress-bar">
                      <div className="progress-fill" style={{ width: `${deal.probability}%` }}></div>
                    </div>

                    <button
                      className="digi-btn"
                      onClick={() => handleDigiLocker(deal)}
                    >
                      🔐 DigiLocker
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Sales Pipeline Table */}
      <div className="loan-processing-section">
        <h2>Sales Pipeline</h2>
        <div className="pipeline-table-wrapper">
          <table className="pipeline-table">
            <thead>
              <tr>
                <th>Folder</th>
                <th>Client</th>
                <th>Amount</th>
                <th>Type of Loan</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {deals.map((deal) => {
                const loanInfo = getLoanProductInfo(deal.loanProduct);
                return (
                  <tr key={deal.id}>
                    <td>
                      <button
                        type="button"
                        className="folder-icon-btn"
                        onClick={() => handleDigiLocker(deal)}
                        title="Open DigiLocker"
                      >
                        <FolderIcon />
                      </button>
                    </td>
                    <td className="pipeline-client-name">{deal.name}</td>
                    <td>₹{deal.value}K</td>
                    <td>{loanInfo?.icon} {loanInfo?.name}</td>
                    <td>
                      <select
                        className={`process-status-select status-${(deal.processStatus || 'Login').toLowerCase()}`}
                        value={deal.processStatus || 'Login'}
                        onChange={(e) => handleProcessStatusChange(deal.id, e.target.value)}
                      >
                        {PROCESS_STATUS_OPTIONS.map((s) => (
                          <option key={s} value={s}>{s}</option>
                        ))}
                      </select>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Deal Form */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create New Deal</h2>
              <button className="btn-close" onClick={() => setShowForm(false)}>×</button>
            </div>

            <div className="modal-body form-content">
              <div className="form-group">
                <label>Client Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Enter client name"
                />
              </div>

              <div className="form-group">
                <label>Company</label>
                <input
                  type="text"
                  value={formData.company}
                  onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                  placeholder="Enter company name"
                />
              </div>

              <div className="form-group">
                <label>Deal Value (₹K)</label>
                <input
                  type="number"
                  value={formData.value}
                  onChange={(e) => setFormData({ ...formData, value: e.target.value })}
                  placeholder="Enter deal value"
                />
              </div>

              <div className="form-group">
                <label>Mobile Number</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  placeholder="Enter phone number"
                />
              </div>

              <div className="form-group">
                <label>Loan Product</label>
                <select
                  value={formData.loanProduct}
                  onChange={(e) => setFormData({ ...formData, loanProduct: e.target.value })}
                >
                  {LOAN_PRODUCTS.map(product => (
                    <option key={product.id} value={product.id}>
                      {product.icon} {product.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Stage</label>
                <select
                  value={formData.stage}
                  onChange={(e) => setFormData({ ...formData, stage: e.target.value })}
                >
                  {STAGES.map(stage => (
                    <option key={stage} value={stage}>{stage}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Probability (%)</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={formData.probability}
                  onChange={(e) => setFormData({ ...formData, probability: e.target.value })}
                />
              </div>

              <div className="modal-actions">
                <button className="btn-primary" onClick={handleAddDeal}>Create Deal</button>
                <button className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* DigiLocker Modal */}
      {showDigi && selectedDeal && (
        <div className="modal-overlay" onClick={() => setShowDigi(false)}>
          <div className="modal-content digi-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>🔐 DigiLocker - Document Management</h2>
              <button className="btn-close" onClick={() => setShowDigi(false)}>×</button>
            </div>

            <div className="modal-body">
              <div className="digi-info">
                <h3>{selectedDeal.name}</h3>
                <p><strong>Company:</strong> {selectedDeal.company}</p>
                <p><strong>Loan Type:</strong> {getLoanProductInfo(selectedDeal.loanProduct)?.name}</p>
                <p><strong>Amount:</strong> ₹{selectedDeal.value}K</p>
              </div>

              <div className="digi-section">
                <h4>Required Documents ({(LOAN_DOCUMENTS[selectedDeal.loanProduct] || []).length})</h4>
                <div className="documents-list">
                  {(LOAN_DOCUMENTS[selectedDeal.loanProduct] || []).map((doc, idx) => (
                    <div key={idx} className="document-item">
                      <input
                        type="checkbox"
                        checked={uploadedDocs[selectedDeal.id]?.[doc] || false}
                        onChange={() => handleDocumentCheck(selectedDeal.id, doc)}
                      />
                      <span>{doc}</span>
                      <span className="doc-status">
                        {uploadedDocs[selectedDeal.id]?.[doc] ? '✓' : '○'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {selectedDeal.id in uploadedDocs && (
                <div className="digi-section">
                  <h4>Progress</h4>
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${getDocumentProgress(selectedDeal.id).percentage}%` }}
                    ></div>
                  </div>
                  <p className="progress-text">
                    {getDocumentProgress(selectedDeal.id).completed} of {getDocumentProgress(selectedDeal.id).total} documents
                    ({getDocumentProgress(selectedDeal.id).percentage}%)
                  </p>
                </div>
              )}

              <div className="modal-actions">
                <button className="btn-primary">Submit to DigiLocker</button>
                <button className="btn-secondary">📨 Request Missing Docs</button>
                <button className="btn-secondary" onClick={() => setShowDigi(false)}>Close</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
