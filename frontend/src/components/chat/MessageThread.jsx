import React, { useEffect, useRef } from 'react';
import { useChat } from '../../contexts/ChatContext';
import MessageBubble from './MessageBubble';
import MessageComposer from './MessageComposer';

const currentUserId = Number(localStorage.getItem('userId'));

function conversationTitle(convo) {
  if (convo.name) return convo.name;
  const others = convo.members.filter((m) => m.user_id !== currentUserId);
  return others.map((m) => m.full_name).join(', ') || 'You';
}

export default function MessageThread({ conversation, onBack }) {
  const { messagesByConversation, presenceMap, sendMessage } = useChat();
  // Read the raw (possibly undefined) value for the effect dependency below - falling back to
  // a literal [] here would create a new array reference every render, re-triggering the
  // scroll effect on every render rather than only when the messages actually change.
  const messages = messagesByConversation[conversation.id];
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const others = conversation.members.filter((m) => m.user_id !== currentUserId);
  const anyOnline = others.some((m) => presenceMap[m.user_id] ?? m.online);

  const handleSend = (body) => sendMessage(conversation.id, body);

  return (
    <>
      <div className="chat-thread-header">
        <button type="button" className="chat-back-btn" onClick={onBack} title="Back to conversation list">
          &larr;
        </button>
        <div className="chat-thread-heading">
          <h2>{conversationTitle(conversation)}</h2>
          {conversation.type === 'dm' && (
            <span className={`chat-presence-label ${anyOnline ? 'online' : ''}`}>
              {anyOnline ? 'Online' : 'Offline'}
            </span>
          )}
          {conversation.type === 'group' && (
            <span className="chat-thread-members">{conversation.members.length} members</span>
          )}
        </div>
      </div>

      <div className="chat-messages">
        {!messages || messages.length === 0 ? (
          <p className="no-data">No messages yet. Say hello.</p>
        ) : (
          messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
        )}
        <div ref={messagesEndRef} />
      </div>

      <MessageComposer onSend={handleSend} />
    </>
  );
}
