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
            <span className="status-main">מעבד את קבצי ה-PDF שלך...</span>
            <span className="status-detail">
              {completed} מתוך {total} הושלמו
              {errors > 0 && `, ${errors} שגיא${errors !== 1 ? 'ות' : 'ה'}`}
            </span>
          </div>
        </>
      ) : (
        <div className="status-complete">
          העיבוד הושלם: {completed} הצליחו
          {errors > 0 && `, ${errors} נכשלו`}
        </div>
      )}
    </div>
  );
}
