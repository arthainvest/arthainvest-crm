import React, { useEffect, useRef, useState } from 'react';

// How long after the last keystroke before we tell the other side "stopped typing" - long
// enough to survive a brief pause mid-sentence, short enough that the indicator doesn't linger
// after someone has clearly walked away from the box.
const TYPING_STOP_DELAY_MS = 2000;

export default function MessageComposer({ onSend, onTyping }) {
  const [text, setText] = useState('');
  const [sending, setSending] = useState(false);
  const isTypingRef = useRef(false);
  const stopTimerRef = useRef(null);

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

  return (
    <div className="chat-composer">
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
  );
}
