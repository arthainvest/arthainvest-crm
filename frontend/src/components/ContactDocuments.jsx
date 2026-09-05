import React, { useState, useEffect, useCallback, useRef } from 'react';
import { getContactDocuments, uploadContactDocument, deleteContactDocument, API_URL } from '../services/api';

const DOCUMENT_TYPES = [
  'PAN', 'Aadhar', 'CIBIL Report', 'Bank Statement', 'ITR', 'Photo', 'Signature',
  'Business Profile', 'Insurance Document', 'Loan Document', 'Other'
];

export default function ContactDocuments({ token, contact, onClose }) {
  const [documents, setDocuments] = useState([]);
  const [documentType, setDocumentType] = useState('PAN');
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const fetchDocuments = useCallback(async () => {
    try {
      const data = await getContactDocuments(token, contact.id);
      setDocuments(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  }, [token, contact.id]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    try {
      await uploadContactDocument(token, contact.id, documentType, file);
      await fetchDocuments();
    } catch (error) {
      console.error('Error uploading document:', error);
      alert('Failed to upload document. Please try again.');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleDelete = async (documentId) => {
    if (!window.confirm('Remove this document from the client\'s record?')) return;
    try {
      await deleteContactDocument(token, contact.id, documentId);
      setDocuments((prev) => prev.filter((d) => d.id !== documentId));
    } catch (error) {
      console.error('Error deleting document:', error);
      alert('Failed to delete document. Please try again.');
    }
  };

  const fileUrl = (doc) => {
    if (doc.file_url.startsWith('http')) return doc.file_url;
    const sep = doc.file_url.includes('?') ? '&' : '?';
    return `${API_URL}${doc.file_url}${sep}token=${token}`;
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content digi-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>📁 Client Documents</h2>
          <button className="btn-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          <div className="digi-info">
            <h3>{contact.name}</h3>
            <p>{contact.company} | {contact.email} | {contact.phone}</p>
          </div>

          <div className="digi-section">
            <h4>Uploaded Documents</h4>
            {documents.length === 0 ? (
              <p className="portfolio-empty">No documents uploaded yet.</p>
            ) : (
              <div className="verified-docs">
                {documents.map((doc) => (
                  <div className="doc-item" key={doc.id} style={{ justifyContent: 'space-between', display: 'flex', alignItems: 'center' }}>
                    <a href={fileUrl(doc)} target="_blank" rel="noopener noreferrer">
                      {doc.document_type}: {doc.file_name}
                    </a>
                    <button type="button" onClick={() => handleDelete(doc.id)} title="Delete">🗑️</button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="digi-section">
            <h4>Upload a Document</h4>
            <div className="digi-options">
              <select value={documentType} onChange={(e) => setDocumentType(e.target.value)}>
                {DOCUMENT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
              <button type="button" className="digi-btn" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
                {uploading ? 'Uploading...' : '📄 Choose File & Upload'}
              </button>
              <input
                type="file" ref={fileInputRef} style={{ display: 'none' }}
                onChange={handleFileChange}
              />
            </div>
          </div>

          <div className="modal-actions">
            <button className="btn-secondary" onClick={onClose}>Close</button>
          </div>
        </div>
      </div>
    </div>
  );
}
