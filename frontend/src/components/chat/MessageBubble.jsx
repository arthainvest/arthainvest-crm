import React from 'react';

const currentUserId = Number(localStorage.getItem('userId'));

function formatTimestamp(ts) {
  if (!ts) return '';
  const iso = ts.includes('T') ? ts : ts.replace(' ', 'T');
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function MessageBubble({ message }) {
  const isMine = message.sender_id === currentUserId;

  return (
    <div className={`chat-message-row ${isMine ? 'outbound' : 'inbound'}`}>
      <div className={`chat-message-bubble ${isMine ? 'outbound' : 'inbound'}`}>
        {!isMine && <div className="chat-message-sender">{message.sender_name}</div>}
        <div className="chat-message-text">{message.body}</div>
        <div className="chat-message-meta">{formatTimestamp(message.created_at)}</div>
      </div>
    </div>
  );
}
