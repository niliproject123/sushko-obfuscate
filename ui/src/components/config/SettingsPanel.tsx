import { useState } from 'react';
import type { ServerConfig } from '../../types';
import './SettingsPanel.css';

interface SettingsPanelProps {
  ocr: ServerConfig['ocr'];
  placeholders: Record<string, string>;
  onUpdateOcr: (ocr: ServerConfig['ocr']) => Promise<void>;
  onUpdatePlaceholders: (placeholders: Record<string, string>) => Promise<void>;
}

export function SettingsPanel({
  ocr,
  placeholders,
  onUpdateOcr,
  onUpdatePlaceholders,
}: SettingsPanelProps) {
  const [localOcr, setLocalOcr] = useState(ocr);
  const [localPlaceholders, setLocalPlaceholders] = useState(placeholders);
  const [saving, setSaving] = useState<string | null>(null);

  const handleSaveOcr = async () => {
    setSaving('ocr');
    try {
      await onUpdateOcr(localOcr);
    } finally {
      setSaving(null);
    }
  };

  const handleSavePlaceholders = async () => {
    setSaving('placeholders');
    try {
      await onUpdatePlaceholders(localPlaceholders);
    } finally {
      setSaving(null);
    }
  };

  return (
    <div className="settings-panel">
      <div className="settings-section">
        <h3>OCR Settings</h3>
        <div className="settings-grid">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={localOcr.enabled}
              onChange={(e) =>
                setLocalOcr({ ...localOcr, enabled: e.target.checked })
              }
            />
            Enable OCR
          </label>
          <div className="setting-field">
            <label>Languages (comma-separated)</label>
            <input
              type="text"
              value={localOcr.languages.join(', ')}
              onChange={(e) =>
                setLocalOcr({
                  ...localOcr,
                  languages: e.target.value.split(',').map((l) => l.trim()),
                })
              }
            />
          </div>
          <div className="setting-field">
            <label>DPI</label>
            <input
              type="number"
              value={localOcr.dpi}
              onChange={(e) =>
                setLocalOcr({ ...localOcr, dpi: parseInt(e.target.value) || 300 })
              }
              min="72"
              max="600"
            />
          </div>
          <div className="setting-field">
            <label>Min Text Threshold</label>
            <input
              type="number"
              value={localOcr.min_text_threshold}
              onChange={(e) =>
                setLocalOcr({
                  ...localOcr,
                  min_text_threshold: parseInt(e.target.value) || 50,
                })
              }
              min="0"
            />
          </div>
        </div>
        <button
          type="button"
          onClick={handleSaveOcr}
          className="btn-save"
          disabled={saving === 'ocr'}
        >
          {saving === 'ocr' ? 'Saving...' : 'Save OCR Settings'}
        </button>
      </div>

      <div className="settings-section">
        <h3>Placeholders</h3>
        <p className="description">
          Default text used when replacing detected PII
        </p>
        <div className="placeholder-list">
          {Object.entries(localPlaceholders).map(([key, value]) => (
            <div key={key} className="placeholder-row">
              <span className="placeholder-key">{key}</span>
              <input
                type="text"
                value={value}
                onChange={(e) =>
                  setLocalPlaceholders({ ...localPlaceholders, [key]: e.target.value })
                }
              />
            </div>
          ))}
        </div>
        <button
          type="button"
          onClick={handleSavePlaceholders}
          className="btn-save"
          disabled={saving === 'placeholders'}
        >
          {saving === 'placeholders' ? 'Saving...' : 'Save Placeholders'}
        </button>
      </div>
    </div>
  );
}
