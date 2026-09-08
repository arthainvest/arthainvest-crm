import React from 'react';
import { useChat } from '../../contexts/ChatContext';

const currentUserId = Number(localStorage.getItem('userId'));

function conversationTitle(convo) {
  if (convo.name) return convo.name;
  const others = convo.members.filter((m) => m.user_id !== currentUserId);
  return others.map((m) => m.full_name).join(', ') || 'You';
}

function formatTimestamp(ts) {
  if (!ts) return '';
  const iso = ts.includes('T') ? ts : ts.replace(' ', 'T');
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  const sameDay = d.toDateString() === new Date().toDateString();
  return sameDay
    ? d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : d.toLocaleDateString([], { day: '2-digit', month: 'short' });
}

export default function ConversationList({ conversations, selectedId, onSelect }) {
  const { presenceMap } = useChat();

  if (conversations.length === 0) {
    return <p className="no-data chat-list-empty">No conversations yet. Start one above.</p>;
  }

  return (
    <div className="chat-conversation-list">
      {conversations.map((convo) => {
        const title = conversationTitle(convo);
        const others = convo.members.filter((m) => m.user_id !== currentUserId);
        // Only DMs show an online ring on the avatar - a group/channel's "anyone online" isn't
        // a meaningful single-dot signal the way it is for exactly one other person.
        const anyOnline = convo.type === 'dm' && others.some((m) => presenceMap[m.user_id] ?? m.online);
        const unread = convo.unread_count || 0;

        return (
          <button
            key={convo.id}
            className={`chat-conversation-item ${selectedId === convo.id ? 'active' : ''} ${unread > 0 ? 'unread' : ''}`}
            onClick={() => onSelect(convo.id)}
          >
            <div className={`chat-avatar ${anyOnline ? 'online' : ''}`}>
              {convo.type === 'channel' ? '#' : title.charAt(0).toUpperCase()}
            </div>
            <div className="chat-conversation-details">
              <div className="chat-conversation-top-row">
                <span className="chat-conversation-name">{title}</span>
                <span className="chat-conversation-time">{formatTimestamp(convo.last_message_at)}</span>
              </div>
              <div className="chat-conversation-preview">
                {convo.last_message_body || 'No messages yet'}
              </div>
              {convo.type === 'group' && <span className="chat-group-badge">Group</span>}
              {convo.type === 'channel' && <span className="chat-group-badge">Channel</span>}
            </div>
            {unread > 0 && <span className="chat-unread-badge">{unread > 99 ? '99+' : unread}</span>}
          </button>
        );
      })}
    </div>
  );
}
