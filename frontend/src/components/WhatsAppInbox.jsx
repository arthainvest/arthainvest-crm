import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  getWhatsAppConversations, getWhatsAppMessages, replyWhatsAppConversation,
  assignWhatsAppConversation, updateWhatsAppConversationStatus, optOutWhatsAppConversation,
  getWhatsAppTemplates, getQuickReplies, getTeam, sendWhatsApp
} from '../services/api';
import '../styles/WhatsAppInbox.css';

const STATUS_TABS = [
  { key: 'all', label: 'All' },
  { key: 'open', label: 'Open' },
  { key: 'handed_off', label: 'Handed Off' },
  { key: 'closed', label: 'Closed' }
];

const TICK = { sent: '✓', delivered: '✓✓', read: '✓✓', failed: '⚠️', received: '', queued: '…' };

function conversationTitle(convo) {
  return convo.contact_name || convo.lead_name || convo.wa_number;
}

function formatTime(ts) {
  if (!ts) return '';
  const d = new Date(ts.endsWith('Z') || ts.includes('T') ? ts : ts.replace(' ', 'T'));
  if (Number.isNaN(d.getTime())) return '';
  const now = new Date();
  const sameDay = d.toDateString() === now.toDateString();
  return sameDay
    ? d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : d.toLocaleDateString([], { day: '2-digit', month: 'short' });
}

