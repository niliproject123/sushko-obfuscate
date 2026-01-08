import { PatternEditor } from './PatternEditor';
import { PoolEditor } from './PoolEditor';
import { SettingsPanel } from './SettingsPanel';
import { ReplacementEditor } from './ReplacementEditor';
import type { ServerConfig, PIIPatternConfig, ReplacementPoolsConfig } from '../../types';
import './AdminConfig.css';

interface AdminConfigProps {
  config: ServerConfig | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => Promise<void>;
  onAddPattern: (pattern: PIIPatternConfig) => Promise<void>;
  onUpdatePattern: (name: string, pattern: PIIPatternConfig) => Promise<void>;
  onDeletePattern: (name: string) => Promise<void>;
  onUpdatePool: (poolName: keyof ReplacementPoolsConfig, values: string[]) => Promise<void>;
  onUpdateOcr: (ocr: ServerConfig['ocr']) => Promise<void>;
  onUpdatePlaceholders: (placeholders: Record<string, string>) => Promise<void>;
  onUpdateDefaultReplacements: (replacements: Record<string, string>) => Promise<void>;
}

export function AdminConfig({
  config,
  loading,
  error,
  onRefresh,
  onAddPattern,
  onUpdatePattern,
  onDeletePattern,
  onUpdatePool,
  onUpdateOcr,
  onUpdatePlaceholders,
  onUpdateDefaultReplacements,
}: AdminConfigProps) {
  if (loading && !config) {
    return (
      <div className="admin-config">
        <div className="loading">Loading configuration...</div>
      </div>
    );
  }

  if (error && !config) {
    return (
      <div className="admin-config">
        <div className="error">
          <p>Failed to load configuration: {error}</p>
          <button type="button" onClick={onRefresh}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!config) {
    return null;
  }

  return (
    <div className="admin-config">
      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      <div className="config-section">
        <ReplacementEditor
          replacements={config.default_replacements}
          onChange={onUpdateDefaultReplacements}
          title="Default Replacements"
          description="Global replacements applied to all requests (can be overridden by users)"
        />
      </div>

      <div className="config-section">
        <PatternEditor
          patterns={config.patterns}
          onAdd={onAddPattern}
          onUpdate={onUpdatePattern}
          onDelete={onDeletePattern}
        />
      </div>

      <div className="config-section">
        <PoolEditor
          pools={config.replacement_pools}
          onUpdate={onUpdatePool}
        />
      </div>

      <div className="config-section">
        <SettingsPanel
          ocr={config.ocr}
          placeholders={config.placeholders}
          onUpdateOcr={onUpdateOcr}
          onUpdatePlaceholders={onUpdatePlaceholders}
        />
      </div>
    </div>
  );
}
