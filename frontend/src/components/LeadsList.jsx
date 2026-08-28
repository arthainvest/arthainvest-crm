import React, { useState, useEffect, useRef } from 'react';
import {
  getLeads, createLead, updateLead, assignLead, getTeam,
  getLeadNotes, createLeadNote, updateLeadNote, deleteLeadNote,
  uploadLeadNoteAudio, API_URL, dialCall, aiSuggestLeadFollowup,
  sendWhatsApp, sendEmailReal, sendSms, detectFollowupDate, assignToDialer, getActivities, getDeals, convertLeadToContact
} from '../services/api';
import { LOAN_PRODUCTS } from '../constants/loanProducts';
import EntityTags from './EntityTags';
import EntityGroups from './EntityGroups';
import EntityCustomFields from './EntityCustomFields';
import '../styles/LeadsList.css';

const STATUS_OPTIONS = ['New', 'Contacted', 'Interested', 'Document Pending', 'In Process', 'Qualified', 'Not Interested', 'CIBIL Issue', 'Lost to Competition'];

const ACTIVITY_ICONS = { Call: '📞', Email: '✉️', WhatsApp: '💬', SMS: '📱', Task: '✅', Meeting: '📅', Campaign: '📢' };

const statusClass = (status) => (status || '').toLowerCase().replace(/\s+/g, '-');
const dealLabel = (deal) => {
  const productInfo = LOAN_PRODUCTS.find((p) => p.id === deal.loan_product);
  return `${productInfo?.name || deal.loan_product} · ₹${(deal.deal_value || 0).toLocaleString('en-IN')} · ${deal.process_status || 'Login'}`;
};

