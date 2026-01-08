import React, { useState } from 'react';
import './ReplacementEditor.css';

interface ReplacementEditorProps {
  replacements: Record<string, string>;
  onChange: (replacements: Record<string, string>) => void;
  title?: string;
  description?: string;
}

export function ReplacementEditor({
  replacements,
  onChange,
  title = 'Custom Replacements',
  description = 'Define specific text to find and replace',
}: ReplacementEditorProps) {
  const [newPattern, setNewPattern] = useState('');
  const [newReplacement, setNewReplacement] = useState('');

  const entries = Object.entries(replacements);

  const handleAdd = () => {
    if (newPattern.trim()) {
      onChange({
        ...replacements,
        [newPattern.trim()]: newReplacement.trim(),
      });
      setNewPattern('');
      setNewReplacement('');
    }
  };

  const handleRemove = (pattern: string) => {
    const { [pattern]: _, ...rest } = replacements;
    onChange(rest);
  };

  const handleUpdate = (oldPattern: string, newValue: string) => {
    const updated = { ...replacements };
    updated[oldPattern] = newValue;
    onChange(updated);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAdd();
    }
  };

  return (
    <div className="replacement-editor">
      <h3>{title}</h3>
      {description && <p className="description">{description}</p>}

      <div className="replacement-list">
        {entries.map(([pattern, replacement]) => (
          <div key={pattern} className="replacement-row">
            <input
              type="text"
              value={pattern}
              disabled
              className="pattern-input"
              placeholder="Find..."
            />
            <span className="arrow">&rarr;</span>
            <input
              type="text"
              value={replacement}
              onChange={(e) => handleUpdate(pattern, e.target.value)}
              className="replacement-input"
              placeholder="Replace with..."
            />
            <button
              type="button"
              onClick={() => handleRemove(pattern)}
              className="remove-btn"
              title="Remove"
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
            placeholder="Find text..."
          />
          <span className="arrow">&rarr;</span>
          <input
            type="text"
            value={newReplacement}
            onChange={(e) => setNewReplacement(e.target.value)}
            onKeyDown={handleKeyDown}
            className="replacement-input"
            placeholder="Replace with..."
          />
          <button
            type="button"
            onClick={handleAdd}
            className="add-btn"
            disabled={!newPattern.trim()}
            title="Add"
          >
            +
          </button>
        </div>
      </div>
    </div>
  );
}
