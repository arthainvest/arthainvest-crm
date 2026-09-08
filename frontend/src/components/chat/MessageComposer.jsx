import React, { useState } from 'react';

export default function MessageComposer({ onSend }) {
  const [text, setText] = useState('');
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    const body = text.trim();
    if (!body || sending) return;
    setSending(true);
    try {
      await onSend(body);
      setText('');
    } catch (err) {
      console.error('Error sending message:', err);
      alert('Failed to send message. Please try again.');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="chat-composer">
      <textarea
        rows="2"
        placeholder="Type a message..."
        value={text}
        disabled={sending}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        }}
      />
      <button className="btn-primary chat-send-btn" onClick={handleSend} disabled={!text.trim() || sending}>
        {sending ? 'Sending...' : 'Send'}
      </button>
    </div>
  );
}
