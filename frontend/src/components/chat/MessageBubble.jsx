import React, { useEffect, useState } from 'react';
import { getChatAttachmentUrl } from '../../services/api';
import { useChat } from '../../contexts/ChatContext';

const currentUserId = Number(localStorage.getItem('userId'));
const token = localStorage.getItem('token');

function formatTimestamp(ts) {
  if (!ts) return '';
  const iso = ts.includes('T') ? ts : ts.replace(' ', 'T');
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Renders @username tokens with a bit of visual weight - purely cosmetic, the backend already
// resolved which of these actually correspond to a real conversation member.
function renderBodyWithMentions(body) {
  const parts = body.split(/(@\w+)/g);
  return parts.map((part, i) => (
    part.startsWith('@')
      ? <span key={i} className="chat-mention">{part}</span>
      : <React.Fragment key={i}>{part}</React.Fragment>
  ));
}

export default function MessageBubble({ message, repliedToMessage, onReply, onEdit, onDelete }) {
  const isMine = message.sender_id === currentUserId;
  const isDeleted = !!message.deleted_at;
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState(message.body || '');
  const [saving, setSaving] = useState(false);
  const { leadCache, getLeadInfo, contactCache, getContactInfo } = useChat();
  const leadInfo = message.lead_id ? leadCache[message.lead_id] : null;
  const contactInfo = message.contact_id ? contactCache[message.contact_id] : null;

  // Fetch-once-per-lead/contact: getLeadInfo/getContactInfo themselves no-op if the record is
  // already cached or already being fetched by another bubble, so N messages linked to the same
  // lead/contact cost one request total, not N.
  useEffect(() => {
    if (message.lead_id && !leadInfo) getLeadInfo(message.lead_id);
  }, [message.lead_id, leadInfo, getLeadInfo]);

  useEffect(() => {
    if (message.contact_id && !contactInfo) getContactInfo(message.contact_id);
  }, [message.contact_id, contactInfo, getContactInfo]);

  const handleSaveEdit = async () => {
    const body = editText.trim();
    if (!body || saving) return;
    setSaving(true);
    try {
      await onEdit(message.id, body);
      setEditing(false);
    } catch (err) {
      console.error('Error editing message:', err);
      alert('Failed to edit message. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Delete this message? This cannot be undone, but an audit record is kept.')) return;
    try {
      await onDelete(message.id);
    } catch (err) {
      console.error('Error deleting message:', err);
      alert('Failed to delete message. Please try again.');
    }
  };

  return (
    <div className={`chat-message-row ${isMine ? 'outbound' : 'inbound'}`}>
      <div className={`chat-message-bubble ${isMine ? 'outbound' : 'inbound'} ${isDeleted ? 'deleted' : ''}`}>
        {!isMine && !isDeleted && <div className="chat-message-sender">{message.sender_name}</div>}

        {message.lead_id && !isDeleted && (
          <div className="chat-lead-card">
            <span className="chat-lead-card-tag">Lead</span>
            {leadInfo?.__notFound ? (
              <span className="chat-lead-card-details chat-lead-card-unavailable">No longer available</span>
            ) : leadInfo ? (
              <span className="chat-lead-card-details">
                <span className="chat-lead-card-name">{leadInfo.name}</span>
                {leadInfo.company && <span className="chat-lead-card-company">{leadInfo.company}</span>}
                <span className="chat-lead-card-status">{leadInfo.status}</span>
              </span>
            ) : (
              <span className="chat-lead-card-details">Loading...</span>
            )}
          </div>
        )}

        {message.contact_id && !isDeleted && (
          <div className="chat-lead-card">
            <span className="chat-lead-card-tag">Contact</span>
            {contactInfo?.__notFound ? (
              <span className="chat-lead-card-details chat-lead-card-unavailable">No longer available</span>
            ) : contactInfo ? (
              <span className="chat-lead-card-details">
                <span className="chat-lead-card-name">{contactInfo.name}</span>
                {contactInfo.company && <span className="chat-lead-card-company">{contactInfo.company}</span>}
                <span className="chat-lead-card-status">{contactInfo.status}</span>
              </span>
            ) : (
              <span className="chat-lead-card-details">Loading...</span>
            )}
          </div>
        )}

        {repliedToMessage && !isDeleted && (
          <div className="chat-reply-preview">
            <span className="chat-reply-preview-sender">{repliedToMessage.sender_name}</span>
            <span className="chat-reply-preview-body">
              {repliedToMessage.deleted_at ? 'Message deleted' : (repliedToMessage.body || '').slice(0, 80)}
            </span>
          </div>
        )}

        {isDeleted ? (
          <div className="chat-message-text chat-message-deleted-text">This message was deleted</div>
        ) : (
          <>
            {message.body && <div className="chat-message-text">
              {editing ? (
                <textarea
                  className="chat-message-edit-input"
                  rows="2"
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSaveEdit(); }
                    if (e.key === 'Escape') setEditing(false);
                  }}
                  autoFocus
                />
              ) : renderBodyWithMentions(message.body)}
            </div>}

            {message.attachments && message.attachments.length > 0 && (
              <div className="chat-attachments">
                {message.attachments.map((att) => (
                  message.message_type === 'image' ? (
                    <a key={att.id} href={getChatAttachmentUrl(token, att.id)} target="_blank" rel="noreferrer">
                      <img className="chat-attachment-image" src={getChatAttachmentUrl(token, att.id)} alt={att.file_name} />
                    </a>
                  ) : (
                    <a key={att.id} className="chat-attachment-file" href={getChatAttachmentUrl(token, att.id)} target="_blank" rel="noreferrer">
                      📎 {att.file_name}
                    </a>
                  )
                ))}
              </div>
            )}
          </>
        )}

        <div className="chat-message-meta">
          {message.edited_at && !isDeleted && <span className="chat-edited-label">(edited)</span>}
          {formatTimestamp(message.created_at)}
        </div>

        {!isDeleted && !editing && (
          <div className="chat-message-actions">
            <button type="button" className="chat-message-action-btn" onClick={() => onReply(message)} title="Reply">↩</button>
            {isMine && (
              <>
                <button type="button" className="chat-message-action-btn" onClick={() => setEditing(true)} title="Edit">✎</button>
                <button type="button" className="chat-message-action-btn" onClick={handleDelete} title="Delete">🗑</button>
              </>
            )}
          </div>
        )}

        {editing && (
          <div className="chat-message-edit-actions">
            <button type="button" className="btn-secondary" onClick={() => setEditing(false)}>Cancel</button>
            <button type="button" className="btn-primary" onClick={handleSaveEdit} disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
          </div>
        )}
      </div>
    </div>
  );
}
