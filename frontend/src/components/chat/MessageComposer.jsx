import React, { useEffect, useRef, useState } from 'react';

// How long after the last keystroke before we tell the other side "stopped typing" - long
// enough to survive a brief pause mid-sentence, short enough that the indicator doesn't linger
// after someone has clearly walked away from the box.
const TYPING_STOP_DELAY_MS = 2000;

export default function MessageComposer({ onSend, onTyping, onAttach, replyTo, onCancelReply, leadContext, onCancelLeadContext }) {
  const [text, setText] = useState('');
  const [sending, setSending] = useState(false);
  const [attaching, setAttaching] = useState(false);
  const isTypingRef = useRef(false);
  const stopTimerRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => () => {
    clearTimeout(stopTimerRef.current);
    if (isTypingRef.current) onTyping?.(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleChange = (e) => {
    setText(e.target.value);
    if (!isTypingRef.current) {
      isTypingRef.current = true;
      onTyping?.(true);
    }
    clearTimeout(stopTimerRef.current);
    stopTimerRef.current = setTimeout(() => {
      isTypingRef.current = false;
      onTyping?.(false);
    }, TYPING_STOP_DELAY_MS);
  };

  const stopTypingNow = () => {
    clearTimeout(stopTimerRef.current);
    if (isTypingRef.current) {
      isTypingRef.current = false;
      onTyping?.(false);
    }
  };

  const handleSend = async () => {
    const body = text.trim();
    if (!body || sending) return;
    setSending(true);
    stopTypingNow();
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

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file || attaching) return;
    setAttaching(true);
    try {
      await onAttach(file);
    } catch (err) {
      console.error('Error uploading attachment:', err);
      const detail = err?.response?.data?.detail;
      alert(detail || 'Failed to upload attachment. Please try again.');
    } finally {
      setAttaching(false);
    }
  };

  return (
    <div className="chat-composer-wrapper">
      {replyTo && (
        <div className="chat-reply-banner">
          <div className="chat-reply-banner-text">
            <span className="chat-reply-banner-label">Replying to {replyTo.sender_name}</span>
            <span className="chat-reply-banner-body">{(replyTo.body || '').slice(0, 100)}</span>
          </div>
          <button type="button" className="chat-reply-banner-close" onClick={onCancelReply} title="Cancel reply">×</button>
        </div>
      )}
      {leadContext && (
        <div className="chat-lead-banner">
          <span className="chat-lead-banner-label">Discussing: {leadContext.name}</span>
          <button type="button" className="chat-lead-banner-close" onClick={onCancelLeadContext} title="Remove lead context">×</button>
        </div>
      )}
      <div className="chat-composer">
        <input
          ref={fileInputRef}
          type="file"
          className="chat-file-input"
          onChange={handleFileChange}
          disabled={attaching}
        />
        <button
          type="button"
          className="chat-attach-btn"
          onClick={() => fileInputRef.current?.click()}
          disabled={attaching}
          title="Attach a file"
        >
          {attaching ? '...' : '📎'}
        </button>
        <textarea
          rows="2"
          placeholder="Type a message..."
          value={text}
          disabled={sending}
          onChange={handleChange}
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
    </div>
  );
}
