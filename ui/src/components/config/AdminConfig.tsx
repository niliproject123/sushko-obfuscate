import { PatternEditor } from './PatternEditor';
import { PoolEditor } from './PoolEditor';
import { SettingsPanel } from './SettingsPanel';
import { ReplacementEditor } from './ReplacementEditor';
import { CategoryEditor } from './CategoryEditor';
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
  // Category management
  onCreateCategory: (name: string, words?: string[]) => Promise<void>;
  onDeleteCategory: (name: string) => Promise<void>;
  onAddWordToCategory: (category: string, word: string) => Promise<void>;
  onRemoveWordFromCategory: (category: string, word: string) => Promise<void>;
  onToggleCategory: (name: string) => Promise<void>;
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
  onCreateCategory,
  onDeleteCategory,
  onAddWordToCategory,
  onRemoveWordFromCategory,
  onToggleCategory,
}: AdminConfigProps) {
  if (loading && !config) {
    return (
      <div className="admin-config">
        <div className="loading">טוען תצורה...</div>
      </div>
    );
  }

  if (error && !config) {
    return (
      <div className="admin-config">
        <div className="error">
          <p>נכשל בטעינת התצורה: {error}</p>
          <button type="button" onClick={onRefresh}>
            נסה שוב
          </button>
        </div>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="admin-config">
        <div className="loading">לא נמצאה תצורה. ודא שהשרת פועל.</div>
      </div>
    );
  }

  return (
    <div className="admin-config">
      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      <div className="config-section">
        <CategoryEditor
          categories={config.categories || {}}
          disabledCategories={config.disabled_categories || []}
          onCreateCategory={onCreateCategory}
          onDeleteCategory={onDeleteCategory}
          onAddWord={onAddWordToCategory}
          onRemoveWord={onRemoveWordFromCategory}
          onToggleCategory={onToggleCategory}
        />
      </div>

      <div className="config-section">
        <ReplacementEditor
          replacements={config.default_replacements}
          onChange={onUpdateDefaultReplacements}
          title="החלפות ברירת מחדל"
          description="החלפות גלובליות המופעלות על כל הבקשות (ניתן לדרוס על ידי משתמשים)"
          collapsible={true}
          defaultCollapsed={true}
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
