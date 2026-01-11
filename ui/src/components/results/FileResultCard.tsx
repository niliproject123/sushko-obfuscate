import { useState } from 'react';
import type { FileProcessingResult } from '../../types';
import { downloadFile } from '../../services/extractApi';
import './FileResultCard.css';

interface FileResultCardProps {
  result: FileProcessingResult;
}

export function FileResultCard({ result }: FileResultCardProps) {
  const [downloading, setDownloading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleDownload = async () => {
    if (!result.response?.file_id) return;

    setDownloading(true);
    try {
      await downloadFile(result.response.file_id, result.file.name);
    } catch (err) {
      console.error('Download failed:', err);
    } finally {
      setDownloading(false);
    }
  };

  const handleCopy = async () => {
    if (!result.response) return;

    const { response } = result;
    const mappings = response.mappings_used || {};
    const mappingEntries = Object.entries(mappings);

    // Format the text for clipboard
    let text = `קובץ: ${result.file.name}\n`;
    text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    text += `עמודים: ${response.page_count}\n`;
    text += `התאמות: ${response.total_matches}\n`;
    text += `החלפות ייחודיות: ${mappingEntries.length}\n`;

    if (mappingEntries.length > 0) {
      text += `\nהחלפות שבוצעו:\n`;
      text += `─────────────────────────────\n`;
      mappingEntries.forEach(([original, replacement]) => {
        text += `${original} → ${replacement}\n`;
      });
    }

    if (response.warnings && response.warnings.length > 0) {
      text += `\nאזהרות:\n`;
      response.warnings.forEach(warning => {
        text += `⚠️ ${warning}\n`;
      });
    }

    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Copy failed:', err);
    }
  };

  if (result.status === 'processing') {
    return (
      <div className="file-result-card processing">
        <div className="card-header">
          <span className="file-name">{result.file.name}</span>
          <span className="status-badge processing">מעבד...</span>
        </div>
      </div>
    );
  }

  if (result.status === 'error') {
    return (
      <div className="file-result-card error">
        <div className="card-header">
          <span className="file-name">{result.file.name}</span>
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

  // Get unique mappings from mappings_used (consolidated per PDF)
  const mappings = response.mappings_used || {};
  const mappingEntries = Object.entries(mappings);

  return (
    <div className="file-result-card success">
      <div className="card-header">
        <div className="file-info">
          <span className="file-name">{result.file.name}</span>
          <span className="stats">
            {response.page_count} עמוד{response.page_count !== 1 ? 'ים' : ''} •{' '}
            {response.total_matches} התאמ{response.total_matches !== 1 ? 'ות' : 'ה'} •{' '}
            {mappingEntries.length} החלפ{mappingEntries.length !== 1 ? 'ות' : 'ה'} ייחודי{mappingEntries.length !== 1 ? 'ות' : 'ת'}
          </span>
        </div>
        <div className="action-buttons">
          <button
            type="button"
            onClick={handleCopy}
            className="copy-btn"
            title="העתק תוצאות"
          >
            {copied ? '✓ הועתק' : 'העתק'}
          </button>
          <button
            type="button"
            onClick={handleDownload}
            className="download-btn"
            disabled={downloading}
          >
            {downloading ? 'מוריד...' : 'הורד'}
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
        <div className="pages-summary">
          <div className="page-item">
            <span className="page-number">שינויים</span>
            <div className="matches">
              {mappingEntries.map(([original, replacement], idx) => (
                <span key={idx} className="match-tag">
                  <span className="match-text">{original}</span>
                  <span className="match-replacement">← {replacement}</span>
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
