import { useState } from 'react';
import type { TextProcessingResult } from '../../types';
import './TextResultCard.css';

interface TextResultCardProps {
  result: TextProcessingResult;
}

export function TextResultCard({ result }: TextResultCardProps) {
  const [copiedMappings, setCopiedMappings] = useState(false);
  const [copiedText, setCopiedText] = useState(false);

  const handleCopyMappings = async () => {
    if (!result.response) return;

    const { response } = result;
    const mappings = response.mappings_used || {};
    const mappingEntries = Object.entries(mappings);

    // Format the mappings for clipboard
    let text = `סיכום שינויים:\n`;
    text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    text += `התאמות: ${response.total_matches}\n`;
    text += `החלפות ייחודיות: ${mappingEntries.length}\n`;

    if (mappingEntries.length > 0) {
      text += `\nהחלפות שבוצעו:\n`;
      text += `─────────────────────────────\n`;
      mappingEntries.forEach(([original, replacement]) => {
        text += `${original} → ${replacement}\n`;
      });
    }

    try {
      await navigator.clipboard.writeText(text);
      setCopiedMappings(true);
      setTimeout(() => setCopiedMappings(false), 2000);
    } catch (err) {
      console.error('Copy failed:', err);
    }
  };

  const handleCopyText = async () => {
    if (!result.response?.obfuscated_text) return;

    try {
      await navigator.clipboard.writeText(result.response.obfuscated_text);
      setCopiedText(true);
      setTimeout(() => setCopiedText(false), 2000);
    } catch (err) {
      console.error('Copy failed:', err);
    }
  };

  if (result.status === 'processing') {
    return (
      <div className="text-result-card processing">
        <div className="card-header">
          <span className="title">טקסט מודבק</span>
          <span className="status-badge processing">מעבד...</span>
        </div>
      </div>
    );
  }

  if (result.status === 'error') {
    return (
      <div className="text-result-card error">
        <div className="card-header">
          <span className="title">טקסט מודבק</span>
          <span className="status-badge error">שגיאה</span>
        </div>
        <div className="error-message">{result.error}</div>
      </div>
    );
  }

  if (!result.response) {
    return null;
  }

  const { response } = result;
  const mappings = response.mappings_used || {};
  const mappingEntries = Object.entries(mappings);

  return (
    <div className="text-result-card success">
      <div className="card-header">
        <div className="result-info">
          <span className="title">טקסט מודבק</span>
          <span className="stats">
            {response.total_matches} התאמ{response.total_matches !== 1 ? 'ות' : 'ה'} •{' '}
            {mappingEntries.length} החלפ{mappingEntries.length !== 1 ? 'ות' : 'ה'} ייחודי{mappingEntries.length !== 1 ? 'ות' : 'ת'}
          </span>
        </div>
        <div className="action-buttons">
          <button
            type="button"
            onClick={handleCopyMappings}
            className="copy-btn copy-mappings"
            title="העתק רשימת שינויים"
          >
            {copiedMappings ? '✓ הועתק' : 'העתק שינויים'}
          </button>
          <button
            type="button"
            onClick={handleCopyText}
            className="copy-btn copy-text"
            title="העתק טקסט מעובד"
          >
            {copiedText ? '✓ הועתק' : 'העתק טקסט'}
          </button>
        </div>
      </div>

      {response.warnings && response.warnings.length > 0 && (
        <div className="warnings-section">
          {response.warnings.map((warning, idx) => (
            <div key={idx} className="warning-message">
              ⚠️ {warning}
            </div>
          ))}
        </div>
      )}

      {mappingEntries.length > 0 && (
        <div className="mappings-section">
          <div className="section-title">שינויים שבוצעו</div>
          <div className="mappings-list">
            {mappingEntries.map(([original, replacement], idx) => (
              <span key={idx} className="match-tag">
                <span className="match-text">{original}</span>
                <span className="match-replacement">← {replacement}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {response.obfuscated_text && (
        <div className="obfuscated-text-section">
          <div className="section-title">טקסט מעובד</div>
          <div className="obfuscated-text" dir="rtl">
            {response.obfuscated_text}
          </div>
        </div>
      )}
    </div>
  );
}
