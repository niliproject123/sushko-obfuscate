import { useState } from 'react';
import type { FileProcessingResult } from '../../types';
import { downloadFile } from '../../services/extractApi';
import './FileResultCard.css';

interface FileResultCardProps {
  result: FileProcessingResult;
}

export function FileResultCard({ result }: FileResultCardProps) {
  const [downloading, setDownloading] = useState(false);

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

  if (result.status === 'processing') {
    return (
      <div className="file-result-card processing">
        <div className="card-header">
          <span className="file-name">{result.file.name}</span>
          <span className="status-badge processing">Processing...</span>
        </div>
      </div>
    );
  }

  if (result.status === 'error') {
    return (
      <div className="file-result-card error">
        <div className="card-header">
          <span className="file-name">{result.file.name}</span>
          <span className="status-badge error">Error</span>
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
            {response.page_count} page{response.page_count !== 1 ? 's' : ''} •{' '}
            {response.total_matches} match{response.total_matches !== 1 ? 'es' : ''} •{' '}
            {mappingEntries.length} unique replacement{mappingEntries.length !== 1 ? 's' : ''}
          </span>
        </div>
        <button
          type="button"
          onClick={handleDownload}
          className="download-btn"
          disabled={downloading}
        >
          {downloading ? 'Downloading...' : 'Download'}
        </button>
      </div>

      {mappingEntries.length > 0 && (
        <div className="pages-summary">
          <div className="page-item">
            <span className="page-number">Changes</span>
            <div className="matches">
              {mappingEntries.map(([original, replacement], idx) => (
                <span key={idx} className="match-tag">
                  <span className="match-text">{original}</span>
                  <span className="match-replacement">→ {replacement}</span>
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