// A naive line.split(',') breaks on quoted fields containing commas (e.g. "Doe, John") or
// escaped quotes ("Say ""hi"""). This walks the line char-by-char tracking quote state instead.
const parseCSVLine = (line) => {
  const result = [];
  let current = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (inQuotes) {
      if (char === '"') {
        if (line[i + 1] === '"') {
          current += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        current += char;
      }
    } else if (char === '"') {
      inQuotes = true;
    } else if (char === ',') {
      result.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  result.push(current.trim());
  return result;
};

// Older leads may have a free-text product value from before this was a dropdown -
// fall back to showing it as-is rather than hiding data that's already there.
const productLabel = (id) => {
  const product = LOAN_PRODUCTS.find((p) => p.id === id);
  return product ? `${product.icon} ${product.name}` : id;
};

const WhatsAppIcon = () => (
  <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true">
    <path d="M12.04 2c-5.46 0-9.91 4.45-9.91 9.91 0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21h.004c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.816 9.816 0 0012.05 2zm5.71 14.14c-.24.68-1.4 1.31-1.94 1.36-.5.05-1.13.07-1.82-.11-.42-.11-.96-.31-1.65-.61-2.9-1.25-4.79-4.17-4.94-4.36-.15-.19-1.18-1.57-1.18-3 0-1.43.75-2.13 1.02-2.42.27-.29.59-.36.78-.36l.56.01c.18 0 .42-.07.66.5.24.58.83 2 .9 2.15.07.15.12.32.02.51-.09.19-.14.31-.28.48-.14.17-.29.37-.42.5-.14.14-.28.29-.12.56.16.28.71 1.17 1.52 1.89 1.05.93 1.93 1.22 2.21 1.36.28.14.44.12.6-.07.16-.19.68-.79.86-1.06.18-.28.36-.23.6-.14.24.09 1.53.72 1.79.85.26.13.44.19.5.3.06.11.06.63-.18 1.31z" />
  </svg>
);

export default function LeadsList() {
  const [leads, setLeads] = useState([]);
  const [teamMembers, setTeamMembers] = useState([]);
  const [showModal, setShowModal] = useState(false);
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
  const [notes, setNotes] = useState([]);
  const [activities, setActivities] = useState([]);
  const [loadingActivities, setLoadingActivities] = useState(false);
  const [leadDeals, setLeadDeals] = useState([]);
  const [loadingLeadDeals, setLoadingLeadDeals] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [dateDetectMessage, setDateDetectMessage] = useState(null);
  const [dateDetecting, setDateDetecting] = useState(false);
  const [noteDraft, setNoteDraft] = useState({ callDateTime: '', nextConversation: '', transcript: '' });
  const [editingNoteId, setEditingNoteId] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [draftAudioUrl, setDraftAudioUrl] = useState(null);
  const [speechSupported] = useState(() => !!(window.SpeechRecognition || window.webkitSpeechRecognition));
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recognitionRef = useRef(null);
  const draftAudioBlobRef = useRef(null);

  // Role-based Import/Export
  const userRole = (localStorage.getItem('role') || 'employee').toLowerCase();
  const canExport = userRole === 'admin';
  const importInputRef = useRef(null);

  // Bulk selection -> "Assign to Dialer" (Kylas My Call Dialer parity)
  const [selectedLeadIds, setSelectedLeadIds] = useState([]);
  const [showDialerModal, setShowDialerModal] = useState(false);
  const [dialerTeamMemberId, setDialerTeamMemberId] = useState('');
  const [assigningToDialer, setAssigningToDialer] = useState(false);

  useEffect(() => {
    fetchLeads();
    fetchTeamMembers();
  }, []);

  const fetchLeads = async () => {
    try {
      const data = await getLeads(token);
      setLeads(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to fetch leads:', err);
    }
  };

  const fetchTeamMembers = async () => {
    try {
      const data = await getTeam(token);
      setTeamMembers(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to fetch team members:', err);
    }
  };

  const handleAssignChange = async (leadId, teamMemberIdRaw) => {
    const teamMemberId = teamMemberIdRaw ? Number(teamMemberIdRaw) : null;
    const previous = leads.find((l) => l.id === leadId);
    setLeads((prev) => prev.map((l) => (l.id === leadId
      ? { ...l, assigned_team_member_id: teamMemberId, assigned_team_member_name: teamMembers.find((m) => m.id === teamMemberId)?.name || null }
      : l)));
    try {
      await assignLead(token, leadId, teamMemberId);
    } catch (err) {
      console.error('Failed to assign lead:', err);
      if (previous) {
        setLeads((prev) => prev.map((l) => (l.id === leadId ? previous : l)));
      }
      alert('Failed to assign lead. Please try again.');
    }
  };

  const handleConvertToContact = async (lead) => {
    if (!window.confirm(`Convert ${lead.name} to a Contact? Their calls, emails, tasks, meetings and campaign history will carry over to the new Contact record.`)) return;
    try {
      const newContact = await convertLeadToContact(token, lead.id);
      setLeads((prev) => prev.map((l) => (l.id === lead.id
        ? { ...l, converted_contact_id: newContact.id, converted_contact_name: newContact.name }
        : l)));
    } catch (err) {
      console.error('Failed to convert lead to contact:', err);
      alert(err.response?.data?.detail || 'Failed to convert lead to contact. Please try again.');
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

  const handleStatusChange = async (leadId, newStatus) => {
    const previous = leads.find((l) => l.id === leadId);
    // Optimistic update, reverted below if the request fails
    setLeads((prev) => prev.map((l) => (l.id === leadId ? { ...l, status: newStatus } : l)));
    try {
      await updateLead(token, leadId, { status: newStatus });
    } catch (err) {
      console.error('Failed to update lead status:', err);
      if (previous) {
        setLeads((prev) => prev.map((l) => (l.id === leadId ? previous : l)));
      }
      alert('Failed to update status. Please try again.');
    }
  };

  const toggleExpand = (leadId) => {
    setExpandedLeads((prev) => ({ ...prev, [leadId]: !prev[leadId] }));
  };

  const toggleLeadSelected = (leadId) => {
    setSelectedLeadIds((prev) => (prev.includes(leadId) ? prev.filter((id) => id !== leadId) : [...prev, leadId]));
  };

  const handleAssignToDialer = async () => {
    if (!dialerTeamMemberId || selectedLeadIds.length === 0) return;
    setAssigningToDialer(true);
    try {
      const result = await assignToDialer(token, { teamMemberId: Number(dialerTeamMemberId), leadIds: selectedLeadIds });
      alert(`Added ${result.assigned} lead(s) to the dial queue.${result.skipped ? ` ${result.skipped} were already queued for that team member.` : ''}`);
      setSelectedLeadIds([]);
      setShowDialerModal(false);
      setDialerTeamMemberId('');
    } catch (err) {
      console.error('Failed to assign to dialer:', err);
      alert('Failed to assign to dialer. Please try again.');
    } finally {
      setAssigningToDialer(false);
    }
  };

  const handleImportClick = () => {
    importInputRef.current?.click();
  };

  const handleImportFile = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async (event) => {
      try {
        const text = event.target.result;
        const rows = text.split(/\r?\n/).filter((r) => r.trim().length > 0);
        if (rows.length < 2) {
          alert('CSV file appears to be empty or missing data rows.');
          return;
        }
        const headers = parseCSVLine(rows[0]).map((h) => h.toLowerCase());
        const imported = rows.slice(1).map((row) => {
          const cols = parseCSVLine(row);
          const obj = {};
          headers.forEach((h, i) => { obj[h] = cols[i] || ''; });
          const assignedName = (obj.employee || obj['assigned to'] || obj['assigned employee'] || '').trim();
          return {
            name: obj.name || 'Unnamed Lead',
            company: obj.company || '',
            email: obj.email || '',
            phone: obj.phone || '',
            product: obj.product || '',
            source: obj.source || '',
            assignedName
          };
        });

        let created = 0;
        let failed = 0;
        for (const row of imported) {
          try {
            const { assignedName, ...leadData } = row;
            const newLead = await createLead(token, leadData);
            if (assignedName) {
              const match = teamMembers.find((m) => m.name.toLowerCase() === assignedName.toLowerCase());
              if (match) await assignLead(token, newLead.id, match.id);
            }
            created++;
          } catch (rowErr) {
            console.error('Error importing row:', row, rowErr);
            failed++;
          }
        }
        await fetchLeads();
        alert(failed > 0
          ? `Imported ${created} lead(s). ${failed} row(s) failed - check the console for details.`
          : `Imported ${created} lead(s) successfully.`);
      } catch (err) {
        alert('Failed to parse CSV file: ' + err.message);
      } finally {
        e.target.value = '';
      }
    };
    reader.readAsText(file);
  };

  const handleExportCSV = () => {
    const headers = ['Name', 'Company', 'Email', 'Phone', 'Status', 'Score', 'Employee'];
    const rows = leads.map((l) => [l.name, l.company || '', l.email || '', l.phone || '', l.status || '', l.ai_score ?? '', l.assigned_team_member_name || '']);
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

  const handleCall = async (lead) => {
    if (!lead.phone) {
      alert('No phone number available');
      return;
    }
    // Try a real Twilio click-to-call first (rings the agent, then bridges to the lead);
    // falls back to a plain tel: link when Twilio isn't configured on the server.
    try {
      const result = await dialCall(token, lead.phone, { leadId: lead.id });
      if (result.configured) {
        alert(result.message);
        return;
      }
    } catch (error) {
      console.error('Error placing Twilio call:', error);
    }
    window.location.href = `tel:${lead.phone}`;
  };

  const handleWhatsApp = async (lead) => {
    if (!lead.phone) {
      alert('No phone number available');
      return;
    }
    // Try a real WhatsApp Business API send first; falls back to opening a wa.me link
    // when it isn't configured on the server.
    try {
      const result = await sendWhatsApp(token, lead.phone, `Hi ${lead.name}, this is ArthaInvest reaching out.`, { leadId: lead.id });
      if (result.configured) {
        alert(result.message);
        return;
      }
    } catch (error) {
      console.error('Error sending WhatsApp message:', error);
    }
    const url = `https://wa.me/${lead.phone.replace(/\D/g, '')}`;
    window.open(url, '_blank');
  };

  const handleSms = async (lead) => {
    if (!lead.phone) {
      alert('No phone number available');
      return;
    }
    const message = window.prompt(`SMS to ${lead.name}:`, `Hi ${lead.name}, this is ArthaInvest.`);
    if (!message) return;
    try {
      const result = await sendSms(token, lead.phone, message, { leadId: lead.id });
      if (result.configured) {
        alert(result.message);
        return;
      }
    } catch (error) {
      console.error('Error sending SMS:', error);
    }
    window.location.href = `sms:${lead.phone}`;
  };

  const handleEmail = (lead) => {
    setSelectedLead(lead);
    setShowEmailModal(true);
  };

  const sendEmail = async () => {
    if (!emailSubject.trim() || !emailBody.trim()) return;
    // Try a real SMTP send first; falls back to opening a mailto: link when SMTP isn't
    // configured on the server.
    try {
      const result = await sendEmailReal(token, selectedLead.email, emailSubject, emailBody, { leadId: selectedLead.id });
      if (result.configured) {
        alert(result.message);
        setEmailSubject('');
        setEmailBody('');
        setShowEmailModal(false);
        return;
      }
    } catch (error) {
      console.error('Error sending email:', error);
    }
    window.location.href = `mailto:${selectedLead.email}?subject=${encodeURIComponent(emailSubject)}&body=${encodeURIComponent(emailBody)}`;
    setEmailSubject('');
    setEmailBody('');
    setShowEmailModal(false);
  };

  // Local recordings use blob: URLs, which the browser won't release until explicitly revoked
  // or the page unloads - revoke before dropping our only reference to one.
  const revokeIfLocalBlob = (url) => {
    if (url && url.startsWith('blob:')) URL.revokeObjectURL(url);
  };

  const resetNoteDraft = () => {
    revokeIfLocalBlob(draftAudioUrl);
    setNoteDraft({
      callDateTime: new Date().toISOString().slice(0, 16),
      nextConversation: '',
      transcript: ''
    });
    setDraftAudioUrl(null);
    draftAudioBlobRef.current = null;
    setEditingNoteId(null);
  };

  const handleNotes = async (lead) => {
    setSelectedLead(lead);
    resetNoteDraft();
    setIsRecording(false);
    setAiSuggestion(null);
    setDateDetectMessage(null);
    setShowNotes(true);
    try {
      const data = await getLeadNotes(token, lead.id);
      setNotes(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching notes:', error);
      setNotes([]);
    }
    setLoadingActivities(true);
    try {
      const activityData = await getActivities(token, null, { leadId: lead.id });
      setActivities(Array.isArray(activityData) ? activityData : []);
    } catch (error) {
      console.error('Error fetching activity timeline:', error);
      setActivities([]);
    } finally {
      setLoadingActivities(false);
    }
    setLoadingLeadDeals(true);
    try {
      const dealsData = await getDeals(token, null, { leadId: lead.id });
      setLeadDeals(Array.isArray(dealsData) ? dealsData : []);
    } catch (error) {
      console.error('Error fetching deals for lead:', error);
      setLeadDeals([]);
    } finally {
      setLoadingLeadDeals(false);
    }
  };

  const handleAiSuggest = async () => {
    if (!selectedLead) return;
    setAiLoading(true);
    setAiSuggestion(null);
    try {
      const result = await aiSuggestLeadFollowup(token, selectedLead.id);
      setAiSuggestion(result.suggestion || result.message);
    } catch (error) {
      console.error('Error getting AI suggestion:', error);
      setAiSuggestion('Failed to get a suggestion. Please try again.');
    } finally {
      setAiLoading(false);
    }
  };

  const handleDetectDate = async () => {
    if (!noteDraft.transcript.trim()) return;
    setDateDetecting(true);
    setDateDetectMessage(null);
    try {
      const result = await detectFollowupDate(token, noteDraft.transcript);
      if (result.detected_date) {
        setNoteDraft((prev) => ({ ...prev, nextConversation: result.detected_date }));
      }
      setDateDetectMessage(result.message);
    } catch (error) {
      console.error('Error detecting follow-up date:', error);
      setDateDetectMessage('Failed to check for a date. Please try again.');
    } finally {
      setDateDetecting(false);
    }
  };

  const closeNotes = () => {
    if (isRecording) stopRecording();
    setShowNotes(false);
  };

  const handleEditNote = (note) => {
    revokeIfLocalBlob(draftAudioUrl);
    setNoteDraft({
      callDateTime: note.call_datetime || '',
      nextConversation: note.next_conversation || '',
      transcript: note.transcript || ''
    });
    setDraftAudioUrl(note.audio_url ? `${API_URL}${note.audio_url}` : null);
    draftAudioBlobRef.current = null;
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
        revokeIfLocalBlob(draftAudioUrl);
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        draftAudioBlobRef.current = blob;
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

  const saveNote = async () => {
    if (!selectedLead) return;
    if (!noteDraft.transcript.trim() && !draftAudioUrl) {
      alert('Add a transcript note or record a voice note before saving.');
      return;
    }

    const payload = {
      call_datetime: noteDraft.callDateTime || null,
      next_conversation: noteDraft.nextConversation || null,
      transcript: noteDraft.transcript.trim()
    };

    try {
      const savedNote = editingNoteId
        ? await updateLeadNote(token, selectedLead.id, editingNoteId, payload)
        : await createLeadNote(token, selectedLead.id, payload);

      if (draftAudioBlobRef.current) {
        await uploadLeadNoteAudio(token, selectedLead.id, savedNote.id, draftAudioBlobRef.current);
      }

      const data = await getLeadNotes(token, selectedLead.id);
      setNotes(Array.isArray(data) ? data : []);
      resetNoteDraft();
    } catch (error) {
      console.error('Error saving note:', error);
      alert('Failed to save note. Please try again.');
    }
  };

  const deleteNote = async (leadId, noteId) => {
    try {
      await deleteLeadNote(token, leadId, noteId);
      setNotes((prev) => prev.filter((n) => n.id !== noteId));
      if (editingNoteId === noteId) resetNoteDraft();
    } catch (error) {
      console.error('Error deleting note:', error);
      alert('Failed to delete note. Please try again.');
    }
  };

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
          {selectedLeadIds.length > 0 && (
            <button className="btn-secondary" onClick={() => setShowDialerModal(true)}>
              🎯 Assign to Dialer ({selectedLeadIds.length})
            </button>
          )}
          <button
            className="btn-primary"
            onClick={() => setShowModal(true)}
          >
            + New Lead
          </button>
        </div>
      </div>

      {showDialerModal && (
        <div className="modal-overlay" onClick={() => setShowDialerModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>🎯 Assign {selectedLeadIds.length} Lead{selectedLeadIds.length === 1 ? '' : 's'} to Dialer</h2>
              <button className="modal-close" onClick={() => setShowDialerModal(false)}>✕</button>
            </div>
            <div className="form-group">
              <label>Team Member</label>
              <select value={dialerTeamMemberId} onChange={(e) => setDialerTeamMemberId(e.target.value)}>
                <option value="">-- Select who will dial these --</option>
                {teamMembers.map((m) => (
                  <option key={m.id} value={m.id}>{m.name}</option>
                ))}
              </select>
            </div>
            <div className="modal-actions">
              <button className="btn-primary" onClick={handleAssignToDialer} disabled={!dialerTeamMemberId || assigningToDialer}>
                {assigningToDialer ? 'Assigning…' : 'Add to Queue'}
              </button>
              <button className="btn-secondary" onClick={() => setShowDialerModal(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}

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
                <select
                  value={formData.product}
                  onChange={(e) =>
                    setFormData({ ...formData, product: e.target.value })
                  }
                >
                  <option value="">-- Select --</option>
                  {LOAN_PRODUCTS.map((product) => (
                    <option key={product.id} value={product.id}>
                      {product.icon} {product.name}
                    </option>
                  ))}
                </select>
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

      {leads.length > 0 ? (
        <div className="leads-list">
          {leads.map((lead) => {
            const isExpanded = !!expandedLeads[lead.id];
            return (
              <div key={lead.id} className="lead-row">
                <div className="lead-row-main">
                  <input
                    type="checkbox"
                    className="lead-select-checkbox"
                    checked={selectedLeadIds.includes(lead.id)}
                    onChange={() => toggleLeadSelected(lead.id)}
                    title="Select for bulk actions"
                  />
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

                  <select
                    className="employee-assign-select"
                    value={lead.assigned_team_member_id || ''}
                    onChange={(e) => handleAssignChange(lead.id, e.target.value)}
                    title="Assigned employee"
                  >
                    <option value="">Unassigned</option>
                    {teamMembers.map((m) => (
                      <option key={m.id} value={m.id}>{m.name}</option>
                    ))}
                  </select>

                  <div className="lead-row-actions">
                    <button className="btn-action call" onClick={() => handleCall(lead)} title="Click to Call">☎️</button>
                    <button className="btn-action sms" onClick={() => handleSms(lead)} title="Send SMS">📱</button>
                    <button className="btn-action whatsapp" onClick={() => handleWhatsApp(lead)} title="WhatsApp">
                      <WhatsAppIcon />
                    </button>
                    <button className="btn-action email" onClick={() => handleEmail(lead)} title="Send Email">📧</button>
                    <button className="btn-action notes" onClick={() => handleNotes(lead)} title="Notes & Follow-up">📝</button>
                    {lead.converted_contact_id ? (
                      <span className="lead-converted-badge" title={`Converted to Contact: ${lead.converted_contact_name || ''}`}>✅ Converted</span>
                    ) : (
                      <button className="btn-action convert" onClick={() => handleConvertToContact(lead)} title="Convert to Contact">🔄</button>
                    )}
                  </div>
                </div>

                {isExpanded && (
                  <div className="lead-row-details">
                    <p><strong>Company:</strong> {lead.company || '-'}</p>
                    <p><strong>Email:</strong> {lead.email || '-'}</p>
                    <p><strong>Phone:</strong> {lead.phone || '-'}</p>
                    <p><strong>Product:</strong> {lead.product ? productLabel(lead.product) : '-'}</p>
                    <p><strong>Source:</strong> {lead.source || '-'}</p>
                    <p><strong>Score:</strong> {lead.ai_score != null ? lead.ai_score : '-'}%</p>
                    {lead.converted_contact_id && (
                      <p><strong>Converted to Contact:</strong> {lead.converted_contact_name || `#${lead.converted_contact_id}`}</p>
                    )}
                  </div>
                )}

                {isExpanded && (
                  <div className="entity-row-extra">
                    <EntityTags token={token} entityType="lead" entityId={lead.id} />
                    <EntityGroups token={token} entityType="lead" entityId={lead.id} />
                    <EntityCustomFields token={token} entityType="lead" entityId={lead.id} />
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
                <button
                  type="button"
                  className="btn-detect-date"
                  onClick={handleDetectDate}
                  disabled={dateDetecting || !noteDraft.transcript.trim()}
                  title="Ask Claude AI whether these notes mention a next-conversation date"
                >
                  {dateDetecting ? '🗓️ Checking…' : '🗓️ Detect Date'}
                </button>
              </div>
              {dateDetectMessage && (
                <p className="date-detect-message">{dateDetectMessage}</p>
              )}

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
              <div className="notes-history-header">
                <h4>History ({notes.length})</h4>
                <button type="button" className="btn-ai-suggest" onClick={handleAiSuggest} disabled={aiLoading}>
                  {aiLoading ? '✨ Thinking…' : '✨ AI Suggest Follow-up'}
                </button>
              </div>
              {aiSuggestion && (
                <div className="ai-suggestion">{aiSuggestion}</div>
              )}
              {notes.length === 0 ? (
                <p className="no-notes">No notes yet for this lead.</p>
              ) : (
                notes.map((note) => (
                  <div key={note.id} className={`note-entry ${editingNoteId === note.id ? 'editing' : ''}`}>
                    <div className="note-entry-header">
                      <span>📞 {note.call_datetime ? new Date(note.call_datetime).toLocaleString() : '—'}</span>
                      <div className="note-entry-actions">
                        <button className="btn-edit-note" onClick={() => handleEditNote(note)} title="Edit">✏️</button>
                        <button className="btn-delete-note" onClick={() => deleteNote(selectedLead.id, note.id)} title="Delete">🗑️</button>
                      </div>
                    </div>
                    {note.next_conversation && (
                      <div className="note-next">⏭️ Next: {new Date(note.next_conversation).toLocaleString()}</div>
                    )}
                    {note.transcript && <p className="note-transcript">{note.transcript}</p>}
                    {note.audio_url && (
                      <audio controls src={`${API_URL}${note.audio_url}`} className="voice-playback" />
                    )}
                    {note.updated_at && note.updated_at !== note.created_at && (
                      <div className="note-updated">Edited {new Date(note.updated_at).toLocaleString()}</div>
                    )}
                  </div>
                ))
              )}
            </div>

            <div className="notes-history activity-timeline">
              <div className="notes-history-header">
                <h4>Activity Timeline ({activities.length})</h4>
              </div>
              {loadingActivities ? (
                <p className="no-notes">Loading…</p>
              ) : activities.length === 0 ? (
                <p className="no-notes">No calls, emails, WhatsApp, SMS, tasks, meetings or campaigns logged for this lead yet.</p>
              ) : (
                activities.map((a) => (
                  <div key={a.id} className="note-entry activity-entry">
                    <div className="note-entry-header">
                      <span>{ACTIVITY_ICONS[a.channel] || '•'} {a.channel} - {new Date(a.timestamp).toLocaleString()}</span>
                      {a.outcome && <span className="activity-outcome">{a.outcome}</span>}
                    </div>
                    {a.detail && <p className="note-transcript">{a.detail}</p>}
                  </div>
                ))
              )}
            </div>

            <div className="notes-history activity-timeline">
              <div className="notes-history-header">
                <h4>Deals ({leadDeals.length})</h4>
              </div>
              {loadingLeadDeals ? (
                <p className="no-notes">Loading…</p>
              ) : leadDeals.length === 0 ? (
                <p className="no-notes">Not converted to a deal yet.</p>
              ) : (
                leadDeals.map((d) => (
                  <div key={d.id} className="note-entry activity-entry">
                    <div className="note-entry-header">
                      <span>💼 {dealLabel(d)}</span>
                      <span className="activity-outcome">{d.stage}</span>
                    </div>
                    {d.company_name && <p className="note-transcript">Company: {d.company_name}</p>}
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
