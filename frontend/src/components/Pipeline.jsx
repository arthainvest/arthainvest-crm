import React, { useState, useEffect } from 'react';
import { getDeals, getLeads, createDeal, createLead, getTeam, assignDeal, updateDealProcessStatus, getDealQuotations, getCompanies, linkDealCompany, getDealDocuments, updateDealDocument, sendWhatsApp } from '../services/api';
import { LOAN_PRODUCTS } from '../constants/loanProducts';
import '../styles/Pipeline.css';

const FolderIcon = () => (
  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
    <path d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
  </svg>
);

export default function Pipeline() {
  const PROCESS_STATUS_OPTIONS = [
    'Document Collection', 'Login', 'Under Verification', 'Approved', 'Sanction',
    'Disbursement Pending', 'Disbursed', 'Hold', 'Rejected', 'Closed - Lost'
  ];

  const processStatusClass = (status) => `status-${(status || 'Login').toLowerCase().replace(/[^a-z0-9]+/g, '-')}`;

  const [deals, setDeals] = useState([]);
  const [leads, setLeads] = useState([]);
  const [teamMembers, setTeamMembers] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [showDigi, setShowDigi] = useState(false);
  const [selectedDeal, setSelectedDeal] = useState(null);
  const [uploadedDocs, setUploadedDocs] = useState({});
  const [loadingDocChecklist, setLoadingDocChecklist] = useState(false);
  const [showQuotations, setShowQuotations] = useState(false);
  const [quotationsForDeal, setQuotationsForDeal] = useState([]);
  const [loadingDealQuotations, setLoadingDealQuotations] = useState(false);
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

  // Backend deals carry {id, lead_id, deal_value, stage, probability, loan_product,
  // expected_close_date, created_at} - no name/company/phone/processStatus, stage is lowercase,
  // and probability is a 0-1 fraction. leadsById fills in the display fields from the matching
  // lead (fetched separately, since /api/deals doesn't join lead data). Normalize into the shape
  // the rest of this component expects.
  const normalizeDeal = (d, leadsById) => {
    const lead = leadsById?.[d.lead_id];
    return {
      id: d.id,
      name: d.name || lead?.name || `Lead #${d.lead_id}`,
      company: d.company || lead?.company || '—',
      value: d.value ?? Math.round((d.deal_value ?? 0) / 1000),
      phone: d.phone || lead?.phone || '—',
      loanProduct: d.loan_product || d.loanProduct || lead?.product || 'LAP',
      stage: STAGES.find((s) => s.toLowerCase() === String(d.stage).toLowerCase()) || 'New',
      probability: d.probability > 1 ? Math.round(d.probability) : Math.round((d.probability ?? 0) * 100),
      processStatus: d.process_status || d.processStatus || 'Login',
      assignedTeamMemberId: d.assigned_team_member_id ?? null,
      assignedTeamMemberName: d.assigned_team_member_name ?? null,
      quotationCount: d.quotation_count ?? 0,
      companyId: d.company_id ?? null,
      companyName: d.company_name ?? null
    };
  };

  useEffect(() => {
    fetchDeals();
    fetchTeamMembers();
    fetchCompanies();
  }, []);

  const fetchTeamMembers = async () => {
    try {
      const data = await getTeam(token);
      setTeamMembers(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching team members:', error);
    }
  };

  const fetchCompanies = async () => {
    try {
      const data = await getCompanies(token);
      setCompanies(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching companies:', error);
    }
  };

  const handleCompanyLinkChange = async (dealId, companyIdRaw) => {
    const companyId = companyIdRaw ? Number(companyIdRaw) : null;
    const previous = deals.find((d) => d.id === dealId);
    setDeals((prev) => prev.map((d) => (d.id === dealId
      ? { ...d, companyId, companyName: companies.find((c) => c.id === companyId)?.name || null }
      : d)));
    try {
      await linkDealCompany(token, dealId, companyId);
    } catch (error) {
      console.error('Error linking deal to company:', error);
      if (previous) {
        setDeals((prev) => prev.map((d) => (d.id === dealId ? previous : d)));
      }
      alert('Failed to link company. Please try again.');
    }
  };

  const handleAssignChange = async (dealId, teamMemberIdRaw) => {
    const teamMemberId = teamMemberIdRaw === '' ? null : Number(teamMemberIdRaw);
    // Optimistic update so the dropdown feels instant; fetchDeals() would also pick up the
    // real name from the backend, but there's no need to round-trip for something this simple.
    const member = teamMembers.find((m) => m.id === teamMemberId);
    setDeals((prev) => prev.map((d) => (
      d.id === dealId ? { ...d, assignedTeamMemberId: teamMemberId, assignedTeamMemberName: member?.name || null } : d
    )));
    try {
      await assignDeal(token, dealId, teamMemberId);
    } catch (error) {
      console.error('Error assigning deal:', error);
      alert('Failed to update assignment. Please try again.');
      fetchDeals();
    }
  };

  const fetchDeals = async () => {
    try {
      const dealsData = await getDeals(token);
      if (Array.isArray(dealsData)) {
        let leadsById = {};
        try {
          const leadsData = await getLeads(token);
          if (Array.isArray(leadsData)) {
            leadsById = leadsData.reduce((acc, lead) => ({ ...acc, [lead.id]: lead }), {});
            setLeads(leadsData);
          }
        } catch (leadsError) {
          console.error('Error fetching leads for deal names:', leadsError);
        }
        setDeals(dealsData.map((d) => normalizeDeal(d, leadsById)));
      } else {
        setDeals([]);
      }
    } catch (error) {
      console.error('Error fetching deals:', error);
      setDeals([]);
    }
  };

  const handleAddDeal = async () => {
    if (!formData.name || !formData.company || !formData.value) return;

    try {
      // Deals are always attached to a lead on the backend - creating one here first, then
      // the deal against it, matches how a genuinely new client actually enters the pipeline.
      const newLead = await createLead(token, {
        name: formData.name,
        company: formData.company,
        phone: formData.phone
      });
      await createDeal(token, {
        lead_id: newLead.id,
        deal_value: parseInt(formData.value) * 1000,
        probability: Number(formData.probability) / 100,
        loan_product: formData.loanProduct,
        stage: formData.stage
      });
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
      fetchDeals();
    } catch (error) {
      console.error('Error creating deal:', error);
      alert('Failed to create deal. Please try again.');
    }
  };

  const handleViewQuotations = async (deal) => {
    setSelectedDeal(deal);
    setShowQuotations(true);
    setLoadingDealQuotations(true);
    try {
      const data = await getDealQuotations(token, deal.id);
      setQuotationsForDeal(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching quotations for deal:', error);
      setQuotationsForDeal([]);
    } finally {
      setLoadingDealQuotations(false);
    }
  };

  const handleDigiLocker = async (deal) => {
    setSelectedDeal(deal);
    setShowDigi(true);
    setLoadingDocChecklist(true);
    try {
      const data = await getDealDocuments(token, deal.id);
      const collectedMap = {};
      (Array.isArray(data) ? data : []).forEach((d) => {
        if (d.collected) collectedMap[d.document_name] = true;
      });
      setUploadedDocs((prev) => ({ ...prev, [deal.id]: collectedMap }));
    } catch (error) {
      console.error('Error fetching document checklist:', error);
      setUploadedDocs((prev) => ({ ...prev, [deal.id]: {} }));
    } finally {
      setLoadingDocChecklist(false);
    }
  };

  const handleDocumentCheck = async (dealId, doc) => {
    const wasChecked = uploadedDocs[dealId]?.[doc] || false;
    const nowChecked = !wasChecked;
    setUploadedDocs((prev) => ({
      ...prev,
      [dealId]: { ...prev[dealId], [doc]: nowChecked }
    }));
    try {
      await updateDealDocument(token, dealId, doc, nowChecked);
    } catch (error) {
      console.error('Error updating document checklist:', error);
      setUploadedDocs((prev) => ({
        ...prev,
        [dealId]: { ...prev[dealId], [doc]: wasChecked }
      }));
      alert('Failed to update checklist. Please try again.');
    }
  };

  const handleRequestMissingDocs = async () => {
    if (!selectedDeal) return;
    const required = LOAN_DOCUMENTS[selectedDeal.loanProduct] || [];
    const collected = uploadedDocs[selectedDeal.id] || {};
    const missing = required.filter((doc) => !collected[doc]);

    if (missing.length === 0) {
      alert('All required documents are already marked collected.');
      return;
    }
    if (!selectedDeal.phone || selectedDeal.phone === '—') {
      alert('No phone number on file for this client.');
      return;
    }

    const message = `Hi ${selectedDeal.name}, to proceed with your ${getLoanProductInfo(selectedDeal.loanProduct)?.name || selectedDeal.loanProduct} application we still need: ${missing.join(', ')}. Please share these at your earliest convenience.`;
    try {
      await sendWhatsApp(token, selectedDeal.phone, message);
      alert('WhatsApp message sent.');
    } catch (error) {
      console.error('Error sending missing-documents WhatsApp message:', error);
      alert('Failed to send WhatsApp message. Please try again.');
    }
  };

  const getDocumentProgress = (dealId) => {
    const docs = uploadedDocs[dealId] || {};
    const total = (LOAN_DOCUMENTS[selectedDeal.loanProduct] || []).length;
    const completed = Object.values(docs).filter(v => v).length;
    return { completed, total, percentage: total > 0 ? Math.round((completed / total) * 100) : 0 };
  };

  const handleProcessStatusChange = async (dealId, newStatus) => {
    const previous = deals.find((d) => d.id === dealId);
    setDeals((prev) => prev.map((d) => (d.id === dealId ? { ...d, processStatus: newStatus } : d)));
    try {
      await updateDealProcessStatus(token, dealId, newStatus);
    } catch (error) {
      console.error('Error updating deal process status:', error);
      if (previous) {
        setDeals((prev) => prev.map((d) => (d.id === dealId ? previous : d)));
      }
      alert('Failed to update status. Please try again.');
    }
  };

  const getDealsByStage = (stage) => {
    if (!deals || !Array.isArray(deals)) {
      return [];
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

      <div className="pipeline-overview">
        {/* Funnel summary */}
        <div className="funnel-panel">
          <div className="funnel-card funnel-new">
            <h3>New Leads ({leads.filter((l) => l.status === 'New').length})</h3>
            <p>Fresh contacts imported</p>
          </div>
          <div className="funnel-card funnel-contacted">
            <h3>Contacted ({leads.filter((l) => l.status === 'Contacted').length})</h3>
            <p>Initial outreach completed</p>
          </div>
          <div className="funnel-card funnel-interested">
            <h3>Interested ({leads.filter((l) => l.status === 'Interested').length})</h3>
            <p>Follow-up scheduled</p>
          </div>
          <div className="funnel-card funnel-proposal">
            <h3>Proposal ({getDealsByStage('Proposal').length})</h3>
            <p>Awaiting decision</p>
          </div>
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
                  <th>Employee</th>
                  <th>Company</th>
                  <th>Status</th>
                  <th>Quotations</th>
                </tr>
              </thead>
              <tbody>
                {deals.length === 0 && (
                  <tr>
                    <td colSpan={8} className="no-data">No deals yet. Add one to get started.</td>
                  </tr>
                )}
                {deals.map((deal) => {
                  const loanInfo = getLoanProductInfo(deal.loanProduct);
                  return (
                    <tr key={deal.id}>
                      <td>
                        <button
                          type="button"
                          className="folder-icon-btn"
                          onClick={() => handleDigiLocker(deal)}
                          title="Loan Document Checklist"
                        >
                          <FolderIcon />
                        </button>
                      </td>
                      <td className="pipeline-client-name">{deal.name}</td>
                      <td>₹{deal.value}K</td>
                      <td>{loanInfo?.icon} {loanInfo?.name}</td>
                      <td>
                        <select
                          className="employee-assign-select"
                          value={deal.assignedTeamMemberId ?? ''}
                          onChange={(e) => handleAssignChange(deal.id, e.target.value)}
                        >
                          <option value="">Unassigned</option>
                          {teamMembers.map((m) => (
                            <option key={m.id} value={m.id}>{m.name}</option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <select
                          className="company-link-select"
                          value={deal.companyId ?? ''}
                          onChange={(e) => handleCompanyLinkChange(deal.id, e.target.value)}
                          title="Linked company"
                        >
                          <option value="">🏢 No linked company</option>
                          {companies.map((co) => (
                            <option key={co.id} value={co.id}>🏢 {co.name}</option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <select
                          className={`process-status-select ${processStatusClass(deal.processStatus)}`}
                          value={deal.processStatus || 'Login'}
                          onChange={(e) => handleProcessStatusChange(deal.id, e.target.value)}
                        >
                          {PROCESS_STATUS_OPTIONS.map((s) => (
                            <option key={s} value={s}>{s}</option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <button
                          type="button"
                          className="quotations-count-btn"
                          onClick={() => handleViewQuotations(deal)}
                          title="View quotations linked to this deal"
                        >
                          📋 {deal.quotationCount || 0}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
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

      {/* Loan Document Checklist Modal */}
      {showDigi && selectedDeal && (
        <div className="modal-overlay" onClick={() => setShowDigi(false)}>
          <div className="modal-content digi-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>📋 Loan Document Checklist</h2>
              <button className="btn-close" onClick={() => setShowDigi(false)}>×</button>
            </div>

            <div className="modal-body">
              <div className="digi-info">
                <h3>{selectedDeal.name}</h3>
                <p><strong>Company:</strong> {selectedDeal.company}</p>
                <p><strong>Loan Type:</strong> {getLoanProductInfo(selectedDeal.loanProduct)?.name}</p>
                <p><strong>Amount:</strong> ₹{selectedDeal.value}K</p>
              </div>

              {loadingDocChecklist ? (
                <p className="no-data-inline">Loading checklist…</p>
              ) : (
                <>
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
                </>
              )}

              <div className="modal-actions">
                <button className="btn-secondary" onClick={handleRequestMissingDocs} disabled={loadingDocChecklist}>
                  📨 Request Missing Docs
                </button>
                <button className="btn-secondary" onClick={() => setShowDigi(false)}>Close</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Linked Quotations Modal */}
      {showQuotations && selectedDeal && (
        <div className="modal-overlay" onClick={() => setShowQuotations(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>📋 Quotations - {selectedDeal.name}</h2>
              <button className="btn-close" onClick={() => setShowQuotations(false)}>×</button>
            </div>
            <div className="modal-body">
              {loadingDealQuotations ? (
                <p className="no-data-inline">Loading…</p>
              ) : quotationsForDeal.length === 0 ? (
                <p className="no-data-inline">No quotations linked to this deal yet. Create one from the Quotations page and link it here.</p>
              ) : (
                <ul className="deal-quotations-list">
                  {quotationsForDeal.map((q) => (
                    <li key={q.id}>
                      <strong>{q.quotation_number}</strong> - {q.title}
                      <span className={`deal-quotation-status status-${(q.status || '').toLowerCase()}`}>{q.status}</span>
                      <span className="deal-quotation-total">₹{(q.grand_total || 0).toLocaleString('en-IN')}</span>
                    </li>
                  ))}
                </ul>
              )}
              <div className="modal-actions">
                <button className="btn-secondary" onClick={() => setShowQuotations(false)}>Close</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
