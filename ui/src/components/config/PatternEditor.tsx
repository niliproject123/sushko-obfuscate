import { useState } from 'react';
import type { PIIPatternConfig } from '../../types';
import './PatternEditor.css';

interface PatternEditorProps {
  patterns: PIIPatternConfig[];
  onAdd: (pattern: PIIPatternConfig) => Promise<void>;
  onUpdate: (name: string, pattern: PIIPatternConfig) => Promise<void>;
  onDelete: (name: string) => Promise<void>;
}

const EMPTY_PATTERN: PIIPatternConfig = {
  name: '',
  pii_type: 'NAME',
  regex: '',
  capture_group: 0,
  enabled: true,
  validator: null,
};

const PII_TYPES = ['NAME', 'ID', 'PHONE', 'EMAIL', 'ADDRESS', 'OTHER'];

export function PatternEditor({
  patterns,
  onAdd,
  onUpdate,
  onDelete,
}: PatternEditorProps) {
  const [editingPattern, setEditingPattern] = useState<PIIPatternConfig | null>(null);
  const [isNew, setIsNew] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleEdit = (pattern: PIIPatternConfig) => {
    setEditingPattern({ ...pattern });
    setIsNew(false);
  };

  const handleNew = () => {
    setEditingPattern({ ...EMPTY_PATTERN });
    setIsNew(true);
  };

  const handleCancel = () => {
    setEditingPattern(null);
    setIsNew(false);
  };

  const handleSave = async () => {
    if (!editingPattern) return;

    setSaving(true);
    try {
      if (isNew) {
        await onAdd(editingPattern);
      } else {
        await onUpdate(editingPattern.name, editingPattern);
      }
      setEditingPattern(null);
      setIsNew(false);
    } catch (err) {
      // Error handled by parent
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (name: string) => {
    if (confirm(`למחוק את הדפוס "${name}"?`)) {
      await onDelete(name);
    }
  };

  const handleToggleEnabled = async (pattern: PIIPatternConfig) => {
    await onUpdate(pattern.name, { ...pattern, enabled: !pattern.enabled });
  };

  return (
    <div className="pattern-editor">
      <div className="pattern-header">
        <h3>דפוסי זיהוי</h3>
        <button type="button" onClick={handleNew} className="btn-add">
          + הוסף דפוס
        </button>
      </div>

      {editingPattern && (
        <div className="pattern-form">
          <h4>{isNew ? 'דפוס חדש' : 'עריכת דפוס'}</h4>
          <div className="form-grid">
            <div className="form-field">
              <label>שם</label>
              <input
                type="text"
                value={editingPattern.name}
                onChange={(e) =>
                  setEditingPattern({ ...editingPattern, name: e.target.value })
                }
                disabled={!isNew}
                placeholder="לדוגמה: israeli_id"
              />
            </div>
            <div className="form-field">
              <label>סוג מידע אישי</label>
              <select
                value={editingPattern.pii_type}
                onChange={(e) =>
                  setEditingPattern({ ...editingPattern, pii_type: e.target.value })
                }
              >
                {PII_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-field full-width">
              <label>ביטוי רגולרי (Regex)</label>
              <input
                type="text"
                value={editingPattern.regex}
                onChange={(e) =>
                  setEditingPattern({ ...editingPattern, regex: e.target.value })
                }
                placeholder="לדוגמה: \b\d{9}\b"
                className="mono"
              />
            </div>
            <div className="form-field">
              <label>קבוצת לכידה</label>
              <input
                type="number"
                value={editingPattern.capture_group}
                onChange={(e) =>
                  setEditingPattern({
                    ...editingPattern,
                    capture_group: parseInt(e.target.value) || 0,
                  })
                }
                min="0"
              />
            </div>
            <div className="form-field">
              <label>מאמת</label>
              <input
                type="text"
                value={editingPattern.validator || ''}
                onChange={(e) =>
                  setEditingPattern({
                    ...editingPattern,
                    validator: e.target.value || null,
                  })
                }
                placeholder="לדוגמה: israeli_id_checksum"
              />
            </div>
            <div className="form-field">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={editingPattern.enabled}
                  onChange={(e) =>
                    setEditingPattern({ ...editingPattern, enabled: e.target.checked })
                  }
                />
                פעיל
              </label>
            </div>
          </div>
          <div className="form-actions">
            <button type="button" onClick={handleCancel} className="btn-cancel">
              ביטול
            </button>
            <button
              type="button"
              onClick={handleSave}
              className="btn-save"
              disabled={saving || !editingPattern.name || !editingPattern.regex}
            >
              {saving ? 'שומר...' : 'שמור'}
            </button>
          </div>
        </div>
      )}

      <div className="pattern-list">
        {patterns.map((pattern) => (
          <div
            key={pattern.name}
            className={`pattern-item ${!pattern.enabled ? 'disabled' : ''}`}
          >
            <div className="pattern-info">
              <span className="pattern-name">{pattern.name}</span>
              <span className="pattern-type">{pattern.pii_type}</span>
              <code className="pattern-regex">{pattern.regex}</code>
            </div>
            <div className="pattern-actions">
              <button
                type="button"
                onClick={() => handleToggleEnabled(pattern)}
                className={`btn-toggle ${pattern.enabled ? 'on' : 'off'}`}
              >
                {pattern.enabled ? 'פעיל' : 'כבוי'}
              </button>
              <button
                type="button"
                onClick={() => handleEdit(pattern)}
                className="btn-edit"
              >
                ערוך
              </button>
              <button
                type="button"
                onClick={() => handleDelete(pattern.name)}
                className="btn-delete"
              >
                מחק
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
