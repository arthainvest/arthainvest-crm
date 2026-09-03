import React, { useState, useEffect, useRef } from 'react';
import {
  getWhatsAppConversations, getWhatsAppMessages, sendWhatsAppReply,
  assignWhatsAppConversation, updateWhatsAppConversationStatus, optOutWhatsAppConversation,
  getTeam
} from '../services/api';
import '../styles/WhatsAppInbox.css';

// Matches the status values ConversationStatusUpdate accepts on the backend
// (backend/schemas.py) - anything else is rejected with a 400.
const STATUS_OPTIONS = ['open', 'handed_off', 'closed'];
const STATUS_FILTER_TABS = [
  { key: '', label: 'All' },
  { key: 'open', label: 'Open' },
  { key: 'handed_off', label: 'Handed Off' },
  { key: 'closed', label: 'Closed' }
];

function conversationTitle(convo) {
  return convo.contact_name || convo.lead_name || convo.wa_number;
}

function formatTimestamp(ts) {
  if (!ts) return '';
  // Backend timestamps come back as "YYYY-MM-DD HH:MM:SS" (SQLite/MySQL, no timezone
  // suffix) - normalize to something Date() reliably parses across browsers.
  const iso = ts.includes('T') ? ts : ts.replace(' ', 'T');
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return ts;
  const sameDay = d.toDateString() === new Date().toDateString();
  return sameDay
    ? d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : d.toLocaleDateString([], { day: '2-digit', month: 'short' }) + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function WhatsAppInbox() {
  const token = localStorage.getItem('token');

  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const [selectedId, setSelectedId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loadingMessages, setLoadingMessages] = useState(false);

  const [replyText, setReplyText] = useState('');
  const [sending, setSending] = useState(false);

  const [teamMembers, setTeamMembers] = useState([]);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchConversations(statusFilter);
    fetchTeamMembers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchConversations = async (status) => {
    setLoading(true);
    setError('');
    try {
      const data = await getWhatsAppConversations(token, status || null);
      setConversations(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching WhatsApp conversations:', err);
      setError('Failed to load conversations. Please refresh and try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchTeamMembers = async () => {
    try {
      const data = await getTeam(token);
      setTeamMembers(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching team members:', err);
    }
  };

  const fetchMessages = async (conversationId) => {
    setLoadingMessages(true);
    try {
      const data = await getWhatsAppMessages(token, conversationId);
      setMessages(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching WhatsApp messages:', err);
      setMessages([]);
    } finally {
      setLoadingMessages(false);
    }
  };

  const handleSelectConversation = (convo) => {
    setSelectedId(convo.id);
    setReplyText('');
    fetchMessages(convo.id);
  };

  const selectedConvo = conversations.find((c) => c.id === selectedId) || null;

  const handleSendReply = async () => {
    if (!selectedConvo || !replyText.trim() || sending) return;
    setSending(true);
    try {
      const result = await sendWhatsAppReply(token, selectedConvo.id, replyText.trim());
      if (result.configured === false) {
        alert('WhatsApp Business API is not configured on this server yet - add WHATSAPP_TOKEN and WHATSAPP_PHONE_ID to the backend .env to send real messages.');
      } else if (result.message && !result.message.toLowerCase().includes('sent')) {
        alert(result.message);
      }
      setReplyText('');
      await fetchMessages(selectedConvo.id);
      await fetchConversations(statusFilter);
    } catch (err) {
      console.error('Error sending WhatsApp reply:', err);
      alert('Failed to send reply. Please try again.');
    } finally {
      setSending(false);
    }
  };

  const handleAssign = async (e) => {
    if (!selectedConvo) return;
    const userId = e.target.value ? Number(e.target.value) : null;
    const previous = selectedConvo.assigned_user_id;
    // Optimistic update, reverted below if the request fails - same pattern used for
    // call assignment and integration toggles elsewhere in this app.
    setConversations((prev) => prev.map((c) => (c.id === selectedConvo.id ? { ...c, assigned_user_id: userId } : c)));
    try {
      await assignWhatsAppConversation(token, selectedConvo.id, userId);
    } catch (err) {
      console.error('Error assigning conversation:', err);
      setConversations((prev) => prev.map((c) => (c.id === selectedConvo.id ? { ...c, assigned_user_id: previous } : c)));
      alert('Failed to update assignment. Please try again.');
    }
  };

  const handleStatusChange = async (e) => {
    if (!selectedConvo) return;
    const status = e.target.value;
    const previous = selectedConvo.status;
    setConversations((prev) => prev.map((c) => (c.id === selectedConvo.id ? { ...c, status } : c)));
    try {
      await updateWhatsAppConversationStatus(token, selectedConvo.id, status);
    } catch (err) {
      console.error('Error updating conversation status:', err);
      setConversations((prev) => prev.map((c) => (c.id === selectedConvo.id ? { ...c, status: previous } : c)));
      alert('Failed to update status. Please try again.');
    }
  };

  const handleOptOut = async () => {
    if (!selectedConvo) return;
    if (!window.confirm(`Mark ${conversationTitle(selectedConvo)} as opted-out of WhatsApp messages? They will no longer be messageable from here.`)) return;
    try {
      await optOutWhatsAppConversation(token, selectedConvo.id);
      await fetchConversations(statusFilter);
    } catch (err) {
      console.error('Error opting out conversation:', err);
      alert('Failed to mark this conversation as opted-out. Please try again.');
    }
  };

  // The backend links a conversation's assignee to a login account (users.id), but
  // GET /api/team only exposes team_members.id/name/role/email/phone - not the linked
  // user_id - so there is no endpoint this page can call to resolve a real display name
  // for assigned_user_id. We fall back to the roster id as a best-effort label; see the
  // handoff notes for the real fix (expose user_id on TeamMemberResponse).
  const assigneeLabel = (userId) => {
    if (!userId) return 'Unassigned';
    const match = teamMembers.find((m) => m.id === userId);
    return match ? match.name : `User #${userId}`;
  };

  const filteredConversations = conversations.filter((c) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return conversationTitle(c).toLowerCase().includes(term) || (c.wa_number || '').includes(searchTerm);
  });

  return (
    <div className="wa-inbox-container">
      <div className="wa-inbox-header">
        <h1>WhatsApp Inbox</h1>
      </div>

      {error && <div className="wa-error-banner">{error}</div>}

      <div className={`wa-inbox ${selectedId ? 'has-selected' : ''}`}>
        <div className="wa-list-pane">
          <div className="wa-list-tabs">
            {STATUS_FILTER_TABS.map((tab) => (
              <button
                key={tab.key || 'all'}
                className={`wa-tab-btn ${statusFilter === tab.key ? 'active' : ''}`}
                onClick={() => setStatusFilter(tab.key)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="wa-search">
            <input
              type="text"
              placeholder="Search by name or number..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <div className="wa-conversation-list">
            {loading ? (
              <p className="no-data">Loading conversations...</p>
            ) : filteredConversations.length === 0 ? (
              <p className="no-data">No conversations yet. They will appear here once a customer messages you.</p>
            ) : (
              filteredConversations.map((convo) => (
                <button
                  key={convo.id}
                  className={`wa-conversation-item ${selectedId === convo.id ? 'active' : ''}`}
                  onClick={() => handleSelectConversation(convo)}
                >
                  <div className="wa-avatar">{conversationTitle(convo).charAt(0).toUpperCase()}</div>
                  <div className="wa-conversation-details">
                    <div className="wa-conversation-top-row">
                      <span className="wa-conversation-name">{conversationTitle(convo)}</span>
                      <span className="wa-conversation-time">{formatTimestamp(convo.last_message_at)}</span>
                    </div>
                    <div className="wa-conversation-number">{convo.wa_number}</div>
                    <div className="wa-conversation-preview">
                      {convo.last_message || 'No messages yet'}
                    </div>
                    <div className="wa-conversation-meta">
                      <span className={`wa-status-badge status-${convo.status}`}>{convo.status.replace('_', ' ')}</span>
                      <span className="wa-assignee-badge">{assigneeLabel(convo.assigned_user_id)}</span>
                      {convo.opted_out_at && <span className="wa-optout-badge">Opted out</span>}
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        <div className="wa-thread-pane">
          {!selectedConvo ? (
            <div className="wa-thread-empty">
              <p>Select a conversation to view the message history.</p>
            </div>
          ) : (
            <>
              <div className="wa-thread-header">
                <button type="button" className="wa-back-btn" onClick={() => setSelectedId(null)} title="Back to conversation list">
                  &larr;
                </button>
                <div className="wa-thread-heading">
                  <h2>{conversationTitle(selectedConvo)}</h2>
                  <span className="wa-thread-number">{selectedConvo.wa_number}</span>
                </div>
                <div className="wa-thread-controls">
                  <select value={selectedConvo.assigned_user_id || ''} onChange={handleAssign} title="Assign to team member">
                    <option value="">Unassigned</option>
                    {teamMembers.map((m) => (
                      <option key={m.id} value={m.id}>{m.name}</option>
                    ))}
                  </select>
                  <select value={selectedConvo.status} onChange={handleStatusChange} title="Conversation status">
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>{s.replace('_', ' ')}</option>
                    ))}
                  </select>
                  {!selectedConvo.opted_out_at && (
                    <button className="btn-secondary wa-optout-btn" onClick={handleOptOut}>Opt Out</button>
                  )}
                </div>
              </div>

              {selectedConvo.opted_out_at && (
                <div className="wa-optout-banner">
                  This contact opted out on {formatTimestamp(selectedConvo.opted_out_at)}
                  {selectedConvo.opt_out_reason ? ` (${selectedConvo.opt_out_reason})` : ''} and can no longer be messaged.
                </div>
              )}

              <div className="wa-messages">
                {loadingMessages ? (
                  <p className="no-data">Loading messages...</p>
                ) : messages.length === 0 ? (
                  <p className="no-data">No messages yet in this conversation.</p>
                ) : (
                  messages.map((msg) => (
                    <div key={msg.id} className={`wa-message-row ${msg.direction === 'in' ? 'inbound' : 'outbound'}`}>
                      <div className={`wa-message-bubble ${msg.direction === 'in' ? 'inbound' : 'outbound'} ${msg.status === 'failed' ? 'failed' : ''}`}>
                        {msg.message_type === 'template' && msg.template_name && (
                          <div className="wa-message-tag">Template: {msg.template_name}</div>
                        )}
                        <div className="wa-message-text">
                          {msg.body || (msg.message_type !== 'text' ? `[${msg.message_type}]` : '')}
                        </div>
                        <div className="wa-message-meta">
                          <span>{formatTimestamp(msg.created_at)}</span>
                          {msg.direction === 'out' && <span className="wa-message-status">{msg.status}</span>}
                        </div>
                        {msg.status === 'failed' && msg.error_message && (
                          <div className="wa-message-error">{msg.error_message}</div>
                        )}
                      </div>
                    </div>
                  ))
                )}
                <div ref={messagesEndRef} />
              </div>

              <div className="wa-reply-box">
                <textarea
                  rows="2"
                  placeholder={selectedConvo.opted_out_at ? 'This contact has opted out' : 'Type a reply...'}
                  value={replyText}
                  disabled={!!selectedConvo.opted_out_at || sending}
                  onChange={(e) => setReplyText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendReply();
                    }
                  }}
                />
                <button
                  className="btn-primary wa-send-btn"
                  onClick={handleSendReply}
                  disabled={!replyText.trim() || sending || !!selectedConvo.opted_out_at}
                >
                  {sending ? 'Sending...' : 'Send'}
                </button>
              </div>
              <p className="wa-reply-hint">
                Freeform replies only deliver within 24 hours of the customer's last message.
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
