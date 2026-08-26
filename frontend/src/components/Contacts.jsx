import React, { useState, useEffect, useRef } from 'react';
import {
  getContactsList, createContact, updateContact, deleteContact, assignContact, getTeam,
  getContactNotes, createContactNote, updateContactNote, deleteContactNote,
  uploadNoteAudio, API_URL, dialCall, aiSuggestContactFollowup,
  sendWhatsApp, sendEmailReal, sendSms, detectFollowupDate,
  getCompanies, linkContactCompany, getActivities, getCompanyDeals
} from '../services/api';
import { LOAN_PRODUCTS } from '../constants/loanProducts';
import '../styles/Contacts.css';

const STATUS_OPTIONS = ['Active', 'Renewal Due', 'Lapsed', 'Inactive'];
const ACTIVITY_ICONS = { Call: '📞', Email: '✉️', WhatsApp: '💬', SMS: '📱', Task: '✅', Meeting: '📅', Campaign: '📢' };
const statusClass = (status) => (status || '').toLowerCase().replace(/\s+/g, '-');
const dealLabel = (deal) => {
  const productInfo = LOAN_PRODUCTS.find((p) => p.id === deal.loan_product);
  return `${productInfo?.name || deal.loan_product} · ₹${(deal.deal_value || 0).toLocaleString('en-IN')} · ${deal.process_status || 'Login'}`;
};

const WhatsAppIcon = () => (
  <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true">
    <path d="M12.04 2c-5.46 0-9.91 4.45-9.91 9.91 0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21h.004c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.816 9.816 0 0012.05 2zm5.71 14.14c-.24.68-1.4 1.31-1.94 1.36-.5.05-1.13.07-1.82-.11-.42-.11-.96-.31-1.65-.61-2.9-1.25-4.79-4.17-4.94-4.36-.15-.19-1.18-1.57-1.18-3 0-1.43.75-2.13 1.02-2.42.27-.29.59-.36.78-.36l.56.01c.18 0 .42-.07.66.5.24.58.83 2 .9 2.15.07.15.12.32.02.51-.09.19-.14.31-.28.48-.14.17-.29.37-.42.5-.14.14-.28.29-.12.56.16.28.71 1.17 1.52 1.89 1.05.93 1.93 1.22 2.21 1.36.28.14.44.12.6-.07.16-.19.68-.79.86-1.06.18-.28.36-.23.6-.14.24.09 1.53.72 1.79.85.26.13.44.19.5.3.06.11.06.63-.18 1.31z" />
  </svg>
);

const emptyContactForm = { name: '', company: '', email: '', phone: '', city: '', amount: '', bank: '', status: 'Active', renewal_date: '' };
const emptyNoteDraft = { callDateTime: '', nextConversation: '', transcript: '' };

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

