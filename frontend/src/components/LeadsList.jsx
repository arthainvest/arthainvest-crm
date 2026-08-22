import React, { useState, useEffect, useRef } from 'react';
import { getLeads, createLead, updateLead } from '../services/api';
import '../styles/LeadsList.css';

const STATUS_OPTIONS = ['New', 'Contacted', 'Interested', 'Document Pending', 'In Process', 'Qualified', 'Not Interested', 'CIBIL Issue', 'Lost to Competition'];

const statusClass = (status) => (status || '').toLowerCase().replace(/\s+/g, '-');

const WhatsAppIcon = () => (
  <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true">
    <path d="M12.04 2c-5.46 0-9.91 4.45-9.91 9.91 0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21h.004c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.816 9.816 0 0012.05 2zm5.71 14.14c-.24.68-1.4 1.31-1.94 1.36-.5.05-1.13.07-1.82-.11-.42-.11-.96-.31-1.65-.61-2.9-1.25-4.79-4.17-4.94-4.36-.15-.19-1.18-1.57-1.18-3 0-1.43.75-2.13 1.02-2.42.27-.29.59-.36.78-.36l.56.01c.18 0 .42-.07.66.5.24.58.83 2 .9 2.15.07.15.12.32.02.51-.09.19-.14.31-.28.48-.14.17-.29.37-.42.5-.14.14-.28.29-.12.56.16.28.71 1.17 1.52 1.89 1.05.93 1.93 1.22 2.21 1.36.28.14.44.12.6-.07.16-.19.68-.79.86-1.06.18-.28.36-.23.6-.14.24.09 1.53.72 1.79.85.26.13.44.19.5.3.06.11.06.63-.18 1.31z" />
  </svg>
);

