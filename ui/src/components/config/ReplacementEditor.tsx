import React, { useState } from 'react';
import './ReplacementEditor.css';

interface ReplacementEditorProps {
  replacements: Record<string, string>;
  onChange: (replacements: Record<string, string>) => void;
  title?: string;
  description?: string;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
}

export function ReplacementEditor({
  replacements,
  onChange,
  title = 'החלפות מותאמות אישית',
  description = 'הגדר טקסט לחיפוש והחלפה',
  collapsible = false,
  defaultCollapsed = false,
}: ReplacementEditorProps) {
  const [newPattern, setNewPattern] = useState('');
  const [newReplacement, setNewReplacement] = useState('');
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);

  // Handle null/undefined replacements safely
  const safeReplacements = replacements || {};
  const entries = Object.entries(safeReplacements);

  const handleAdd = () => {
    if (newPattern.trim()) {
      onChange({
        ...safeReplacements,
        [newPattern.trim()]: newReplacement.trim(),
      });
      setNewPattern('');
      setNewReplacement('');
    }
  };

  const handleRemove = (pattern: string) => {
    const { [pattern]: _, ...rest } = safeReplacements;
    onChange(rest);
  };

  const handleUpdate = (oldPattern: string, newValue: string) => {
    const updated = { ...safeReplacements };
    updated[oldPattern] = newValue;
    onChange(updated);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAdd();
    }
  };

  const content = (
    <div className="replacement-list">
      {entries.map(([pattern, replacement]) => (
        <div key={pattern} className="replacement-row">
          <input
            type="text"
            value={pattern}
            disabled
            className="pattern-input"
            placeholder="חפש..."
          />
          <span className="arrow">&rarr;</span>
          <input
            type="text"
            value={replacement}
            onChange={(e) => handleUpdate(pattern, e.target.value)}
            className="replacement-input"
            placeholder="החלף ב..."
          />
          <button
            type="button"
            onClick={() => handleRemove(pattern)}
            className="remove-btn"
            title="הסר"
          >
            &times;
          </button>
        </div>
      ))}

      <div className="replacement-row new-row">
        <input
          type="text"
          value={newPattern}
          onChange={(e) => setNewPattern(e.target.value)}
          onKeyDown={handleKeyDown}
          className="pattern-input"
          placeholder="טקסט לחיפוש..."
        />
        <span className="arrow">&rarr;</span>
        <input
          type="text"
          value={newReplacement}
          onChange={(e) => setNewReplacement(e.target.value)}
          onKeyDown={handleKeyDown}
          className="replacement-input"
          placeholder="החלף ב..."
        />
        <button
          type="button"
          onClick={handleAdd}
          className="add-btn"
          disabled={!newPattern.trim()}
          title="הוסף"
        >
          +
        </button>
      </div>
    </div>
  );

  if (collapsible) {
    return (
      <div className="replacement-editor collapsible">
        <button
          type="button"
          className="collapsible-header"
          onClick={() => setIsCollapsed(!isCollapsed)}
        >
          <span className="collapse-icon">{isCollapsed ? '▶' : '▼'}</span>
          <h3>{title}</h3>
          {entries.length > 0 && (
            <span className="count-badge">{entries.length}</span>
          )}
        </button>
        {description && !isCollapsed && <p className="description">{description}</p>}
        {!isCollapsed && content}
      </div>
    );
  }

  return (
    <div className="replacement-editor">
      <h3>{title}</h3>
      {description && <p className="description">{description}</p>}
      {content}
    </div>
  );
}