// Renewal dates in an imported CSV could come in as ISO (2026-09-15, matches our own Export),
// DD/MM/YYYY or DD-MM-YYYY (common in India), or other spreadsheet date formats. Normalizes
// to the "YYYY-MM-DD" the backend/date input expects; returns null if it can't be parsed
// rather than silently saving a garbage date.
const parseImportDate = (raw) => {
  const value = (raw || '').trim();
  if (!value) return null;
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return value;
  const dmy = value.match(/^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$/);
  if (dmy) {
    const [, d, m, y] = dmy;
    return `${y}-${m.padStart(2, '0')}-${d.padStart(2, '0')}`;
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed.toISOString().slice(0, 10);
};

export default function Contacts() {
  const [contacts, setContacts] = useState([]);
  const [teamMembers, setTeamMembers] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const token = localStorage.getItem('token');

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
  const [notes, setNotes] = useState([]);
  const [activities, setActivities] = useState([]);
  const [loadingActivities, setLoadingActivities] = useState(false);
  const [companyDeals, setCompanyDeals] = useState([]);
  const [loadingCompanyDeals, setLoadingCompanyDeals] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [dateDetectMessage, setDateDetectMessage] = useState(null);
  const [dateDetecting, setDateDetecting] = useState(false);
  const [noteDraft, setNoteDraft] = useState(emptyNoteDraft);
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

  useEffect(() => {
    fetchContacts();
    fetchTeamMembers();
    fetchCompanies();
  }, []);

  const fetchContacts = async () => {
    try {
      const data = await getContactsList(token);
      setContacts(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching contacts:', error);
    }
  };

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

  const handleCompanyLinkChange = async (contactId, companyIdRaw) => {
    const companyId = companyIdRaw ? Number(companyIdRaw) : null;
    const previous = contacts.find((c) => c.id === contactId);
    setContacts((prev) => prev.map((c) => (c.id === contactId
      ? { ...c, company_id: companyId, company_name: companies.find((co) => co.id === companyId)?.name || null }
      : c)));
    try {
      await linkContactCompany(token, contactId, companyId);
    } catch (error) {
      console.error('Error linking contact to company:', error);
      if (previous) {
        setContacts((prev) => prev.map((c) => (c.id === contactId ? previous : c)));
      }
      alert('Failed to link company. Please try again.');
    }
  };

  const handleAssignChange = async (contactId, teamMemberIdRaw) => {
    const teamMemberId = teamMemberIdRaw ? Number(teamMemberIdRaw) : null;
    const previous = contacts.find((c) => c.id === contactId);
    setContacts((prev) => prev.map((c) => (c.id === contactId
      ? { ...c, assigned_team_member_id: teamMemberId, assigned_team_member_name: teamMembers.find((m) => m.id === teamMemberId)?.name || null }
      : c)));
    try {
      await assignContact(token, contactId, teamMemberId);
    } catch (error) {
      console.error('Error assigning contact:', error);
      if (previous) {
        setContacts((prev) => prev.map((c) => (c.id === contactId ? previous : c)));
      }
      alert('Failed to assign contact. Please try again.');
    }
  };

  const handleStatusChange = async (contactId, newStatus) => {
    const previous = contacts.find((c) => c.id === contactId);
    setContacts((prev) => prev.map((c) => (c.id === contactId ? { ...c, status: newStatus } : c)));
    try {
      await updateContact(token, contactId, { status: newStatus });
    } catch (error) {
      console.error('Error updating contact status:', error);
      if (previous) {
        setContacts((prev) => prev.map((c) => (c.id === contactId ? previous : c)));
      }
      alert('Failed to update status. Please try again.');
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
            name: obj.name || 'Unnamed Contact',
            company: obj.company || '',
            email: obj.email || '',
            phone: obj.phone || '',
            city: obj.city || obj['city/area'] || obj.location || '',
            score: obj.score ? Number(obj.score) : null,
            amount: obj.amount ? Number(obj.amount) : null,
            bank: obj.bank || '',
            status: obj.status || 'Active',
            renewal_date: parseImportDate(obj['renewal date'] || obj.renewal_date || obj.renewaldate),
            assignedName
          };
        });

        let created = 0;
        let failed = 0;
        for (const row of imported) {
          try {
            const { score, assignedName, ...contactData } = row;
            const newContact = await createContact(token, contactData);
            if (score !== null && !Number.isNaN(score)) {
              await updateContact(token, newContact.id, { score });
            }
            if (assignedName) {
              const match = teamMembers.find((m) => m.name.toLowerCase() === assignedName.toLowerCase());
              if (match) await assignContact(token, newContact.id, match.id);
            }
            created++;
          } catch (rowErr) {
            console.error('Error importing row:', row, rowErr);
            failed++;
          }
        }
        await fetchContacts();
        alert(failed > 0
          ? `Imported ${created} contact(s). ${failed} row(s) failed - check the console for details.`
          : `Imported ${created} contact(s) successfully.`);
      } catch (err) {
        alert('Failed to parse CSV file: ' + err.message);
      } finally {
        e.target.value = '';
      }
    };
    reader.readAsText(file);
  };

  const handleExportCSV = () => {
    const headers = ['Name', 'Company', 'Email', 'Phone', 'City/Area', 'Score', 'Amount', 'Bank', 'Status', 'Renewal Date', 'Employee'];
    const rows = filteredContacts.map((c) => [
      c.name, c.company || '', c.email || '', c.phone || '', c.city || '', c.score ?? '',
      c.amount ?? '', c.bank || '', c.status || '', c.renewal_date || '', c.assigned_team_member_name || ''
    ]);
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

  const handleDownloadTemplate = () => {
    const headers = ['Name', 'Company', 'Email', 'Phone', 'City', 'Amount', 'Bank', 'Status', 'Renewal Date', 'Employee'];
    const example = ['Rohit Sharma', 'ABC Traders', 'rohit@example.com', '9876543210', 'Pune', '500000', 'HDFC ERGO', 'Active', '2026-09-15', 'Rajesh Kumar'];
    const csvContent = [headers, example]
      .map((row) => row.map((field) => `"${String(field).replace(/"/g, '""')}"`).join(','))
      .join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'contacts-import-template.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleCall = async (contact) => {
    if (!contact.phone) {
      alert('No phone number available');
      return;
    }
    // Try a real Twilio click-to-call first (rings the agent, then bridges to the contact);
    // falls back to a plain tel: link when Twilio isn't configured on the server.
    try {
      const result = await dialCall(token, contact.phone, { contactId: contact.id });
      if (result.configured) {
        alert(result.message);
        return;
      }
    } catch (error) {
      console.error('Error placing Twilio call:', error);
    }
    window.location.href = `tel:${contact.phone}`;
  };

  const handleWhatsApp = async (contact) => {
    if (!contact.phone) {
      alert('No phone number available');
      return;
    }
    // Try a real WhatsApp Business API send first; falls back to opening a wa.me link
    // when it isn't configured on the server.
    try {
      const result = await sendWhatsApp(token, contact.phone, `Hi ${contact.name}, this is ArthaInvest reaching out.`, { contactId: contact.id });
      if (result.configured) {
        alert(result.message);
        return;
      }
    } catch (error) {
      console.error('Error sending WhatsApp message:', error);
    }
    const url = `https://wa.me/${contact.phone.replace(/\D/g, '')}`;
    window.open(url, '_blank');
  };

  const handleSms = async (contact) => {
    if (!contact.phone) {
      alert('No phone number available');
      return;
    }
    const message = window.prompt(`SMS to ${contact.name}:`, `Hi ${contact.name}, this is ArthaInvest.`);
    if (!message) return;
    try {
      const result = await sendSms(token, contact.phone, message, { contactId: contact.id });
      if (result.configured) {
        alert(result.message);
        return;
      }
    } catch (error) {
      console.error('Error sending SMS:', error);
    }
    window.location.href = `sms:${contact.phone}`;
  };

  const handleEmail = (contact) => {
    setSelectedContact(contact);
    setShowEmailModal(true);
  };

  const sendEmail = async () => {
    if (!emailSubject.trim() || !emailBody.trim()) return;
    // Try a real SMTP send first; falls back to opening a mailto: link when SMTP isn't
    // configured on the server.
    try {
      const result = await sendEmailReal(token, selectedContact.email, emailSubject, emailBody, { contactId: selectedContact.id });
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
    window.location.href = `mailto:${selectedContact.email}?subject=${encodeURIComponent(emailSubject)}&body=${encodeURIComponent(emailBody)}`;
    setEmailSubject('');
    setEmailBody('');
    setShowEmailModal(false);
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
      city: contact.city || '',
      amount: contact.amount ?? '',
      bank: contact.bank || '',
      status: contact.status || 'Active',
      renewal_date: contact.renewal_date || ''
    });
    setShowForm(true);
  };

  const handleDeleteContact = async (contactId) => {
    if (!window.confirm('Are you sure you want to delete this contact?')) return;
    try {
      await deleteContact(token, contactId);
      setContacts((prev) => prev.filter((c) => c.id !== contactId));
    } catch (error) {
      console.error('Error deleting contact:', error);
      alert('Failed to delete contact. Please try again.');
    }
  };

  const handleSaveContact = async (e) => {
    e.preventDefault();
    if (!contactForm.name.trim()) return;

    const payload = {
      ...contactForm,
      amount: contactForm.amount === '' ? null : Number(contactForm.amount),
      renewal_date: contactForm.renewal_date === '' ? null : contactForm.renewal_date
    };

    try {
      if (editingContactId) {
        await updateContact(token, editingContactId, payload);
      } else {
        await createContact(token, payload);
      }
      setShowForm(false);
      setContactForm(emptyContactForm);
      setEditingContactId(null);
      fetchContacts();
    } catch (error) {
      console.error('Error saving contact:', error);
      alert('Failed to save contact. Please try again.');
    }
  };

  const handleNotes = async (contact) => {
    setSelectedContact(contact);
    resetNoteDraft();
    setIsRecording(false);
    setAiSuggestion(null);
    setDateDetectMessage(null);
    setShowNotes(true);
    try {
      const data = await getContactNotes(token, contact.id);
      setNotes(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching notes:', error);
      setNotes([]);
    }
    setLoadingActivities(true);
    try {
      const activityData = await getActivities(token, null, { contactId: contact.id });
      setActivities(Array.isArray(activityData) ? activityData : []);
    } catch (error) {
      console.error('Error fetching activity timeline:', error);
      setActivities([]);
    } finally {
      setLoadingActivities(false);
    }

    if (contact.company_id) {
      setLoadingCompanyDeals(true);
      try {
        const dealsData = await getCompanyDeals(token, contact.company_id);
        setCompanyDeals(Array.isArray(dealsData) ? dealsData : []);
      } catch (error) {
        console.error('Error fetching company deals:', error);
        setCompanyDeals([]);
      } finally {
        setLoadingCompanyDeals(false);
      }
    } else {
      setCompanyDeals([]);
    }
  };

  const handleAiSuggest = async () => {
    if (!selectedContact) return;
    setAiLoading(true);
    setAiSuggestion(null);
    try {
      const result = await aiSuggestContactFollowup(token, selectedContact.id);
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

  const handleEditNote = (note) => {
    revokeIfLocalBlob(draftAudioUrl);
    setNoteDraft({
      callDateTime: note.call_datetime || '',
      nextConversation: note.next_conversation || '',
      transcript: note.transcript || ''
    });
    // Load the previously saved recording for playback; a fresh recording (if the user makes
    // one) replaces it on save via draftAudioBlobRef, which stays null until that happens.
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
    if (!selectedContact) return;
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
        ? await updateContactNote(token, selectedContact.id, editingNoteId, payload)
        : await createContactNote(token, selectedContact.id, payload);

      if (draftAudioBlobRef.current) {
        await uploadNoteAudio(token, selectedContact.id, savedNote.id, draftAudioBlobRef.current);
      }

      const data = await getContactNotes(token, selectedContact.id);
      setNotes(Array.isArray(data) ? data : []);
      resetNoteDraft();
    } catch (error) {
      console.error('Error saving note:', error);
      alert('Failed to save note. Please try again.');
    }
  };

  const deleteNote = async (contactId, noteId) => {
    try {
      await deleteContactNote(token, contactId, noteId);
      setNotes((prev) => prev.filter((n) => n.id !== noteId));
      if (editingNoteId === noteId) resetNoteDraft();
    } catch (error) {
      console.error('Error deleting note:', error);
      alert('Failed to delete note. Please try again.');
    }
  };

  const filteredContacts = contacts.filter(c =>
    (c.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (c.email || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

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
          <button className="btn-secondary" onClick={handleDownloadTemplate} title="Download a blank CSV with the correct column headers, including Renewal Date">
            📄 Template
          </button>
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
        {filteredContacts.length === 0 ? (
          <p className="no-data">No contacts yet. Add one to get started.</p>
        ) : filteredContacts.map((contact) => {
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
                  <button className="btn-action sms" onClick={() => handleSms(contact)} title="Send SMS">📱</button>
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

              <div className="contact-row-meta">
                {contact.city && (
                  <span className="contact-location-badge" title="Location">📍 {contact.city}</span>
                )}

                <select
                  className={`status-select-compact status-${statusClass(contact.status)}`}
                  value={contact.status || 'Active'}
                  onChange={(e) => handleStatusChange(contact.id, e.target.value)}
                >
                  {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>

                <select
                  className="employee-assign-select"
                  value={contact.assigned_team_member_id || ''}
                  onChange={(e) => handleAssignChange(contact.id, e.target.value)}
                  title="Assigned employee"
                >
                  <option value="">Unassigned</option>
                  {teamMembers.map((m) => (
                    <option key={m.id} value={m.id}>{m.name}</option>
                  ))}
                </select>

                <select
                  className="company-link-select"
                  value={contact.company_id || ''}
                  onChange={(e) => handleCompanyLinkChange(contact.id, e.target.value)}
                  title="Linked company"
                >
                  <option value="">🏢 No linked company</option>
                  {companies.map((co) => (
                    <option key={co.id} value={co.id}>🏢 {co.name}</option>
                  ))}
                </select>

                {(contact.amount != null || contact.bank) && (
                  <span className="contact-amount-bank-badge" title="Amount / Bank">
                    {contact.amount != null ? `₹${Number(contact.amount).toLocaleString('en-IN')}` : ''}
                    {contact.amount != null && contact.bank ? ' · ' : ''}
                    {contact.bank || ''}
                  </span>
                )}

                {contact.renewal_date && (
                  <span className="contact-renewal-badge" title="Renewal Date">
                    📅 Renews {new Date(contact.renewal_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                  </span>
                )}
              </div>

              {isExpanded && (
                <div className="contact-row-details">
                  <p><strong>Company:</strong> {contact.company_name || contact.company || '-'}{contact.company_name && contact.company && contact.company !== contact.company_name ? ` (typed: ${contact.company})` : ''}</p>
                  <p><strong>Email:</strong> {contact.email || '-'}</p>
                  <p><strong>Phone:</strong> {contact.phone || '-'}</p>
                  <p><strong>City/Area:</strong> 📍 {contact.city || '-'}</p>
                  <p><strong>Amount:</strong> {contact.amount != null ? `₹${Number(contact.amount).toLocaleString('en-IN')}` : '-'}</p>
                  <p><strong>Bank/Insurer:</strong> {contact.bank || '-'}</p>
                  <p><strong>Status:</strong> {contact.status || '-'}</p>
                  <p><strong>Renewal Date:</strong> {contact.renewal_date ? new Date(contact.renewal_date).toLocaleDateString('en-IN') : '-'}</p>
                  <p><strong>Assigned To:</strong> {contact.assigned_team_member_name || 'Unassigned'}</p>
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
                  <label>City/Area (Location)</label>
                  <input
                    type="text"
                    value={contactForm.city}
                    onChange={(e) => setContactForm({ ...contactForm, city: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Amount (₹)</label>
                  <input
                    type="number"
                    min="0"
                    value={contactForm.amount}
                    onChange={(e) => setContactForm({ ...contactForm, amount: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Bank / Insurer</label>
                  <input
                    type="text"
                    placeholder="e.g. HDFC Bank, TATA AIG..."
                    value={contactForm.bank}
                    onChange={(e) => setContactForm({ ...contactForm, bank: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Status</label>
                  <select
                    value={contactForm.status}
                    onChange={(e) => setContactForm({ ...contactForm, status: e.target.value })}
                  >
                    {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label>Renewal Date</label>
                  <input
                    type="date"
                    value={contactForm.renewal_date}
                    onChange={(e) => setContactForm({ ...contactForm, renewal_date: e.target.value })}
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
                  <p className="no-notes">No notes yet for this contact.</p>
                ) : (
                  notes.map((note) => (
                    <div key={note.id} className={`note-entry ${editingNoteId === note.id ? 'editing' : ''}`}>
                      <div className="note-entry-header">
                        <span>📞 {note.call_datetime ? new Date(note.call_datetime).toLocaleString() : '—'}</span>
                        <div className="note-entry-actions">
                          <button className="btn-edit-note" onClick={() => handleEditNote(note)} title="Edit">✏️</button>
                          <button className="btn-delete-note" onClick={() => deleteNote(selectedContact.id, note.id)} title="Delete">🗑️</button>
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
                  <p className="no-notes">No calls, emails, WhatsApp, SMS, tasks, meetings or campaigns logged for this contact yet.</p>
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
                  <h4>Company Deals ({companyDeals.length})</h4>
                </div>
                {!selectedContact.company_id ? (
                  <p className="no-notes">Not linked to a company - link one above to see its deals here.</p>
                ) : loadingCompanyDeals ? (
                  <p className="no-notes">Loading…</p>
                ) : companyDeals.length === 0 ? (
                  <p className="no-notes">No deals yet for {selectedContact.company_name}.</p>
                ) : (
                  companyDeals.map((d) => (
                    <div key={d.id} className="note-entry activity-entry">
                      <div className="note-entry-header">
                        <span>💼 {dealLabel(d)}</span>
                        <span className="activity-outcome">{d.stage}</span>
                      </div>
                      {d.assigned_team_member_name && <p className="note-transcript">Owner: {d.assigned_team_member_name}</p>}
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
