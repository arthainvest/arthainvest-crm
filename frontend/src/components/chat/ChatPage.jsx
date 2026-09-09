import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { useChat } from '../../contexts/ChatContext';
import { searchChatMessages } from '../../services/api';
import ConversationList from './ConversationList';
import MessageThread from './MessageThread';
import NewConversationModal from './NewConversationModal';
import '../../styles/Chat.css';

const token = localStorage.getItem('token');

// Layout modeled on WhatsAppInbox.jsx's conversation-list-plus-thread structure, the closest
// existing precedent in this app - extended here with a live WebSocket connection (via
// ChatContext) instead of that page's plain request/response REST calls.
export default function ChatPage() {
  const { conversations, connected, refreshConversations, loadMessages } = useChat();
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [selectedId, setSelectedId] = useState(conversationId ? Number(conversationId) : null);
  const [showNewModal, setShowNewModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);
  // Phase 2B-i/2B-ii: "Discuss in Connect" (LeadsList.jsx, Contacts.jsx) navigates here with a
  // CRM record attached via router state rather than creating/opening a conversation itself -
  // the user still picks or starts the actual conversation through the existing flows below, so
  // this never risks creating duplicate conversations. `type` distinguishes which entity it is
  // (lead_id vs contact_id are independent columns - see the 2B-ii design notes); the two
  // pieces of navigation state are read here but never both exist at once in practice, since a
  // single row action can only ever start one of them. Handed to MessageThread once a
  // conversation is selected; cleared once MessageThread confirms it took ownership (see
  // onLinkContextConsumed).
  const initialLinkContext = location.state?.leadContext
    ? { type: 'lead', ...location.state.leadContext }
    : location.state?.contactContext
      ? { type: 'contact', ...location.state.contactContext }
      : null;
  const [pendingLinkContext, setPendingLinkContext] = useState(initialLinkContext);

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

  const handleSearch = async (e) => {
    e.preventDefault();
    const q = searchQuery.trim();
    if (!q) { setSearchResults(null); return; }
    setSearching(true);
    try {
      const results = await searchChatMessages(token, q);
      setSearchResults(results);
    } catch (err) {
      console.error('Error searching messages:', err);
    } finally {
      setSearching(false);
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults(null);
  };

  const handleSearchResultClick = (result) => {
    clearSearch();
    handleSelect(result.conversation_id);
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

          <form className="chat-search-form" onSubmit={handleSearch}>
            <input
              type="text"
              className="chat-search-input"
              placeholder="Search messages..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button type="button" className="chat-search-clear" onClick={clearSearch} title="Clear search">×</button>
            )}
          </form>

          {searchResults !== null ? (
            <div className="chat-search-results">
              {searching ? (
                <p className="no-data">Searching...</p>
              ) : searchResults.length === 0 ? (
                <p className="no-data">No messages found.</p>
              ) : (
                searchResults.map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    className="chat-search-result"
                    onClick={() => handleSearchResultClick(m)}
                  >
                    <span className="chat-search-result-sender">{m.sender_name}</span>
                    <span className="chat-search-result-body">{m.body}</span>
                  </button>
                ))
              )}
            </div>
          ) : (
            <ConversationList
              conversations={conversations}
              selectedId={selectedId}
              onSelect={handleSelect}
            />
          )}
        </div>

        <div className="chat-thread-pane">
          {!selectedConversation ? (
            <div className="chat-thread-empty">
              {pendingLinkContext ? (
                <p>Discussing <strong>{pendingLinkContext.name}</strong> - select a conversation, or start a new one.</p>
              ) : (
                <p>Select a conversation, or start a new one.</p>
              )}
            </div>
          ) : (
            <MessageThread
              key={selectedConversation.id}
              conversation={selectedConversation}
              initialLinkContext={pendingLinkContext}
              onLinkContextConsumed={() => setPendingLinkContext(null)}
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