export default function LeadsList() {
  const mockLeads = [
    { id: 1, name: 'Neha Singh', company: 'Startup Fund', email: 'neha@startup.com', phone: '+91-9876543210', status: 'New', ai_score: 85 },
    { id: 2, name: 'Vikram Reddy', company: 'Tech Park', email: 'vikram@techpark.com', phone: '+91-9876543211', status: 'Interested', ai_score: 72 },
    { id: 3, name: 'Anjali Desai', company: 'Retail Chain', email: 'anjali@retail.com', phone: '+91-9876543212', status: 'Not Interested', ai_score: 65 },
    { id: 4, name: 'Amit Patel', company: 'Manufacturing', email: 'amit@mfg.com', phone: '+91-9876543213', status: 'CIBIL Issue', ai_score: 58 },
    { id: 5, name: 'Priya Kapoor', company: 'Digital Ventures', email: 'priya@digital.com', phone: '+91-9876543214', status: 'Lost to Competition', ai_score: 80 }
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

  // Expand/collapse per-lead details
  const [expandedLeads, setExpandedLeads] = useState({});

  // Email modal state
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [selectedLead, setSelectedLead] = useState(null);
  const [emailSubject, setEmailSubject] = useState('');
  const [emailBody, setEmailBody] = useState('');

  // Notes & voice-note state
  const [showNotes, setShowNotes] = useState(false);
  const [leadNotes, setLeadNotes] = useState({});
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

  const handleStatusChange = (leadId, newStatus) => {
    setLeads((prev) => prev.map((l) => (l.id === leadId ? { ...l, status: newStatus } : l)));
  };

  const toggleExpand = (leadId) => {
    setExpandedLeads((prev) => ({ ...prev, [leadId]: !prev[leadId] }));
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
            name: obj.name || 'Unnamed Lead',
            company: obj.company || '',
            email: obj.email || '',
            phone: obj.phone || '',
            status: STATUS_OPTIONS.includes(obj.status) ? obj.status : 'New',
            ai_score: obj.score || obj.ai_score || ''
          };
        });
        setLeads((prev) => [...prev, ...imported]);
        alert(`Imported ${imported.length} lead(s) successfully.`);
      } catch (err) {
        alert('Failed to parse CSV file: ' + err.message);
      } finally {
        e.target.value = '';
      }
    };
    reader.readAsText(file);
  };

  const handleExportCSV = () => {
    const headers = ['Name', 'Company', 'Email', 'Phone', 'Status', 'Score'];
    const rows = displayLeads.map((l) => [l.name, l.company || '', l.email || '', l.phone || '', l.status || '', l.ai_score ?? '']);
    const csvContent = [headers, ...rows]
      .map((row) => row.map((field) => `"${String(field).replace(/"/g, '""')}"`).join(','))
      .join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `leads-export-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
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

  const handleEmail = (lead) => {
    setSelectedLead(lead);
    setShowEmailModal(true);
  };

  const sendEmail = () => {
    if (emailSubject.trim() && emailBody.trim()) {
      window.location.href = `mailto:${selectedLead.email}?subject=${encodeURIComponent(emailSubject)}&body=${encodeURIComponent(emailBody)}`;
      setEmailSubject('');
      setEmailBody('');
      setShowEmailModal(false);
    }
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

  const handleNotes = (lead) => {
    setSelectedLead(lead);
    resetNoteDraft();
    setIsRecording(false);
    setShowNotes(true);
  };

  const closeNotes = () => {
    if (isRecording) stopRecording();
    setShowNotes(false);
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
    if (!selectedLead) return;
    if (!noteDraft.transcript.trim() && !draftAudioUrl) {
      alert('Add a transcript note or record a voice note before saving.');
      return;
    }

    if (editingNoteId) {
      setLeadNotes((prev) => ({
        ...prev,
        [selectedLead.id]: (prev[selectedLead.id] || []).map((n) =>
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
      setLeadNotes((prev) => ({
        ...prev,
        [selectedLead.id]: [entry, ...(prev[selectedLead.id] || [])]
      }));
    }

    resetNoteDraft();
  };

  const deleteNote = (leadId, noteId) => {
    setLeadNotes((prev) => ({
      ...prev,
      [leadId]: (prev[leadId] || []).filter((n) => n.id !== noteId)
    }));
    if (editingNoteId === noteId) resetNoteDraft();
  };

  const displayLeads = (leads && leads.length > 0) ? leads : mockLeads;

  return (
    <div className="leads-container">
      <div className="leads-header">
        <h1>Leads</h1>
        <div className="leads-header-actions">
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
          <button
            className="btn-primary"
            onClick={() => setShowModal(true)}
          >
            + New Lead
          </button>
        </div>
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
        <div className="leads-list">
          {displayLeads.map((lead) => {
            const isExpanded = !!expandedLeads[lead.id];
            return (
              <div key={lead.id} className="lead-row">
                <div className="lead-row-main">
                  <button
                    type="button"
                    className="lead-name-toggle"
                    onClick={() => toggleExpand(lead.id)}
                    title={isExpanded ? 'Hide details' : 'Show details'}
                  >
                    <span className={`expand-arrow ${isExpanded ? 'open' : ''}`}>▸</span>
                    <span className="lead-name">{lead.name}</span>
                  </button>

                  <select
                    className={`status-select-compact status-${statusClass(lead.status)}`}
                    value={lead.status}
                    onChange={(e) => handleStatusChange(lead.id, e.target.value)}
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>

                  <div className="lead-row-actions">
                    <button className="btn-action call" onClick={() => handleCall(lead)} title="Click to Call">☎️</button>
                    <button className="btn-action whatsapp" onClick={() => handleWhatsApp(lead)} title="WhatsApp">
                      <WhatsAppIcon />
                    </button>
                    <button className="btn-action email" onClick={() => handleEmail(lead)} title="Send Email">📧</button>
                    <button className="btn-action notes" onClick={() => handleNotes(lead)} title="Notes & Follow-up">📝</button>
                  </div>
                </div>

                {isExpanded && (
                  <div className="lead-row-details">
                    <p><strong>Company:</strong> {lead.company || '-'}</p>
                    <p><strong>Email:</strong> {lead.email || '-'}</p>
                    <p><strong>Phone:</strong> {lead.phone || '-'}</p>
                    <p><strong>Score:</strong> {lead.ai_score || '-'}%</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <p className="no-data">No leads yet. Create your first lead!</p>
      )}

      {/* Email Modal */}
      {showEmailModal && selectedLead && (
        <div className="modal-overlay" onClick={() => setShowEmailModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Send Email to {selectedLead.name}</h2>
              <button className="modal-close" onClick={() => setShowEmailModal(false)}>✕</button>
            </div>

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
              <button className="btn-secondary" onClick={() => setShowEmailModal(false)}>Cancel</button>
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
                <button className="btn-primary" onClick={saveNote}>
                  {editingNoteId ? '💾 Update Note' : '💾 Save Note'}
                </button>
                {editingNoteId && (
                  <button className="btn-secondary" onClick={cancelEditNote}>Cancel Edit</button>
                )}
              </div>
            </div>

            <div className="notes-history">
              <h4>History ({(leadNotes[selectedLead.id] || []).length})</h4>
              {(leadNotes[selectedLead.id] || []).length === 0 ? (
                <p className="no-notes">No notes yet for this lead.</p>
              ) : (
                (leadNotes[selectedLead.id] || []).map((note) => (
                  <div key={note.id} className={`note-entry ${editingNoteId === note.id ? 'editing' : ''}`}>
                    <div className="note-entry-header">
                      <span>📞 {note.callDateTime ? new Date(note.callDateTime).toLocaleString() : '—'}</span>
                      <div className="note-entry-actions">
                        <button className="btn-edit-note" onClick={() => handleEditNote(note)} title="Edit">✏️</button>
                        <button className="btn-delete-note" onClick={() => deleteNote(selectedLead.id, note.id)} title="Delete">🗑️</button>
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
      )}
    </div>
  );
}
