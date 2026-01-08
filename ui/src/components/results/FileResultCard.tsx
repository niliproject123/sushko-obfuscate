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

  return (
    <div className="file-result-card success">
      <div className="card-header">
        <div className="file-info">
          <span className="file-name">{result.file.name}</span>
          <span className="stats">
            {response.page_count} page{response.page_count !== 1 ? 's' : ''} •{' '}
            {response.total_matches} match{response.total_matches !== 1 ? 'es' : ''}
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

      {response.pages.length > 0 && (
        <div className="pages-summary">
          {response.pages.map((page) => (
            <div key={page.page_number} className="page-item">
              <span className="page-number">Page {page.page_number}</span>
              <span className="match-count">
                {page.matches_found} match{page.matches_found !== 1 ? 'es' : ''}
              </span>
              {page.matches.length > 0 && (
                <div className="matches">
                  {page.matches.map((match, idx) => (
                    <span key={idx} className="match-tag">
                      <span className="match-type">{match.type}</span>
                      <span className="match-text">{match.text}</span>
                      {match.replacement && (
                        <span className="match-replacement">→ {match.replacement}</span>
                      )}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
