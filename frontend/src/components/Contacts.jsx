import React, { useState, useEffect, useRef } from 'react';
import '../styles/Contacts.css';

export default function Contacts() {
  // Mock data
  const mockContactsData = [
    { id: 1, name: 'Neha Singh', company: 'Tech Startup', email: 'neha@techstartup.com', phone: '+91-9876543210', score: 85, city: 'Mumbai, Andheri West' },
    { id: 2, name: 'Vikram Reddy', company: 'Tech Park', email: 'vikram@techpark.com', phone: '+91-9876543211', score: 72, city: 'Bangalore, Whitefield' },
    { id: 3, name: 'Anjali Desai', company: 'Retail Chain', email: 'anjali@retail.com', phone: '+91-9876543212', score: 65, city: 'Pune, Kothrud' },
    { id: 4, name: 'Amit Patel', company: 'Manufacturing', email: 'amit@mfg.com', phone: '+91-9876543213', score: 58, city: 'Ahmedabad, Naroda' },
    { id: 5, name: 'Priya Kapoor', company: 'Digital Ventures', email: 'priya@digital.com', phone: '+91-9876543214', score: 80, city: 'Delhi, Connaught Place' }
  ];

  const [contacts, setContacts] = useState(mockContactsData);
  const [showForm, setShowForm] = useState(false);
  const [showCommunication, setShowCommunication] = useState(false);
  const [showDigi, setShowDigi] = useState(false);
  const [showNotes, setShowNotes] = useState(false);
  const [communicationTab, setCommunicationTab] = useState('message');
  const [selectedContact, setSelectedContact] = useState(null);
  const [message, setMessage] = useState('');
  const [emailSubject, setEmailSubject] = useState('');
  const [emailBody, setEmailBody] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  // Notes & voice-note state
  const [contactNotes, setContactNotes] = useState({});
  const [noteDraft, setNoteDraft] = useState({ callDateTime: '', nextConversation: '', transcript: '' });
  const [isRecording, setIsRecording] = useState(false);
  const [draftAudioUrl, setDraftAudioUrl] = useState(null);
  const [speechSupported] = useState(() => !!(window.SpeechRecognition || window.webkitSpeechRecognition));
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recognitionRef = useRef(null);

  useEffect(() => {
    fetchContacts();
  }, []);

  const fetchContacts = async () => {
    try {
      const response = await fetch('/api/contacts');
      if (!response.ok) throw new Error('API error');
      const data = await response.json();
      if (Array.isArray(data) && data.length > 0) {
        setContacts(data);
      } else {
        setContacts(mockContactsData);
      }
    } catch (error) {
      console.error('Error fetching contacts:', error);
      setContacts(mockContactsData);
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

  const handleNotes = (contact) => {
    setSelectedContact(contact);
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
    if (!selectedContact) return;
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
    setContactNotes((prev) => ({
      ...prev,
      [selectedContact.id]: [entry, ...(prev[selectedContact.id] || [])]
    }));
    setNoteDraft({
      callDateTime: new Date().toISOString().slice(0, 16),
      nextConversation: '',
      transcript: ''
    });
    setDraftAudioUrl(null);
  };

  const deleteNote = (contactId, noteId) => {
    setContactNotes((prev) => ({
      ...prev,
      [contactId]: (prev[contactId] || []).filter((n) => n.id !== noteId)
    }));
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

  // Always show mock data - use mock data if no contacts are loaded
  const displayContacts = (contacts && contacts.length > 0) ? contacts : mockContactsData;

  const filteredContacts = (displayContacts && displayContacts.length > 0) ?
    displayContacts.filter(c =>
      c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.email.toLowerCase().includes(searchTerm.toLowerCase())
    ) : mockContactsData;

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
              <p><strong>City/Area:</strong> 📍 {contact.city}</p>
            </div>

            <div className="action-buttons">
              <button className="btn-action call" onClick={() => handleCall(contact)} title="Click to Call">☎️</button>
              <button className="btn-action message" onClick={() => handleMessage(contact)} title="Direct Message">💬</button>
              <button className="btn-action email" onClick={() => handleEmail(contact)} title="Send Email">📧</button>
              <button className="btn-action whatsapp" onClick={() => handleWhatsApp(contact)} title="WhatsApp">📱</button>
              <button className="btn-action digilocker" onClick={() => handleDigi(contact)} title="DigiLocker">🔐</button>
              <button className="btn-action notes" onClick={() => handleNotes(contact)} title="Notes & Follow-up">📝</button>
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

      {/* Notes & Follow-up Modal */}
      {showNotes && selectedContact && (
        <div className="modal-overlay" onClick={closeNotes}>
          <div className="modal-content notes-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>📝 Notes & Follow-up - {selectedContact.name}</h2>
              <button className="btn-close" onClick={closeNotes}>×</button>
            </div>

            <div className="modal-body">
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
                <h4>History ({(contactNotes[selectedContact.id] || []).length})</h4>
                {(contactNotes[selectedContact.id] || []).length === 0 ? (
                  <p className="no-notes">No notes yet for this contact.</p>
                ) : (
                  (contactNotes[selectedContact.id] || []).map((note) => (
                    <div key={note.id} className="note-entry">
                      <div className="note-entry-header">
                        <span>📞 {note.callDateTime ? new Date(note.callDateTime).toLocaleString() : '—'}</span>
                        <button className="btn-delete-note" onClick={() => deleteNote(selectedContact.id, note.id)}>🗑️</button>
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
        </div>
      )}
    </div>
  );
}
