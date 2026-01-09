import { ExtractResponse } from '../types'
import './Results.css'

interface ResultsProps {
  results: ExtractResponse
}

function Results({ results }: ResultsProps) {
  return (
    <div className="results">
      {results.warnings && results.warnings.length > 0 && (
        <div className="warnings">
          {results.warnings.map((warning, i) => (
            <div key={i} className="warning">
              ⚠️ {warning}
            </div>
          ))}
        </div>
      )}

      <div className="summary">
        <strong>Processing Complete</strong>
        <br />
        Pages: {results.page_count}
        <br />
        Total PII matches found: {results.total_matches}
      </div>

      <div className="page-results">
        {results.pages.map((page) => (
          <div key={page.page_number} className="page-result">
            <strong>Page {page.page_number}</strong>: {page.matches_found} matches found
            <div className="matches">
              {page.matches.length > 0 ? (
                page.matches.map((match, i) => (
                  <span key={i} className="match-tag">
                    {match.type}: "{match.text}"
                  </span>
                ))
              ) : (
                <em>No PII detected</em>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Results
