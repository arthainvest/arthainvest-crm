import React, { useState, useEffect, useRef, useCallback } from 'react';
import { getTags, getTagsForEntity, assignTag, unassignTag, createTag } from '../services/api';
import '../styles/EntityTagsFields.css';

export default function EntityTags({ token, entityType, entityId }) {
  const [allTags, setAllTags] = useState([]);
  const [assignedTags, setAssignedTags] = useState([]);
  const [showPicker, setShowPicker] = useState(false);
  const [newTagName, setNewTagName] = useState('');
  const [newTagColor, setNewTagColor] = useState('#667eea');
  const pickerRef = useRef(null);

  const fetchAssigned = useCallback(async () => {
    try {
      const data = await getTagsForEntity(token, entityType, entityId);
      setAssignedTags(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching tags for entity:', error);
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
    if (opening && allTags.length === 0) {
      try {
        const data = await getTags(token);
        setAllTags(Array.isArray(data) ? data : []);
      } catch (error) {
        console.error('Error fetching tags:', error);
      }
    }
  };

  const isAssigned = (tagId) => assignedTags.some((t) => t.id === tagId);

  const toggleTag = async (tag) => {
    try {
      if (isAssigned(tag.id)) {
        await unassignTag(token, entityType, entityId, tag.id);
      } else {
        await assignTag(token, entityType, entityId, tag.id);
      }
      fetchAssigned();
    } catch (error) {
      console.error('Error toggling tag:', error);
    }
  };

  const handleRemoveChip = async (tagId) => {
    try {
      await unassignTag(token, entityType, entityId, tagId);
      setAssignedTags((prev) => prev.filter((t) => t.id !== tagId));
    } catch (error) {
      console.error('Error removing tag:', error);
    }
  };

  const handleCreateTag = async (e) => {
    e.preventDefault();
    if (!newTagName.trim()) return;
    try {
      const tag = await createTag(token, { name: newTagName.trim(), color: newTagColor });
      setNewTagName('');
      setAllTags((prev) => [...prev, tag]);
      await assignTag(token, entityType, entityId, tag.id);
      fetchAssigned();
    } catch (error) {
      console.error('Error creating tag:', error);
      alert('Failed to create tag - a tag with this name may already exist.');
    }
  };

  return (
    <div className="entity-tags" ref={pickerRef}>
      <div className="entity-tags-chips">
        {assignedTags.map((tag) => (
          <span
            key={tag.id}
            className="entity-tag-chip"
            style={{ background: `${tag.color}22`, color: tag.color, borderColor: `${tag.color}55` }}
          >
            {tag.name}
            <button type="button" onClick={() => handleRemoveChip(tag.id)} title={`Remove ${tag.name}`}>×</button>
          </span>
        ))}
        <button type="button" className="entity-tag-add" onClick={openPicker}>+ Tag</button>

        {showPicker && (
          <div className="entity-tag-picker">
            {allTags.length === 0 ? (
              <p className="entity-picker-empty">No tags yet - create the first one below.</p>
            ) : allTags.map((tag) => (
              <label key={tag.id} className="entity-tag-option">
                <input type="checkbox" checked={isAssigned(tag.id)} onChange={() => toggleTag(tag)} />
                <span className="entity-tag-dot" style={{ background: tag.color }} />
                {tag.name}
              </label>
            ))}
            <form className="entity-tag-create" onSubmit={handleCreateTag}>
              <input type="color" value={newTagColor} onChange={(e) => setNewTagColor(e.target.value)} title="Tag color" />
              <input
                type="text"
                placeholder="New tag name"
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
              />
              <button type="submit" className="btn-secondary small">Add</button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
