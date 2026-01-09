import { FileResultCard } from './FileResultCard';
import type { FileProcessingResult } from '../../types';
import './ResultsContainer.css';

interface ResultsContainerProps {
  results: FileProcessingResult[];
}

export function ResultsContainer({ results }: ResultsContainerProps) {
  if (results.length === 0) {
    return null;
  }

  return (
    <div className="results-container">
      <h2>Results</h2>
      <div className="results-list">
        {results.map((result, index) => (
          <FileResultCard key={`${result.file.name}-${index}`} result={result} />
        ))}
      </div>
    </div>
  );
}