export default function WhatsAppInbox() {
  const token = localStorage.getItem('token');

  const [conversations, setConversations] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedId, setSelectedId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loadingMessages, setLoadingMessages] = useState(false);

  const [composerText, setComposerText] = useState('');
  const [sending, setSending] = useState(false);

  const [team, setTeam] = useState([]);
  const [quickReplies, setQuickReplies] = useState([]);
  const [showQuickReplies, setShowQuickReplies] = useState(false);

  const [templates, setTemplates] = useState([]);
  const [templatesMessage, setTemplatesMessage] = useState('');
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [templateForm, setTemplateForm] = useState({ name: '', language: 'en_US', params: '' });

  const [showNewModal, setShowNewModal] = useState(false);
  const [newForm, setNewForm] = useState({ to: '', message: '' });

  const messagesEndRef = useRef(null);
  const selectedIdRef = useRef(null);
  selectedIdRef.current = selectedId;

  const fetchConversations = useCallback(async () => {
    try {
      const data = await getWhatsAppConversations(token, { status: statusFilter === 'all' ? null : statusFilter });
      setConversations(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching WhatsApp conversations:', error);
    }
  }, [token, statusFilter]);

  const fetchMessages = useCallback(async (conversationId, { silent } = {}) => {
    if (!conversationId) return;
    if (!silent) setLoadingMessages(true);
    try {
      const data = await getWhatsAppMessages(token, conversationId);
      if (selectedIdRef.current === conversationId) {
        setMessages(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      console.error('Error fetching WhatsApp messages:', error);
    } finally {
      if (!silent) setLoadingMessages(false);
    }
  }, [token]);

  useEffect(() => {
    fetchConversations();
    getTeam(token).then(setTeam).catch((e) => console.error('Error fetching team:', e));
    getQuickReplies(token).then(setQuickReplies).catch((e) => console.error('Error fetching quick replies:', e));
  }, [fetchConversations, token]);

  // Poll the conversation list for new activity, and the open thread for new messages/status.
  useEffect(() => {
    const listInterval = setInterval(fetchConversations, 10000);
    return () => clearInterval(listInterval);
  }, [fetchConversations]);

  useEffect(() => {
    if (!selectedId) return;
    const msgInterval = setInterval(() => fetchMessages(selectedId, { silent: true }), 5000);
    return () => clearInterval(msgInterval);
  }, [selectedId, fetchMessages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const selectedConvo = conversations.find((c) => c.id === selectedId) || null;

  const handleSelect = (convo) => {
    setSelectedId(convo.id);
    setComposerText('');
    setShowQuickReplies(false);
    fetchMessages(convo.id);
  };

  const handleSendText = async () => {
    if (!selectedConvo || !composerText.trim() || sending) return;
    setSending(true);
    try {
      const result = await replyWhatsAppConversation(token, selectedConvo.id, { message: composerText.trim() });
      if (result.configured === false) {
        alert('WhatsApp Business API is not configured on this server yet - add WHATSAPP_TOKEN and WHATSAPP_PHONE_ID to the backend .env to send real messages.');
      } else if (!result.message?.toLowerCase().includes('sent')) {
        alert(result.message);
      }
      setComposerText('');
      await fetchMessages(selectedConvo.id, { silent: true });
      await fetchConversations();
    } catch (error) {
      console.error('Error sending message:', error);
      alert('Failed to send message. Please try again.');
    } finally {
      setSending(false);
    }
  };

  const handleOpenTemplates = async () => {
    setShowTemplateModal(true);
    if (templates.length === 0) {
      try {
        const result = await getWhatsAppTemplates(token);
        setTemplates(result.templates || []);
        if (!result.configured) setTemplatesMessage(result.message);
      } catch (error) {
        console.error('Error fetching templates:', error);
      }
    }
  };

  const handleSendTemplate = async () => {
    if (!selectedConvo || !templateForm.name.trim()) return;
    const params = templateForm.params.split(',').map((p) => p.trim()).filter(Boolean);
    try {
      const result = await replyWhatsAppConversation(token, selectedConvo.id, {
        template_name: templateForm.name.trim(),
        template_language: templateForm.language || 'en_US',
        template_params: params.length ? params : undefined
      });
      if (result.configured === false) {
        alert('WhatsApp Business API is not configured on this server yet.');
      } else {
        alert(result.message);
      }
      setShowTemplateModal(false);
      setTemplateForm({ name: '', language: 'en_US', params: '' });
      await fetchMessages(selectedConvo.id, { silent: true });
      await fetchConversations();
    } catch (error) {
      console.error('Error sending template:', error);
      alert('Failed to send template message.');
    }
  };

  const handleAssign = async (e) => {
    if (!selectedConvo) return;
    const userId = e.target.value ? Number(e.target.value) : null;
    try {
      await assignWhatsAppConversation(token, selectedConvo.id, userId);
      await fetchConversations();
    } catch (error) {
      console.error('Error assigning conversation:', error);
    }
  };

  const handleStatusChange = async (status) => {
    if (!selectedConvo) return;
    try {
      await updateWhatsAppConversationStatus(token, selectedConvo.id, status);
      await fetchConversations();
    } catch (error) {
      console.error('Error updating conversation status:', error);
    }
  };

  const handleOptOut = async () => {
    if (!selectedConvo) return;
    if (!window.confirm(`Mark ${conversationTitle(selectedConvo)} as opted-out of WhatsApp messages?`)) return;
    try {
      await optOutWhatsAppConversation(token, selectedConvo.id);
      await fetchConversations();
    } catch (error) {
      console.error('Error opting out conversation:', error);
    }
  };

  const handlePickQuickReply = (reply) => {
    setComposerText(reply.message);
    setShowQuickReplies(false);
  };

  const handleStartNewConversation = async (e) => {
    e.preventDefault();
    if (!newForm.to.trim() || !newForm.message.trim()) return;
    try {
      const result = await sendWhatsApp(token, newForm.to.trim(), newForm.message.trim());
      if (result.configured === false) {
        alert('WhatsApp Business API is not configured on this server yet - add WHATSAPP_TOKEN and WHATSAPP_PHONE_ID to the backend .env to send real messages.');
      } else {
        alert(result.message);
      }
      setShowNewModal(false);
      setNewForm({ to: '', message: '' });
      await fetchConversations();
    } catch (error) {
      console.error('Error starting conversation:', error);
      alert('Failed to start conversation.');
    }
  };

  const filteredConversations = conversations.filter((c) =>
    conversationTitle(c).toLowerCase().includes(searchTerm.toLowerCase()) ||
    (c.wa_number || '').includes(searchTerm)
  );

  return (
    <div className={`wa-inbox ${selectedId ? 'has-selected' : ''}`}>
      <div className="wa-sidebar">
        <div className="wa-sidebar-header">
          <h1>WhatsApp</h1>
          <button className="btn-primary wa-new-btn" onClick={() => setShowNewModal(true)}>+ New</button>
        </div>

        <div className="wa-tabs">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.key}
              className={`wa-tab ${statusFilter === tab.key ? 'active' : ''}`}
              onClick={() => setStatusFilter(tab.key)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="wa-search">
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="wa-conversation-list">
          {filteredConversations.length === 0 ? (
            <p className="no-data">No conversations yet. They'll appear here as customers message you, or start one with + New.</p>
          ) : filteredConversations.map((convo) => (
            <button
              key={convo.id}
              className={`wa-conversation-item ${selectedId === convo.id ? 'active' : ''}`}
              onClick={() => handleSelect(convo)}
            >
              <div className="wa-conversation-avatar">{conversationTitle(convo).charAt(0).toUpperCase()}</div>
              <div className="wa-conversation-body">
                <div className="wa-conversation-top">
                  <span className="wa-conversation-name">{conversationTitle(convo)}</span>
                  <span className="wa-conversation-time">{formatTime(convo.last_message_at)}</span>
                </div>
                <div className="wa-conversation-preview">
                  {convo.opted_out_at && <span className="wa-badge opted-out">Opted out</span>}
                  <span className="wa-preview-text">{convo.last_message || 'No messages yet'}</span>
                </div>
              </div>
              {convo.status !== 'open' && <span className={`wa-status-dot ${convo.status}`} title={convo.status} />}
            </button>
          ))}
        </div>
      </div>

      <div className="wa-thread">
        {!selectedConvo ? (
          <div className="wa-thread-empty">
            <p>Select a conversation to view the message history.</p>
          </div>
        ) : (
          <>
            <div className="wa-thread-header">
              <button type="button" className="wa-back-btn" onClick={() => setSelectedId(null)} title="Back to conversations">←</button>
              <div className="wa-thread-heading">
                <h2>{conversationTitle(selectedConvo)}</h2>
                <span className="wa-thread-number">{selectedConvo.wa_number}</span>
              </div>
              <div className="wa-thread-controls">
                <select value={selectedConvo.assigned_user_id || ''} onChange={handleAssign} title="Assign agent">
                  <option value="">Unassigned</option>
                  {team.filter((m) => m.user_id).map((m) => (
                    <option key={m.id} value={m.user_id}>{m.name}</option>
                  ))}
                </select>
                <select value={selectedConvo.status} onChange={(e) => handleStatusChange(e.target.value)} title="Conversation status">
                  <option value="open">Open</option>
                  <option value="handed_off">Handed Off</option>
                  <option value="closed">Closed</option>
                </select>
                {!selectedConvo.opted_out_at && (
                  <button className="btn-secondary wa-optout-btn" onClick={handleOptOut}>Mark Opted-Out</button>
                )}
              </div>
            </div>

            {selectedConvo.opted_out_at && (
              <div className="wa-optout-banner">
                🚫 Opted out on {formatTime(selectedConvo.opted_out_at)} ({selectedConvo.opt_out_reason || 'no reason given'}) - this contact cannot be messaged.
              </div>
            )}

            <div className="wa-messages">
              {loadingMessages ? (
                <p className="no-data">Loading messages...</p>
              ) : messages.length === 0 ? (
                <p className="no-data">No messages yet in this conversation.</p>
              ) : messages.map((msg) => (
                <div key={msg.id} className={`wa-bubble-row ${msg.direction}`}>
                  <div className={`wa-bubble ${msg.direction} ${msg.status === 'failed' ? 'failed' : ''}`}>
                    {msg.message_type === 'template' && msg.template_name && (
                      <div className="wa-bubble-template-tag">Template: {msg.template_name}</div>
                    )}
                    <div className="wa-bubble-text">{msg.body || (msg.message_type !== 'text' ? `[${msg.message_type}]` : '')}</div>
                    <div className="wa-bubble-meta">
                      <span>{formatTime(msg.created_at)}</span>
                      {msg.direction === 'out' && <span className={`wa-tick ${msg.status}`}>{TICK[msg.status] || ''}</span>}
                    </div>
                    {msg.status === 'failed' && msg.error_message && (
                      <div className="wa-bubble-error">{msg.error_message}</div>
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            <div className="wa-composer">
              {showQuickReplies && (
                <div className="wa-quick-reply-list">
                  {quickReplies.length === 0 ? (
                    <p className="no-data">No quick replies saved yet.</p>
                  ) : quickReplies.map((qr) => (
                    <button key={qr.id} className="wa-quick-reply-item" onClick={() => handlePickQuickReply(qr)}>
                      <strong>{qr.shortcut}</strong>
                      <span>{qr.message}</span>
                    </button>
                  ))}
                </div>
              )}
              <div className="wa-composer-row">
                <button
                  type="button"
                  className="btn-secondary wa-composer-action"
                  onClick={() => setShowQuickReplies((v) => !v)}
                  title="Quick replies"
                  disabled={!!selectedConvo.opted_out_at}
                >
                  ⚡
                </button>
                <button
                  type="button"
                  className="btn-secondary wa-composer-action"
                  onClick={handleOpenTemplates}
                  title="Send a template message"
                  disabled={!!selectedConvo.opted_out_at}
                >
                  📄
                </button>
                <textarea
                  rows="1"
                  placeholder={selectedConvo.opted_out_at ? 'This contact has opted out' : 'Type a message...'}
                  value={composerText}
                  disabled={!!selectedConvo.opted_out_at}
                  onChange={(e) => setComposerText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendText();
                    }
                  }}
                />
                <button
                  className="btn-primary wa-send-btn"
                  onClick={handleSendText}
                  disabled={!composerText.trim() || sending || !!selectedConvo.opted_out_at}
                >
                  {sending ? '…' : 'Send'}
                </button>
              </div>
              <p className="wa-composer-hint">
                Freeform text only delivers within 24h of the customer's last message. Outside that window, use a Template.
              </p>
            </div>
          </>
        )}
      </div>

      {/* Template send modal */}
      {showTemplateModal && (
        <div className="modal-overlay" onClick={() => setShowTemplateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Send a Template Message</h2>
              <button className="btn-close" onClick={() => setShowTemplateModal(false)}>×</button>
            </div>
            <div className="modal-body">
              {templatesMessage && <p className="wa-templates-warning">{templatesMessage}</p>}
              {templates.length > 0 && (
                <div className="form-group">
                  <label>Approved templates</label>
                  <select
                    value={templateForm.name}
                    onChange={(e) => {
                      const t = templates.find((tp) => tp.name === e.target.value);
                      setTemplateForm({ ...templateForm, name: e.target.value, language: t?.language || 'en_US' });
                    }}
                  >
                    <option value="">Choose a template...</option>
                    {templates.map((t) => (
                      <option key={t.name} value={t.name}>{t.name} ({t.status})</option>
                    ))}
                  </select>
                </div>
              )}
              <div className="form-group">
                <label>Template name</label>
                <input
                  type="text"
                  placeholder="e.g. order_confirmation"
                  value={templateForm.name}
                  onChange={(e) => setTemplateForm({ ...templateForm, name: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Language code</label>
                <input
                  type="text"
                  value={templateForm.language}
                  onChange={(e) => setTemplateForm({ ...templateForm, language: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Body variables (comma-separated, in order)</label>
                <input
                  type="text"
                  placeholder="e.g. Priya, ₹50,000"
                  value={templateForm.params}
                  onChange={(e) => setTemplateForm({ ...templateForm, params: e.target.value })}
                />
              </div>
              <div className="modal-actions">
                <button className="btn-primary" onClick={handleSendTemplate}>Send Template</button>
                <button className="btn-secondary" onClick={() => setShowTemplateModal(false)}>Cancel</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* New conversation modal */}
      {showNewModal && (
        <div className="modal-overlay" onClick={() => setShowNewModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Start a WhatsApp Conversation</h2>
              <button className="btn-close" onClick={() => setShowNewModal(false)}>×</button>
            </div>
            <form onSubmit={handleStartNewConversation}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Phone number *</label>
                  <input
                    type="tel"
                    required
                    placeholder="+91 98765 43210"
                    value={newForm.to}
                    onChange={(e) => setNewForm({ ...newForm, to: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Message *</label>
                  <textarea
                    rows="4"
                    required
                    placeholder="This only delivers if this number has messaged you in the last 24h - otherwise send a Template instead once the conversation exists."
                    value={newForm.message}
                    onChange={(e) => setNewForm({ ...newForm, message: e.target.value })}
                  />
                </div>
              </div>
              <div className="modal-actions">
                <button type="submit" className="btn-primary">Send</button>
                <button type="button" className="btn-secondary" onClick={() => setShowNewModal(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
