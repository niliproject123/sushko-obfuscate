import type { FileProcessingResult } from '../../types';
import './ProcessingStatus.css';

interface ProcessingStatusProps {
  results: FileProcessingResult[];
  processing: boolean;
}

export function ProcessingStatus({ results, processing }: ProcessingStatusProps) {
  if (!processing && results.length === 0) {
    return null;
  }

  const completed = results.filter((r) => r.status === 'completed').length;
  const errors = results.filter((r) => r.status === 'error').length;
  const total = results.length;

  return (
    <div className="processing-status">
      {processing ? (
        <>
          <div className="spinner"></div>
          <div className="status-text">
            <span className="status-main">Processing your PDFs...</span>
            <span className="status-detail">
              {completed} of {total} completed
              {errors > 0 && `, ${errors} error${errors !== 1 ? 's' : ''}`}
            </span>
          </div>
        </>
      ) : (
        <div className="status-complete">
          Processing complete: {completed} succeeded
          {errors > 0 && `, ${errors} failed`}
        </div>
      )}
    </div>
  );
}
