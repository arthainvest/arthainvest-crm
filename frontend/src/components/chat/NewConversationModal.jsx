import React, { useEffect, useState } from 'react';
import { getChatUsers } from '../../services/api';
import { useChat } from '../../contexts/ChatContext';

const currentUserId = Number(localStorage.getItem('userId'));

export default function NewConversationModal({ onClose, onCreated }) {
  const { startConversation } = useChat();
  const [users, setUsers] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [groupName, setGroupName] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('token');
    getChatUsers(token)
      .then((data) => setUsers((Array.isArray(data) ? data : []).filter((u) => u.id !== currentUserId)))
      .catch((err) => {
        console.error('Error fetching chat users:', err);
        setError('Failed to load teammates. Please try again.');
      });
  }, []);

  const toggleUser = (userId) => {
    setSelectedIds((prev) => (prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]));
  };

  const isGroup = selectedIds.length > 1;

  const handleCreate = async () => {
    if (selectedIds.length === 0 || creating) return;
    setCreating(true);
    setError('');
    try {
      const conv = await startConversation(isGroup ? 'group' : 'dm', selectedIds, isGroup ? (groupName.trim() || null) : null);
      onCreated(conv);
    } catch (err) {
      console.error('Error creating conversation:', err);
      setError(err.response?.data?.detail || 'Failed to create conversation. Please try again.');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="chat-modal-overlay" onClick={onClose}>
      <div className="chat-modal" onClick={(e) => e.stopPropagation()}>
        <h2>New conversation</h2>
        {error && <div className="chat-modal-error">{error}</div>}

        <p className="chat-modal-hint">Select one teammate for a direct message, or several for a group.</p>
        <div className="chat-user-picker">
          {users.map((u) => (
            <label key={u.id} className="chat-user-option">
              <input
                type="checkbox"
                checked={selectedIds.includes(u.id)}
                onChange={() => toggleUser(u.id)}
              />
              {u.full_name}
            </label>
          ))}
          {users.length === 0 && <p className="no-data">No other teammates found.</p>}
        </div>

        {isGroup && (
          <input
            type="text"
            className="chat-group-name-input"
            placeholder="Group name (optional)"
            value={groupName}
            onChange={(e) => setGroupName(e.target.value)}
          />
        )}

        <div className="chat-modal-actions">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={handleCreate} disabled={selectedIds.length === 0 || creating}>
            {creating ? 'Creating...' : isGroup ? 'Create Group' : 'Start Chat'}
          </button>
        </div>
      </div>
    </div>
  );
}
