import React, { useState, useEffect, useRef, useCallback } from 'react';
import { getGroups, getGroupsForEntity, assignGroup, unassignGroup, createGroup } from '../services/api';
import '../styles/EntityTagsFields.css';

export default function EntityGroups({ token, entityType, entityId }) {
  const [allGroups, setAllGroups] = useState([]);
  const [assignedGroups, setAssignedGroups] = useState([]);
  const [showPicker, setShowPicker] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const pickerRef = useRef(null);

  const fetchAssigned = useCallback(async () => {
    try {
      const data = await getGroupsForEntity(token, entityType, entityId);
      setAssignedGroups(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching groups for entity:', error);
    }
  }, [token, entityType, entityId]);

  useEffect(() => {
    fetchAssigned();
  }, [fetchAssigned]);

  useEffect(() => {
    if (!showPicker) return;
    const handleOutsideClick = (e) => {
      if (pickerRef.current && !pickerRef.current.contains(e.target)) setShowPicker(false);
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, [showPicker]);

  const openPicker = async () => {
    const opening = !showPicker;
    setShowPicker(opening);
    if (opening && allGroups.length === 0) {
      try {
        const data = await getGroups(token);
        setAllGroups(Array.isArray(data) ? data : []);
      } catch (error) {
        console.error('Error fetching groups:', error);
      }
    }
  };

  const isAssigned = (groupId) => assignedGroups.some((g) => g.id === groupId);

  const toggleGroup = async (group) => {
    try {
      if (isAssigned(group.id)) {
        await unassignGroup(token, entityType, entityId, group.id);
      } else {
        await assignGroup(token, entityType, entityId, group.id);
      }
      fetchAssigned();
    } catch (error) {
      console.error('Error toggling group:', error);
    }
  };

  const handleRemoveChip = async (groupId) => {
    try {
      await unassignGroup(token, entityType, entityId, groupId);
      setAssignedGroups((prev) => prev.filter((g) => g.id !== groupId));
    } catch (error) {
      console.error('Error removing group:', error);
    }
  };

  const handleCreateGroup = async (e) => {
    e.preventDefault();
    if (!newGroupName.trim()) return;
    try {
      const group = await createGroup(token, { name: newGroupName.trim() });
      setNewGroupName('');
      setAllGroups((prev) => [...prev, group]);
      await assignGroup(token, entityType, entityId, group.id);
      fetchAssigned();
    } catch (error) {
      console.error('Error creating group:', error);
      alert('Failed to create group - a group with this name may already exist.');
    }
  };

  return (
    <div className="entity-tags" ref={pickerRef}>
      <div className="entity-tags-chips">
        {assignedGroups.map((group) => (
          <span key={group.id} className="entity-group-chip">
            👥 {group.name}
            <button type="button" onClick={() => handleRemoveChip(group.id)} title={`Remove from ${group.name}`}>×</button>
          </span>
        ))}
        <button type="button" className="entity-tag-add" onClick={openPicker}>+ Group</button>

        {showPicker && (
          <div className="entity-tag-picker">
            {allGroups.length === 0 ? (
              <p className="entity-picker-empty">No groups yet - create the first one below.</p>
            ) : allGroups.map((group) => (
              <label key={group.id} className="entity-tag-option">
                <input type="checkbox" checked={isAssigned(group.id)} onChange={() => toggleGroup(group)} />
                {group.name}
              </label>
            ))}
            <form className="entity-tag-create" onSubmit={handleCreateGroup}>
              <input
                type="text"
                placeholder="New group name"
                value={newGroupName}
                onChange={(e) => setNewGroupName(e.target.value)}
              />
              <button type="submit" className="btn-secondary small">Add</button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
