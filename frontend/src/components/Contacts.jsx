import React, { useState, useEffect, useRef } from 'react';
import '../styles/Contacts.css';

const WhatsAppIcon = () => (
  <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true">
    <path d="M12.04 2c-5.46 0-9.91 4.45-9.91 9.91 0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21h.004c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.816 9.816 0 0012.05 2zm5.71 14.14c-.24.68-1.4 1.31-1.94 1.36-.5.05-1.13.07-1.82-.11-.42-.11-.96-.31-1.65-.61-2.9-1.25-4.79-4.17-4.94-4.36-.15-.19-1.18-1.57-1.18-3 0-1.43.75-2.13 1.02-2.42.27-.29.59-.36.78-.36l.56.01c.18 0 .42-.07.66.5.24.58.83 2 .9 2.15.07.15.12.32.02.51-.09.19-.14.31-.28.48-.14.17-.29.37-.42.5-.14.14-.28.29-.12.56.16.28.71 1.17 1.52 1.89 1.05.93 1.93 1.22 2.21 1.36.28.14.44.12.6-.07.16-.19.68-.79.86-1.06.18-.28.36-.23.6-.14.24.09 1.53.72 1.79.85.26.13.44.19.5.3.06.11.06.63-.18 1.31z" />
  </svg>
);

