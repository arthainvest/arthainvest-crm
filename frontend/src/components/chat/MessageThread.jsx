import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useChat } from '../../contexts/ChatContext';
import MessageBubble from './MessageBubble';
import MessageComposer from './MessageComposer';

const currentUserId = Number(localStorage.getItem('userId'));

function conversationTitle(convo) {
  if (convo.name) return convo.name;
  const others = convo.members.filter((m) => m.user_id !== currentUserId);
  return others.map((m) => m.full_name).join(', ') || 'You';
}

function typingLabel(conversation, typingUserIds) {
  const names = conversation.members
    .filter((m) => typingUserIds.includes(m.user_id))
    .map((m) => m.full_name);
  if (names.length === 0) return null;
  if (names.length === 1) return `${names[0]} is typing...`;
  if (names.length === 2) return `${names[0]} and ${names[1]} are typing...`;
  return `${names.length} people are typing...`;
}

export default function MessageThread({ conversation, onBack, initialLinkContext, onLinkContextConsumed }) {
  const {
    messagesByConversation, presenceMap, typingMap, sendMessage, sendTyping, markRead,
    editMessage, removeMessage, uploadAttachment,
  } = useChat();
  // Read the raw (possibly undefined) value for the effect dependency below - falling back to
  // a literal [] here would create a new array reference every render, re-triggering the
  // scroll effect on every render rather than only when the messages actually change.
  const messages = messagesByConversation[conversation.id];
  const messagesEndRef = useRef(null);
  const lastMarkedReadIdRef = useRef(0);
  const [replyTo, setReplyTo] = useState(null);
  // Phase 2B-i/2B-ii: "Discuss in Connect" (see LeadsList.jsx/Contacts.jsx) hands off a CRM
  // record via ChatPage's navigation state as { type: 'lead'|'contact', id, name }; this
  // component owns the actual composer-facing state from there, exactly mirroring how
  // `replyTo` above works - set once, attached to the next message sent, then cleared.
  // `initialLinkContext` only seeds the very first render of a freshly-selected conversation
  // (this component remounts on conversation switch via ChatPage's `key` prop). Kept as one
  // typed value rather than separate leadContext/contactContext state, since at most one is
  // ever active at a time and handleSend below just reads `.type` to know which id to send -
  // this is a UI-state-shape convenience only, not the DB/backend link model, which keeps
  // lead_id and contact_id fully independent columns.
  const [linkContext, setLinkContext] = useState(initialLinkContext || null);

  useEffect(() => {
    if (initialLinkContext) onLinkContextConsumed?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const messagesById = useMemo(() => {
    const map = {};
    (messages || []).forEach((m) => { map[m.id] = m; });
    return map;
  }, [messages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Mark read whenever the visible last message advances - guarded by a ref (not state) so
  // this never re-triggers itself via the unread_count update markRead causes elsewhere.
  useEffect(() => {
    if (!messages || messages.length === 0) return;
    const lastId = messages[messages.length - 1].id;
    if (lastId > lastMarkedReadIdRef.current) {
      lastMarkedReadIdRef.current = lastId;
      markRead(conversation.id, lastId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages, conversation.id]);

  const others = conversation.members.filter((m) => m.user_id !== currentUserId);
  const anyOnline = conversation.type === 'dm' && others.some((m) => presenceMap[m.user_id] ?? m.online);
  const typingUserIds = (typingMap[conversation.id] || []).filter((id) => id !== currentUserId);
  const typing = typingLabel(conversation, typingUserIds);

  const handleSend = async (body) => {
    const leadId = linkContext?.type === 'lead' ? linkContext.id : null;
    const contactId = linkContext?.type === 'contact' ? linkContext.id : null;
    await sendMessage(conversation.id, body, replyTo?.id ?? null, leadId, contactId);
    setReplyTo(null);
    setLinkContext(null);
  };
  const handleTyping = (isTyping) => sendTyping(conversation.id, isTyping);
  const handleAttach = (file) => uploadAttachment(conversation.id, file);
  const handleEdit = (messageId, body) => editMessage(messageId, conversation.id, body);
  const handleDelete = (messageId) => removeMessage(messageId, conversation.id);

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
          {(conversation.type === 'group' || conversation.type === 'channel') && (
            <span className="chat-thread-members">{conversation.members.length} members</span>
          )}
        </div>
      </div>

      <div className="chat-messages">
        {!messages || messages.length === 0 ? (
          <p className="no-data">No messages yet. Say hello.</p>
        ) : (
          messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              repliedToMessage={msg.reply_to_message_id ? messagesById[msg.reply_to_message_id] : null}
              onReply={setReplyTo}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {typing && <div className="chat-typing-indicator">{typing}</div>}

      <MessageComposer
        onSend={handleSend}
        onTyping={handleTyping}
        onAttach={handleAttach}
        replyTo={replyTo}
        onCancelReply={() => setReplyTo(null)}
        linkContext={linkContext}
        onCancelLinkContext={() => setLinkContext(null)}
      />
    </>
  );
}
