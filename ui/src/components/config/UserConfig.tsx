import { useState } from 'react';
import { ReplacementEditor } from './ReplacementEditor';
import type { UserConfig as UserConfigType, PIIPatternConfig } from '../../types';
import './UserConfig.css';

interface UserConfigProps {
  config: UserConfigType;
  onReplacementsChange: (replacements: Record<string, string>) => void;
  onToggleDetector: (name: string, disabled: boolean) => void;
  onForceOcrChange: (forceOcr: boolean) => void;
  availablePatterns?: PIIPatternConfig[];
}

export function UserConfig({
  config,
  onReplacementsChange,
  onToggleDetector,
  onForceOcrChange,
  availablePatterns = [],
}: UserConfigProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  return (
    <div className="user-config">
      <ReplacementEditor
        replacements={config.replacements}
        onChange={onReplacementsChange}
        title="My Replacements"
        description="Add text patterns to find and their replacements. These take priority over server settings."
      />

      <div className="advanced-section">
        <button
          type="button"
          className="advanced-toggle"
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          {showAdvanced ? '▼' : '▶'} Advanced Options
        </button>

        {showAdvanced && (
          <div className="advanced-content">
            <div className="option-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={config.force_ocr}
                  onChange={(e) => onForceOcrChange(e.target.checked)}
                />
                Force OCR Processing
              </label>
              <p className="option-hint">
                Use OCR even if the PDF has a text layer
              </p>
            </div>

            {availablePatterns.length > 0 && (
              <div className="option-group">
                <h4>Disable Detectors</h4>
                <p className="option-hint">
                  Uncheck patterns you don't want to detect
                </p>
                <div className="detector-list">
                  {availablePatterns.map((pattern) => (
                    <label key={pattern.name} className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={!config.disabled_detectors.includes(pattern.name)}
                        onChange={(e) =>
                          onToggleDetector(pattern.name, !e.target.checked)
                        }
                      />
                      {pattern.name} ({pattern.pii_type})
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
