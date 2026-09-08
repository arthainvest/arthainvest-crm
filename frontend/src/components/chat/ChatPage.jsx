import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useChat } from '../../contexts/ChatContext';
import ConversationList from './ConversationList';
import MessageThread from './MessageThread';
import NewConversationModal from './NewConversationModal';
import '../../styles/Chat.css';

// Layout modeled on WhatsAppInbox.jsx's conversation-list-plus-thread structure, the closest
// existing precedent in this app - extended here with a live WebSocket connection (via
// ChatContext) instead of that page's plain request/response REST calls.
export default function ChatPage() {
  const { conversations, connected, refreshConversations, loadMessages } = useChat();
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const [selectedId, setSelectedId] = useState(conversationId ? Number(conversationId) : null);
  const [showNewModal, setShowNewModal] = useState(false);

  useEffect(() => {
    refreshConversations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Deep-linking support (e.g. a future "start chat about this record" CRM entry point
  // navigating straight to /connect/:conversationId).
  useEffect(() => {
    if (selectedId != null) loadMessages(selectedId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId]);

  const handleSelect = (id) => {
    setSelectedId(id);
    navigate(`/connect/${id}`, { replace: true });
  };

  const handleCreated = (conv) => {
    setShowNewModal(false);
    handleSelect(conv.id);
  };

  const selectedConversation = conversations.find((c) => c.id === selectedId) || null;

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>ArthaInvest Connect</h1>
        <span className={`chat-connection-badge ${connected ? 'online' : 'offline'}`}>
          {connected ? 'Live' : 'Reconnecting...'}
        </span>
      </div>

      <div className={`chat-layout ${selectedId ? 'has-selected' : ''}`}>
        <div className="chat-list-pane">
          <button className="btn-primary chat-new-btn" onClick={() => setShowNewModal(true)}>
            + New conversation
          </button>
          <ConversationList
            conversations={conversations}
            selectedId={selectedId}
            onSelect={handleSelect}
          />
        </div>

        <div className="chat-thread-pane">
          {!selectedConversation ? (
            <div className="chat-thread-empty">
              <p>Select a conversation, or start a new one.</p>
            </div>
          ) : (
            <MessageThread
              conversation={selectedConversation}
              onBack={() => {
                setSelectedId(null);
                navigate('/connect', { replace: true });
              }}
            />
          )}
        </div>
      </div>

      {showNewModal && (
        <NewConversationModal onClose={() => setShowNewModal(false)} onCreated={handleCreated} />
      )}
    </div>
  );
}
