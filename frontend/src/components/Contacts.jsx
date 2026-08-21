import React, { useState, useEffect } from 'react';
import '../styles/Contacts.css';

export default function Contacts() {
  const [contacts, setContacts] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [showCommunication, setShowCommunication] = useState(false);
  const [showDigi, setShowDigi] = useState(false);
  const [communicationTab, setCommunicationTab] = useState('message');
  const [selectedContact, setSelectedContact] = useState(null);
  const [message, setMessage] = useState('');
  const [emailSubject, setEmailSubject] = useState('');
  const [emailBody, setEmailBody] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchContacts();
  }, []);

  const fetchContacts = async () => {
    try {
      const response = await fetch('/api/contacts');
      const data = await response.json();
      setContacts(data);
    } catch (error) {
      console.error('Error fetching contacts:', error);
      setContacts(mockContacts);
    }
  };

  const handleCall = (contact) => {
    if (contact.phone) {
      window.location.href = `tel:${contact.phone}`;
    } else {
      alert('No phone number available');
    }
  };

  const handleWhatsApp = (contact) => {
    if (contact.phone) {
      const url = `https://wa.me/${contact.phone.replace(/\D/g, '')}`;
      window.open(url, '_blank');
    }
  };

  const handleMessage = (contact) => {
    setSelectedContact(contact);
    setCommunicationTab('message');
    setShowCommunication(true);
  };

  const handleEmail = (contact) => {
    setSelectedContact(contact);
    setCommunicationTab('email');
    setShowCommunication(true);
  };

  const handleDigi = (contact) => {
    setSelectedContact(contact);
    setShowDigi(true);
  };

  const sendMessage = () => {
    if (message.trim()) {
      alert(`Message sent to ${selectedContact.name}: ${message}`);
      setMessage('');
      setShowCommunication(false);
    }
  };

  const sendEmail = () => {
    if (emailSubject.trim() && emailBody.trim()) {
      window.location.href = `mailto:${selectedContact.email}?subject=${encodeURIComponent(emailSubject)}&body=${encodeURIComponent(emailBody)}`;
      setEmailSubject('');
      setEmailBody('');
      setShowCommunication(false);
    }
  };

  const filteredContacts = contacts.filter(c =>
    c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="contacts-container">
      <div className="contacts-header">
        <h1>Contacts</h1>
        <button className="btn-primary" onClick={() => setShowForm(true)}>+ Add Contact</button>
      </div>

      <div className="search-bar">
        <input
          type="text"
          placeholder="Search contacts by name or email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="contacts-grid">
        {filteredContacts.map(contact => (
          <div key={contact.id} className="contact-card">
            <div className="card-header">
              <h3>{contact.name}</h3>
              <span className="score-badge">{contact.score}%</span>
            </div>

            <div className="card-info">
              <p><strong>Company:</strong> {contact.company}</p>
              <p><strong>Email:</strong> {contact.email}</p>
              <p><strong>Phone:</strong> {contact.phone}</p>
              <p><strong>Tier:</strong> <span className={`tier-${contact.tier.toLowerCase()}`}>{contact.tier}</span></p>
            </div>

            <div className="action-buttons">
              <button className="btn-action call" onClick={() => handleCall(contact)} title="Click to Call">☎️</button>
              <button className="btn-action message" onClick={() => handleMessage(contact)} title="Direct Message">💬</button>
              <button className="btn-action email" onClick={() => handleEmail(contact)} title="Send Email">📧</button>
              <button className="btn-action whatsapp" onClick={() => handleWhatsApp(contact)} title="WhatsApp">📱</button>
              <button className="btn-action digilocker" onClick={() => handleDigi(contact)} title="DigiLocker">🔐</button>
              <button className="btn-action edit" onClick={() => alert('Edit feature coming')}>✏️</button>
              <button className="btn-action delete" onClick={() => alert('Delete feature coming')}>🗑️</button>
            </div>
          </div>
        ))}
      </div>

      {/* Communication Modal */}
      {showCommunication && selectedContact && (
        <div className="modal-overlay" onClick={() => setShowCommunication(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{communicationTab === 'message' ? 'Send Message' : 'Send Email'} to {selectedContact.name}</h2>
              <button className="btn-close" onClick={() => setShowCommunication(false)}>×</button>
            </div>

            {communicationTab === 'message' && (
              <div className="modal-body">
                <textarea
                  placeholder="Type your message..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  rows="6"
                />
                <div className="modal-actions">
                  <button className="btn-primary" onClick={sendMessage}>Send Message</button>
                  <button className="btn-secondary" onClick={() => setShowCommunication(false)}>Cancel</button>
                </div>
              </div>
            )}

            {communicationTab === 'email' && (
              <div className="modal-body">
                <div className="form-group">
                  <label>Subject:</label>
                  <input
                    type="text"
                    placeholder="Email subject..."
                    value={emailSubject}
                    onChange={(e) => setEmailSubject(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>Message:</label>
                  <textarea
                    placeholder="Email body..."
                    value={emailBody}
                    onChange={(e) => setEmailBody(e.target.value)}
                    rows="6"
                  />
                </div>
                <div className="modal-actions">
                  <button className="btn-primary" onClick={sendEmail}>Send Email</button>
                  <button className="btn-secondary" onClick={() => setShowCommunication(false)}>Cancel</button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* DigiLocker Modal */}
      {showDigi && selectedContact && (
        <div className="modal-overlay" onClick={() => setShowDigi(false)}>
          <div className="modal-content digi-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>DigiLocker - Document Management</h2>
              <button className="btn-close" onClick={() => setShowDigi(false)}>×</button>
            </div>

            <div className="modal-body">
              <div className="digi-info">
                <h3>{selectedContact.name}</h3>
                <p>{selectedContact.company} | {selectedContact.email} | {selectedContact.phone}</p>
              </div>

              <div className="digi-section">
                <h4>Verified Documents</h4>
                <div className="verified-docs">
                  <div className="doc-item">
                    <input type="checkbox" defaultChecked /> PAN Card
                  </div>
                  <div className="doc-item">
                    <input type="checkbox" defaultChecked /> Aadhar Card
                  </div>
                  <div className="doc-item">
                    <input type="checkbox" /> Bank Statement
                  </div>
                  <div className="doc-item">
                    <input type="checkbox" /> ITR (Income Tax Return)
                  </div>
                </div>
              </div>

              <div className="digi-section">
                <h4>Document Options</h4>
                <div className="digi-options">
                  <button className="digi-btn">✓ Request from Aadhar</button>
                  <button className="digi-btn">✓ Request PAN</button>
                  <button className="digi-btn">📄 Upload Bank Statement</button>
                  <button className="digi-btn">📄 Upload ITR</button>
                </div>
              </div>

              <div className="modal-actions">
                <button className="btn-primary">Submit to DigiLocker</button>
                <button className="btn-secondary" onClick={() => setShowDigi(false)}>Close</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const mockContacts = [
  {
    id: 1,
    name: 'Neha Singh',
    company: 'Tech Startup',
    email: 'neha@techstartup.com',
    phone: '+91-9876543210',
    score: 85,
    tier: 'Premium'
  },
  {
    id: 2,
    name: 'Vikram Reddy',
    company: 'Tech Park',
    email: 'vikram@techpark.com',
    phone: '+91-9876543211',
    score: 72,
    tier: 'Gold'
  },
  {
    id: 3,
    name: 'Anjali Desai',
    company: 'Retail Chain',
    email: 'anjali@retail.com',
    phone: '+91-9876543212',
    score: 65,
    tier: 'Silver'
  },
  {
    id: 4,
    name: 'Amit Patel',
    company: 'Manufacturing',
    email: 'amit@mfg.com',
    phone: '+91-9876543213',
    score: 58,
    tier: 'Silver'
  },
  {
    id: 5,
    name: 'Priya Kapoor',
    company: 'Digital Ventures',
    email: 'priya@digital.com',
    phone: '+91-9876543214',
    score: 80,
    tier: 'Premium'
  }
];
