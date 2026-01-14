import React from 'react';
import './TextInput.css';

interface TextInputProps {
  text: string;
  onTextChange: (text: string) => void;
  onClear: () => void;
  disabled?: boolean;
}

export function TextInput({ text, onTextChange, onClear, disabled = false }: TextInputProps) {
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onTextChange(e.target.value);
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    // Handle paste event - the onChange will handle the actual update
    e.currentTarget.focus();
  };

  return (
    <div className="text-input">
      <div className="textarea-container">
        <textarea
          className={`text-area ${disabled ? 'disabled' : ''}`}
          value={text}
          onChange={handleChange}
          onPaste={handlePaste}
          placeholder="הדבק טקסט כאן לעיבוד..."
          disabled={disabled}
          dir="rtl"
        />
      </div>

      {text.length > 0 && (
        <div className="text-info">
          <span>{text.length} תווים</span>
          <button type="button" onClick={onClear} className="clear-btn" disabled={disabled}>
            נקה
          </button>
        </div>
      )}
    </div>
  );
}
