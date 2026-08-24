import React, { useState, useRef, useEffect } from 'react';
import { chatWithAI } from '../services/api';
import '../styles/ChatbotWidget.css';

export default function ChatbotWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const token = localStorage.getItem('token');
  const historyEndRef = useRef(null);

  useEffect(() => {
    if (open) historyEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, open]);

  const handleSend = async (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || sending) return;

    const nextMessages = [...messages, { role: 'user', content: text }];
    setMessages(nextMessages);
    setInput('');
    setSending(true);

    try {
      const history = nextMessages.slice(0, -1).map((m) => ({ role: m.role, content: m.content }));
      const result = await chatWithAI(token, text, history);
      if (result.configured && result.reply) {
        setMessages((prev) => [...prev, { role: 'assistant', content: result.reply }]);
      } else {
        setMessages((prev) => [...prev, { role: 'assistant', content: result.message, isNotice: true }]);
      }
    } catch (error) {
      console.error('Error chatting with AI:', error);
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Something went wrong - please try again.', isNotice: true }]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="chatbot-widget">
      {open && (
        <div className="chatbot-panel">
          <div className="chatbot-panel-header">
            <span>🤖 Ask AI</span>
            <button type="button" className="chatbot-close" onClick={() => setOpen(false)}>×</button>
          </div>

          <div className="chatbot-messages">
            {messages.length === 0 && (
              <p className="chatbot-empty">
                Ask me anything about your leads, deals, contacts, or calls -
                e.g. "How many leads are from Mumbai?" or "What's Amit Patel's loan amount?"
              </p>
            )}
            {messages.map((m, idx) => (
              <div key={idx} className={`chatbot-bubble ${m.role}${m.isNotice ? ' notice' : ''}`}>
                {m.content}
              </div>
            ))}
            {sending && <div className="chatbot-bubble assistant thinking">Thinking…</div>}
            <div ref={historyEndRef} />
          </div>

          <form className="chatbot-input-row" onSubmit={handleSend}>
            <input
              type="text"
              placeholder="Ask about your CRM data..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={sending}
            />
            <button type="submit" disabled={sending || !input.trim()}>➤</button>
          </form>
        </div>
      )}

      <button
        type="button"
        className="chatbot-toggle"
        onClick={() => setOpen((prev) => !prev)}
        title="Ask AI about your CRM"
      >
        {open ? '×' : '🤖'}
      </button>
    </div>
  );
}