const emptyContactForm = { name: '', company: '', email: '', phone: '', city: '' };

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
  const [searchTerm, setSearchTerm] = useState('');

  // Expand/collapse per-contact details
  const [expandedContacts, setExpandedContacts] = useState({});

  // Add/Edit Contact modal
  const [showForm, setShowForm] = useState(false);
  const [editingContactId, setEditingContactId] = useState(null);
  const [contactForm, setContactForm] = useState(emptyContactForm);

  // Email modal
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [selectedContact, setSelectedContact] = useState(null);
  const [emailSubject, setEmailSubject] = useState('');
  const [emailBody, setEmailBody] = useState('');

  // DigiLocker modal
  const [showDigi, setShowDigi] = useState(false);

  // Notes & voice-note state
  const [showNotes, setShowNotes] = useState(false);
  const [contactNotes, setContactNotes] = useState({});
  const [noteDraft, setNoteDraft] = useState({ callDateTime: '', nextConversation: '', transcript: '' });
  const [editingNoteId, setEditingNoteId] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [draftAudioUrl, setDraftAudioUrl] = useState(null);
  const [speechSupported] = useState(() => !!(window.SpeechRecognition || window.webkitSpeechRecognition));
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recognitionRef = useRef(null);

  // Role-based Import/Export
  const userRole = (localStorage.getItem('role') || 'employee').toLowerCase();
  const canExport = userRole === 'admin';
  const importInputRef = useRef(null);

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

  const toggleExpand = (contactId) => {
    setExpandedContacts((prev) => ({ ...prev, [contactId]: !prev[contactId] }));
  };

  const handleImportClick = () => {
    importInputRef.current?.click();
  };

  const handleImportFile = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const text = event.target.result;
        const rows = text.split(/\r?\n/).filter((r) => r.trim().length > 0);
        if (rows.length < 2) {
          alert('CSV file appears to be empty or missing data rows.');
          return;
        }
        const headers = rows[0].split(',').map((h) => h.trim().toLowerCase().replace(/"/g, ''));
        const imported = rows.slice(1).map((row, idx) => {
          const cols = row.split(',').map((c) => c.trim().replace(/^"|"$/g, ''));
          const obj = {};
          headers.forEach((h, i) => { obj[h] = cols[i] || ''; });
          return {
            id: Date.now() + idx,
            name: obj.name || 'Unnamed Contact',
            company: obj.company || '',
            email: obj.email || '',
            phone: obj.phone || '',
            city: obj.city || obj['city/area'] || '',
            score: obj.score || ''
          };
        });
        setContacts((prev) => [...prev, ...imported]);
        alert(`Imported ${imported.length} contact(s) successfully.`);
      } catch (err) {
        alert('Failed to parse CSV file: ' + err.message);
      } finally {
        e.target.value = '';
      }
    };
    reader.readAsText(file);
  };

  const handleExportCSV = () => {
    const headers = ['Name', 'Company', 'Email', 'Phone', 'City/Area', 'Score'];
    const rows = displayContacts.map((c) => [c.name, c.company || '', c.email || '', c.phone || '', c.city || '', c.score ?? '']);
    const csvContent = [headers, ...rows]
      .map((row) => row.map((field) => `"${String(field).replace(/"/g, '""')}"`).join(','))
      .join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `contacts-export-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
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

  const handleEmail = (contact) => {
    setSelectedContact(contact);
    setShowEmailModal(true);
  };

  const sendEmail = () => {
    if (emailSubject.trim() && emailBody.trim()) {
      window.location.href = `mailto:${selectedContact.email}?subject=${encodeURIComponent(emailSubject)}&body=${encodeURIComponent(emailBody)}`;
      setEmailSubject('');
      setEmailBody('');
      setShowEmailModal(false);
    }
  };

  const handleDigi = (contact) => {
    setSelectedContact(contact);
    setShowDigi(true);
  };

  const handleAddContactClick = () => {
    setEditingContactId(null);
    setContactForm(emptyContactForm);
    setShowForm(true);
  };

  const handleEditContact = (contact) => {
    setEditingContactId(contact.id);
    setContactForm({
      name: contact.name || '',
      company: contact.company || '',
      email: contact.email || '',
      phone: contact.phone || '',
      city: contact.city || ''
    });
    setShowForm(true);
  };

  const handleDeleteContact = (contactId) => {
    if (window.confirm('Are you sure you want to delete this contact?')) {
      setContacts((prev) => prev.filter((c) => c.id !== contactId));
    }
  };

  const handleSaveContact = (e) => {
    e.preventDefault();
    if (!contactForm.name.trim()) return;

    if (editingContactId) {
      setContacts((prev) => prev.map((c) => (
        c.id === editingContactId ? { ...c, ...contactForm } : c
      )));
    } else {
      setContacts((prev) => [
        ...prev,
        { id: Date.now(), score: '', ...contactForm }
      ]);
    }
    setShowForm(false);
    setContactForm(emptyContactForm);
    setEditingContactId(null);
  };

  const handleNotes = (contact) => {
    setSelectedContact(contact);
    resetNoteDraft();
    setIsRecording(false);
    setShowNotes(true);
  };

  const closeNotes = () => {
    if (isRecording) stopRecording();
    setShowNotes(false);
  };

  const resetNoteDraft = () => {
    setNoteDraft({
      callDateTime: new Date().toISOString().slice(0, 16),
      nextConversation: '',
      transcript: ''
    });
    setDraftAudioUrl(null);
    setEditingNoteId(null);
  };

  const handleEditNote = (note) => {
    setNoteDraft({
      callDateTime: note.callDateTime || '',
      nextConversation: note.nextConversation || '',
      transcript: note.transcript || ''
    });
    setDraftAudioUrl(note.audioUrl || null);
    setEditingNoteId(note.id);
  };

  const cancelEditNote = () => {
    resetNoteDraft();
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

    if (editingNoteId) {
      setContactNotes((prev) => ({
        ...prev,
        [selectedContact.id]: (prev[selectedContact.id] || []).map((n) =>
          n.id === editingNoteId
            ? {
                ...n,
                callDateTime: noteDraft.callDateTime,
                nextConversation: noteDraft.nextConversation,
                transcript: noteDraft.transcript.trim(),
                audioUrl: draftAudioUrl,
                updatedAt: new Date().toLocaleString()
              }
            : n
        )
      }));
    } else {
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
    }

    resetNoteDraft();
  };

  const deleteNote = (contactId, noteId) => {
    setContactNotes((prev) => ({
      ...prev,
      [contactId]: (prev[contactId] || []).filter((n) => n.id !== noteId)
    }));
    if (editingNoteId === noteId) resetNoteDraft();
  };

  // Always show mock data - use mock data if no contacts are loaded
  const displayContacts = (contacts && contacts.length > 0) ? contacts : mockContactsData;

  const filteredContacts = (displayContacts && displayContacts.length > 0) ?
    displayContacts.filter(c =>
      (c.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (c.email || '').toLowerCase().includes(searchTerm.toLowerCase())
    ) : mockContactsData;

  return (
    <div className="contacts-container">
      <div className="contacts-header">
        <h1>Contacts</h1>
        <div className="contacts-header-actions">
          <input
            type="file"
            accept=".csv"
            ref={importInputRef}
            onChange={handleImportFile}
            style={{ display: 'none' }}
          />
          <button className="btn-secondary" onClick={handleImportClick}>📥 Import</button>
          {canExport && (
            <button className="btn-secondary" onClick={handleExportCSV}>📤 Export</button>
          )}
          <button className="btn-primary" onClick={handleAddContactClick}>+ Add Contact</button>
        </div>
      </div>

      <div className="search-bar">
        <input
          type="text"
          placeholder="Search contacts by name or email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="contacts-list">
        {filteredContacts.map((contact) => {
          const isExpanded = !!expandedContacts[contact.id];
          return (
            <div key={contact.id} className="contact-row">
              <div className="contact-row-main">
                <button
                  type="button"
                  className="contact-name-toggle"
                  onClick={() => toggleExpand(contact.id)}
                  title={isExpanded ? 'Hide details' : 'Show details'}
                >
                  <span className={`expand-arrow ${isExpanded ? 'open' : ''}`}>▸</span>
                  <span className="contact-name">{contact.name}</span>
                </button>

                {contact.score !== '' && contact.score != null && (
                  <span className="score-badge-inline">{contact.score}%</span>
                )}

                <div className="contact-row-actions">
                  <button className="btn-action call" onClick={() => handleCall(contact)} title="Click to Call">☎️</button>
                  <button className="btn-action email" onClick={() => handleEmail(contact)} title="Send Email">📧</button>
                  <button className="btn-action whatsapp" onClick={() => handleWhatsApp(contact)} title="WhatsApp">
                    <WhatsAppIcon />
                  </button>
                  <button className="btn-action digilocker" onClick={() => handleDigi(contact)} title="DigiLocker">🔐</button>
                  <button className="btn-action notes" onClick={() => handleNotes(contact)} title="Notes & Follow-up">📝</button>
                </div>

                <div className="contact-row-corner">
                  <button className="btn-corner edit" onClick={() => handleEditContact(contact)} title="Edit">✏️</button>
                  <button className="btn-corner delete" onClick={() => handleDeleteContact(contact.id)} title="Delete">🗑️</button>
                </div>
              </div>

              {isExpanded && (
                <div className="contact-row-details">
                  <p><strong>Company:</strong> {contact.company || '-'}</p>
                  <p><strong>Email:</strong> {contact.email || '-'}</p>
                  <p><strong>Phone:</strong> {contact.phone || '-'}</p>
                  <p><strong>City/Area:</strong> 📍 {contact.city || '-'}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Add/Edit Contact Modal */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingContactId ? 'Edit Contact' : 'Add New Contact'}</h2>
              <button className="btn-close" onClick={() => setShowForm(false)}>×</button>
            </div>

            <form onSubmit={handleSaveContact}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Name *</label>
                  <input
                    type="text"
                    required
                    value={contactForm.name}
                    onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Company</label>
                  <input
                    type="text"
                    value={contactForm.company}
                    onChange={(e) => setContactForm({ ...contactForm, company: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Email</label>
                  <input
                    type="email"
                    value={contactForm.email}
                    onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Phone</label>
                  <input
                    type="tel"
                    value={contactForm.phone}
                    onChange={(e) => setContactForm({ ...contactForm, phone: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>City/Area</label>
                  <input
                    type="text"
                    value={contactForm.city}
                    onChange={(e) => setContactForm({ ...contactForm, city: e.target.value })}
                  />
                </div>
              </div>
              <div className="modal-actions">
                <button type="submit" className="btn-primary">
                  {editingContactId ? 'Save Changes' : 'Add Contact'}
                </button>
                <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Email Modal */}
      {showEmailModal && selectedContact && (
        <div className="modal-overlay" onClick={() => setShowEmailModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Send Email to {selectedContact.name}</h2>
              <button className="btn-close" onClick={() => setShowEmailModal(false)}>×</button>
            </div>

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
                <button className="btn-secondary" onClick={() => setShowEmailModal(false)}>Cancel</button>
              </div>
            </div>
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
                  <button className="btn-primary" onClick={saveNote}>
                    {editingNoteId ? '💾 Update Note' : '💾 Save Note'}
                  </button>
                  {editingNoteId && (
                    <button className="btn-secondary" onClick={cancelEditNote}>Cancel Edit</button>
                  )}
                </div>
              </div>

              <div className="notes-history">
                <h4>History ({(contactNotes[selectedContact.id] || []).length})</h4>
                {(contactNotes[selectedContact.id] || []).length === 0 ? (
                  <p className="no-notes">No notes yet for this contact.</p>
                ) : (
                  (contactNotes[selectedContact.id] || []).map((note) => (
                    <div key={note.id} className={`note-entry ${editingNoteId === note.id ? 'editing' : ''}`}>
                      <div className="note-entry-header">
                        <span>📞 {note.callDateTime ? new Date(note.callDateTime).toLocaleString() : '—'}</span>
                        <div className="note-entry-actions">
                          <button className="btn-edit-note" onClick={() => handleEditNote(note)} title="Edit">✏️</button>
                          <button className="btn-delete-note" onClick={() => deleteNote(selectedContact.id, note.id)} title="Delete">🗑️</button>
                        </div>
                      </div>
                      {note.nextConversation && (
                        <div className="note-next">⏭️ Next: {new Date(note.nextConversation).toLocaleString()}</div>
                      )}
                      {note.transcript && <p className="note-transcript">{note.transcript}</p>}
                      {note.audioUrl && <audio controls src={note.audioUrl} className="voice-playback" />}
                      {note.updatedAt && <div className="note-updated">Edited {note.updatedAt}</div>}
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
