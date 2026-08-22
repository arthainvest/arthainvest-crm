import React, { useState, useEffect, useRef } from 'react';
import { getLeads, createLead, updateLead, deleteLead } from '../services/api';
import '../styles/LeadsList.css';

export default function LeadsList() {
  const mockLeads = [
    { id: 1, name: 'Neha Singh', company: 'Startup Fund', email: 'neha@startup.com', phone: '+91-9876543210', status: 'New', ai_score: 85 },
    { id: 2, name: 'Vikram Reddy', company: 'Tech Park', email: 'vikram@techpark.com', phone: '+91-9876543211', status: 'Contacted', ai_score: 72 },
    { id: 3, name: 'Anjali Desai', company: 'Retail Chain', email: 'anjali@retail.com', phone: '+91-9876543212', status: 'Interested', ai_score: 65 },
    { id: 4, name: 'Amit Patel', company: 'Manufacturing', email: 'amit@mfg.com', phone: '+91-9876543213', status: 'Qualified', ai_score: 58 },
    { id: 5, name: 'Priya Kapoor', company: 'Digital Ventures', email: 'priya@digital.com', phone: '+91-9876543214', status: 'New', ai_score: 80 }
  ];

  const [leads, setLeads] = useState(mockLeads);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    company: '',
    email: '',
    phone: '',
    product: '',
    source: '',
  });
  const token = localStorage.getItem('token');

  // Communication modal state
  const [showCommunication, setShowCommunication] = useState(false);
  const [communicationTab, setCommunicationTab] = useState('message');
  const [selectedLead, setSelectedLead] = useState(null);
  const [message, setMessage] = useState('');
  const [emailSubject, setEmailSubject] = useState('');
  const [emailBody, setEmailBody] = useState('');

  // DigiLocker modal state
  const [showDigi, setShowDigi] = useState(false);

  // Notes & voice-note state
  const [showNotes, setShowNotes] = useState(false);
  const [leadNotes, setLeadNotes] = useState({});
  const [noteDraft, setNoteDraft] = useState({ callDateTime: '', nextConversation: '', transcript: '' });
  const [isRecording, setIsRecording] = useState(false);
  const [draftAudioUrl, setDraftAudioUrl] = useState(null);
  const [speechSupported] = useState(() => !!(window.SpeechRecognition || window.webkitSpeechRecognition));
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recognitionRef = useRef(null);

  useEffect(() => {
    fetchLeads();
  }, []);

  const fetchLeads = async () => {
    try {
      const data = await getLeads(token);
      if (Array.isArray(data) && data.length > 0) {
        setLeads(data);
      } else {
        setLeads(mockLeads);
      }
    } catch (err) {
      console.error('Failed to fetch leads:', err);
      setLeads(mockLeads);
    } finally {
      setLoading(false);
    }
  };

  const handleAddLead = async (e) => {
    e.preventDefault();
    try {
      await createLead(token, formData);
      setFormData({
        name: '',
        company: '',
        email: '',
        phone: '',
        product: '',
        source: '',
      });
      setShowModal(false);
      fetchLeads();
    } catch (err) {
      console.error('Failed to create lead:', err);
      alert('Error creating lead');
    }
  };

  const handleDeleteLead = async (id) => {
    if (window.confirm('Are you sure you want to delete this lead?')) {
      try {
        await deleteLead(token, id);
        fetchLeads();
      } catch (err) {
        console.error('Failed to delete lead:', err);
        alert('Error deleting lead');
      }
    }
  };

  const handleCall = (lead) => {
    if (lead.phone) {
      window.location.href = `tel:${lead.phone}`;
    } else {
      alert('No phone number available');
    }
  };

  const handleWhatsApp = (lead) => {
    if (lead.phone) {
      const url = `https://wa.me/${lead.phone.replace(/\D/g, '')}`;
      window.open(url, '_blank');
    }
  };

  const handleMessage = (lead) => {
    setSelectedLead(lead);
    setCommunicationTab('message');
    setShowCommunication(true);
  };

  const handleEmail = (lead) => {
    setSelectedLead(lead);
    setCommunicationTab('email');
    setShowCommunication(true);
  };

  const sendMessage = () => {
    if (message.trim()) {
      alert(`Message sent to ${selectedLead.name}: ${message}`);
      setMessage('');
      setShowCommunication(false);
    }
  };

  const sendEmail = () => {
    if (emailSubject.trim() && emailBody.trim()) {
      window.location.href = `mailto:${selectedLead.email}?subject=${encodeURIComponent(emailSubject)}&body=${encodeURIComponent(emailBody)}`;
      setEmailSubject('');
      setEmailBody('');
      setShowCommunication(false);
    }
  };

  const handleDigi = (lead) => {
    setSelectedLead(lead);
    setShowDigi(true);
  };

  const handleNotes = (lead) => {
    setSelectedLead(lead);
    setNoteDraft({
      callDateTime: new Date().toISOString().slice(0, 16),
      nextConversation: '',
      transcript: ''
    });
    setDraftAudioUrl(null);
    setIsRecording(false);
    setShowNotes(true);
  };

  const closeNotes = () => {
    if (isRecording) stopRecording();
    setShowNotes(false);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const recorder = new MediaRecorder(stream);
      recorder.ondataavailable = (e) => audioChunksRef.current.push(e.data);
      recorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setDraftAudioUrl(URL.createObjectURL(blob));
        stream.getTracks().forEach((t) => t.stop());
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);

      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-IN';
        let finalTranscript = '';
        recognition.onresult = (event) => {
          let interim = '';
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const text = event.results[i][0].transcript;
            if (event.results[i].isFinal) finalTranscript += text + ' ';
            else interim += text;
          }
          setNoteDraft((prev) => ({ ...prev, transcript: (finalTranscript + interim).trim() }));
        };
        recognition.onerror = (e) => console.error('Speech recognition error:', e.error);
        recognition.start();
        recognitionRef.current = recognition;
      }
    } catch (err) {
      alert('Microphone access denied or unavailable: ' + err.message);
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    recognitionRef.current?.stop();
    recognitionRef.current = null;
    setIsRecording(false);
  };

  const saveNote = () => {
    if (!selectedLead) return;
    if (!noteDraft.transcript.trim() && !draftAudioUrl) {
      alert('Add a transcript note or record a voice note before saving.');
      return;
    }
    const entry = {
      id: Date.now(),
      callDateTime: noteDraft.callDateTime,
      nextConversation: noteDraft.nextConversation,
      transcript: noteDraft.transcript.trim(),
      audioUrl: draftAudioUrl,
      createdAt: new Date().toLocaleString()
    };
    setLeadNotes((prev) => ({
      ...prev,
      [selectedLead.id]: [entry, ...(prev[selectedLead.id] || [])]
    }));
    setNoteDraft({
      callDateTime: new Date().toISOString().slice(0, 16),
      nextConversation: '',
      transcript: ''
    });
    setDraftAudioUrl(null);
  };

  const deleteNote = (leadId, noteId) => {
    setLeadNotes((prev) => ({
      ...prev,
      [leadId]: (prev[leadId] || []).filter((n) => n.id !== noteId)
    }));
  };

  const displayLeads = (leads && leads.length > 0) ? leads : mockLeads;

  return (
    <div className="leads-container">
      <div className="leads-header">
        <h1>Leads</h1>
        <button
          className="btn-primary"
          onClick={() => setShowModal(true)}
        >
          + New Lead
        </button>
      </div>

      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h2>Add New Lead</h2>
              <button
                className="modal-close"
                onClick={() => setShowModal(false)}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddLead}>
              <div className="form-group">
                <label>Name *</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                />
              </div>

              <div className="form-group">
                <label>Company</label>
                <input
                  type="text"
                  value={formData.company}
                  onChange={(e) =>
                    setFormData({ ...formData, company: e.target.value })
                  }
                />
              </div>

              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                />
              </div>

              <div className="form-group">
                <label>Phone</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) =>
                    setFormData({ ...formData, phone: e.target.value })
                  }
                />
              </div>

              <div className="form-group">
                <label>Product</label>
                <input
                  type="text"
                  value={formData.product}
                  onChange={(e) =>
                    setFormData({ ...formData, product: e.target.value })
                  }
                />
              </div>

              <div className="form-group">
                <label>Source</label>
                <input
                  type="text"
                  value={formData.source}
                  onChange={(e) =>
                    setFormData({ ...formData, source: e.target.value })
                  }
                />
              </div>

              <div className="modal-actions">
                <button type="submit" className="btn-primary">
                  Create Lead
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowModal(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {displayLeads && displayLeads.length > 0 ? (
        <table className="leads-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Company</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Status</th>
              <th>Score</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {displayLeads.map((lead) => (
              <tr key={lead.id}>
                <td>{lead.name}</td>
                <td>{lead.company || '-'}</td>
                <td>{lead.email || '-'}</td>
                <td>{lead.phone || '-'}</td>
                <td>
                  <span className={`status-badge ${lead.status}`}>
                    {lead.status}
                  </span>
                </td>
                <td>{lead.ai_score || '-'}</td>
                <td>
                  <div className="action-buttons">
                    <button className="btn-action call" onClick={() => handleCall(lead)} title="Click to Call">☎️</button>
                    <button className="btn-action message" onClick={() => handleMessage(lead)} title="Direct Message">💬</button>
                    <button className="btn-action email" onClick={() => handleEmail(lead)} title="Send Email">📧</button>
                    <button className="btn-action whatsapp" onClick={() => handleWhatsApp(lead)} title="WhatsApp">📱</button>
                    <button className="btn-action digilocker" onClick={() => handleDigi(lead)} title="DigiLocker">🔐</button>
                    <button className="btn-action notes" onClick={() => handleNotes(lead)} title="Notes & Follow-up">📝</button>
                    <button
                      className="btn-danger"
                      onClick={() => handleDeleteLead(lead.id)}
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="no-data">No leads yet. Create your first lead!</p>
      )}

      {/* Communication Modal */}
      {showCommunication && selectedLead && (
        <div className="modal-overlay" onClick={() => setShowCommunication(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{communicationTab === 'message' ? 'Send Message' : 'Send Email'} to {selectedLead.name}</h2>
              <button className="modal-close" onClick={() => setShowCommunication(false)}>✕</button>
            </div>

            {communicationTab === 'message' && (
              <>
                <div className="form-group">
                  <label>Message</label>
                  <textarea
                    placeholder="Type your message..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    rows="6"
                  />
                </div>
                <div className="modal-actions">
                  <button className="btn-primary" onClick={sendMessage}>Send Message</button>
                  <button className="btn-secondary" onClick={() => setShowCommunication(false)}>Cancel</button>
                </div>
              </>
            )}

            {communicationTab === 'email' && (
              <>
                <div className="form-group">
                  <label>Subject</label>
                  <input
                    type="text"
                    placeholder="Email subject..."
                    value={emailSubject}
                    onChange={(e) => setEmailSubject(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>Message</label>
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
              </>
            )}
          </div>
        </div>
      )}

      {/* DigiLocker Modal */}
      {showDigi && selectedLead && (
        <div className="modal-overlay" onClick={() => setShowDigi(false)}>
          <div className="modal-content digi-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>DigiLocker - Document Management</h2>
              <button className="modal-close" onClick={() => setShowDigi(false)}>✕</button>
            </div>

            <div className="digi-info">
              <h3>{selectedLead.name}</h3>
              <p>{selectedLead.company} | {selectedLead.email} | {selectedLead.phone}</p>
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
      )}

      {/* Notes & Follow-up Modal */}
      {showNotes && selectedLead && (
        <div className="modal-overlay" onClick={closeNotes}>
          <div className="modal-content notes-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>📝 Notes & Follow-up - {selectedLead.name}</h2>
              <button className="modal-close" onClick={closeNotes}>✕</button>
            </div>

            <div className="notes-form">
              <div className="form-row">
                <div className="form-group">
                  <label>Call Date &amp; Time</label>
                  <input
                    type="datetime-local"
                    value={noteDraft.callDateTime}
                    onChange={(e) => setNoteDraft({ ...noteDraft, callDateTime: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Next Conversation</label>
                  <input
                    type="datetime-local"
                    value={noteDraft.nextConversation}
                    onChange={(e) => setNoteDraft({ ...noteDraft, nextConversation: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Notes / AI Transcript</label>
                <textarea
                  rows="5"
                  placeholder={speechSupported ? 'Type notes, or record a voice note to auto-transcribe...' : 'Type notes here...'}
                  value={noteDraft.transcript}
                  onChange={(e) => setNoteDraft({ ...noteDraft, transcript: e.target.value })}
                />
              </div>

              <div className="voice-note-controls">
                {!isRecording ? (
                  <button type="button" className="btn-record" onClick={startRecording}>
                    🎙️ Start Voice Note
                  </button>
                ) : (
                  <button type="button" className="btn-record recording" onClick={stopRecording}>
                    <span className="rec-dot">●</span> Stop Recording
                  </button>
                )}
                {!speechSupported && (
                  <span className="voice-note-hint">AI live transcription needs Chrome/Edge - recording still works.</span>
                )}
                {draftAudioUrl && (
                  <audio controls src={draftAudioUrl} className="voice-playback" />
                )}
              </div>

              <div className="modal-actions">
                <button className="btn-primary" onClick={saveNote}>💾 Save Note</button>
              </div>
            </div>

            <div className="notes-history">
              <h4>History ({(leadNotes[selectedLead.id] || []).length})</h4>
              {(leadNotes[selectedLead.id] || []).length === 0 ? (
                <p className="no-notes">No notes yet for this lead.</p>
              ) : (
                (leadNotes[selectedLead.id] || []).map((note) => (
                  <div key={note.id} className="note-entry">
                    <div className="note-entry-header">
                      <span>📞 {note.callDateTime ? new Date(note.callDateTime).toLocaleString() : '—'}</span>
                      <button className="btn-delete-note" onClick={() => deleteNote(selectedLead.id, note.id)}>🗑️</button>
                    </div>
                    {note.nextConversation && (
                      <div className="note-next">⏭️ Next: {new Date(note.nextConversation).toLocaleString()}</div>
                    )}
                    {note.transcript && <p className="note-transcript">{note.transcript}</p>}
                    {note.audioUrl && <audio controls src={note.audioUrl} className="voice-playback" />}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
