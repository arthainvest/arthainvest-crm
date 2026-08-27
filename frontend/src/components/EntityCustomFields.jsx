import React, { useState, useEffect, useCallback } from 'react';
import { getCustomFieldValuesForEntity, createCustomField, setCustomFieldValue } from '../services/api';
import '../styles/EntityTagsFields.css';

const INPUT_TYPE = { number: 'number', date: 'date', text: 'text' };

export default function EntityCustomFields({ token, entityType, entityId }) {
  const [fields, setFields] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [draftValue, setDraftValue] = useState('');
  const [showAddField, setShowAddField] = useState(false);
  const [newFieldName, setNewFieldName] = useState('');
  const [newFieldType, setNewFieldType] = useState('text');

  const fetchFields = useCallback(async () => {
    try {
      const data = await getCustomFieldValuesForEntity(token, entityType, entityId);
      setFields(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching custom fields:', error);
    }
  }, [token, entityType, entityId]);

  useEffect(() => {
    fetchFields();
  }, [fetchFields]);

  const startEdit = (field) => {
    setEditingId(field.id);
    setDraftValue(field.value || '');
  };

  const saveValue = async (field) => {
    try {
      await setCustomFieldValue(token, {
        entity_type: entityType, entity_id: entityId, custom_field_id: field.id, value: draftValue
      });
      setFields((prev) => prev.map((f) => (f.id === field.id ? { ...f, value: draftValue } : f)));
    } catch (error) {
      console.error('Error saving custom field value:', error);
      alert('Failed to save value. Please try again.');
    } finally {
      setEditingId(null);
    }
  };

  const handleAddField = async (e) => {
    e.preventDefault();
    if (!newFieldName.trim()) return;
    try {
      await createCustomField(token, { name: newFieldName.trim(), field_type: newFieldType });
      setNewFieldName('');
      setNewFieldType('text');
      setShowAddField(false);
      fetchFields();
    } catch (error) {
      console.error('Error creating custom field:', error);
      alert('Failed to create field - a field with this name may already exist.');
    }
  };

  return (
    <div className="entity-fields">
      {fields.map((field) => (
        <div key={field.id} className="entity-field-row">
          <span className="entity-field-name">{field.name}</span>
          {editingId === field.id ? (
            <input
              className="entity-field-input"
              type={INPUT_TYPE[field.field_type] || 'text'}
              value={draftValue}
              autoFocus
              onChange={(e) => setDraftValue(e.target.value)}
              onBlur={() => saveValue(field)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') saveValue(field);
                if (e.key === 'Escape') setEditingId(null);
              }}
            />
          ) : (
            <button type="button" className="entity-field-value" onClick={() => startEdit(field)}>
              {field.value || <span className="entity-field-placeholder">Set value</span>}
            </button>
          )}
        </div>
      ))}

      {showAddField ? (
        <div className="entity-field-create-wrap">
          <form className="entity-field-create" onSubmit={handleAddField}>
            <input
              type="text"
              placeholder="Field name (e.g. SIP Amount)"
              value={newFieldName}
              onChange={(e) => setNewFieldName(e.target.value)}
              autoFocus
            />
            <select value={newFieldType} onChange={(e) => setNewFieldType(e.target.value)}>
              <option value="text">Text</option>
              <option value="number">Number</option>
              <option value="date">Date</option>
            </select>
            <button type="submit" className="btn-secondary small">Add</button>
            <button type="button" className="btn-secondary small" onClick={() => setShowAddField(false)}>Cancel</button>
          </form>
          <p className="entity-field-hint">This creates a field available on every contact/lead - only its value here is specific to this one.</p>
        </div>
      ) : (
        <button type="button" className="entity-field-add" onClick={() => setShowAddField(true)}>+ Custom Field</button>
      )}
    </div>
  );
}
