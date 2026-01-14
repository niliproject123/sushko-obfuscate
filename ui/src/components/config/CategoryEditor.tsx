import { useState } from 'react';
import './CategoryEditor.css';

interface CategoryEditorProps {
  categories: Record<string, string[]>;
  disabledCategories?: string[];
  onCreateCategory: (name: string, words?: string[]) => Promise<void>;
  onDeleteCategory: (name: string) => Promise<void>;
  onAddWord: (category: string, word: string) => Promise<void>;
  onRemoveWord: (category: string, word: string) => Promise<void>;
  onToggleCategory?: (name: string) => Promise<void>;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
}

export function CategoryEditor({
  categories,
  disabledCategories = [],
  onCreateCategory,
  onDeleteCategory,
  onAddWord,
  onRemoveWord,
  onToggleCategory,
  collapsible = true,
  defaultCollapsed = true,
}: CategoryEditorProps) {
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newWords, setNewWords] = useState<Record<string, string>>({});
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);

  const handleCreateCategory = async () => {
    if (!newCategoryName.trim()) return;
    try {
      await onCreateCategory(newCategoryName.trim());
      setNewCategoryName('');
    } catch {
      // Error handled by parent
    }
  };

  const handleDeleteCategory = async (name: string) => {
    if (window.confirm(`למחוק את הקטגוריה "${name}"?`)) {
      await onDeleteCategory(name);
    }
  };

  const handleAddWord = async (category: string) => {
    const word = newWords[category]?.trim();
    if (!word) return;
    try {
      await onAddWord(category, word);
      setNewWords((prev) => ({ ...prev, [category]: '' }));
    } catch {
      // Error handled by parent
    }
  };

  const toggleCategory = (name: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  const categoryEntries = Object.entries(categories);
  const totalWords = categoryEntries.reduce((sum, [, words]) => sum + words.length, 0);

  const content = (
    <>
      {/* Add new category */}
      <div className="add-category-form">
        <input
          type="text"
          value={newCategoryName}
          onChange={(e) => setNewCategoryName(e.target.value)}
          placeholder="שם קטגוריה חדשה..."
          onKeyDown={(e) => e.key === 'Enter' && handleCreateCategory()}
        />
        <button
          type="button"
          onClick={handleCreateCategory}
          disabled={!newCategoryName.trim()}
          className="btn-add"
        >
          הוסף קטגוריה
        </button>
      </div>

      {/* Categories list */}
      <div className="categories-list">
        {categoryEntries.length === 0 ? (
          <div className="empty-state">אין קטגוריות מוגדרות</div>
        ) : (
          categoryEntries.map(([name, words]) => {
            const isExpanded = expandedCategories.has(name);
            const isEnabled = !disabledCategories.includes(name);
            return (
              <div key={name} className={`category-item ${!isEnabled ? 'disabled' : ''}`}>
                <div className="category-header" onClick={() => toggleCategory(name)}>
                  <span className="expand-icon">{isExpanded ? '▼' : '◀'}</span>
                  <span className="category-name">{name}</span>
                  <span className="word-count">{words.length} מילים</span>
                  {onToggleCategory && (
                    <button
                      type="button"
                      className={`btn-toggle ${isEnabled ? 'on' : 'off'}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        onToggleCategory(name);
                      }}
                    >
                      {isEnabled ? 'פעיל' : 'כבוי'}
                    </button>
                  )}
                  <button
                    type="button"
                    className="btn-delete-category"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteCategory(name);
                    }}
                  >
                    מחק
                  </button>
                </div>

                {isExpanded && (
                  <div className="category-content">
                    {/* Add word form */}
                    <div className="add-word-form">
                      <input
                        type="text"
                        value={newWords[name] || ''}
                        onChange={(e) =>
                          setNewWords((prev) => ({ ...prev, [name]: e.target.value }))
                        }
                        placeholder="הוסף מילה..."
                        onKeyDown={(e) => e.key === 'Enter' && handleAddWord(name)}
                      />
                      <button
                        type="button"
                        onClick={() => handleAddWord(name)}
                        disabled={!newWords[name]?.trim()}
                        className="btn-add-word"
                      >
                        +
                      </button>
                    </div>

                    {/* Words list */}
                    <div className="words-list">
                      {words.length === 0 ? (
                        <div className="empty-words">אין מילים בקטגוריה</div>
                      ) : (
                        words.map((word) => (
                          <span key={word} className="word-tag">
                            {word}
                            <button
                              type="button"
                              className="btn-remove-word"
                              onClick={() => onRemoveWord(name, word)}
                              title="הסר מילה"
                            >
                              ×
                            </button>
                          </span>
                        ))
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </>
  );

  if (collapsible) {
    return (
      <div className="category-editor collapsible">
        <button
          type="button"
          className="collapsible-header"
          onClick={() => setIsCollapsed(!isCollapsed)}
        >
          <span className="collapse-icon">{isCollapsed ? '▶' : '▼'}</span>
          <h3>קטגוריות לזיהוי (יחידות צבאיות)</h3>
          <span className="count-badge">
            {categoryEntries.length} קטגוריות, {totalWords} מילים
          </span>
        </button>
        {!isCollapsed && (
          <p className="section-description">
            הגדר קטגוריות ומילים לזיהוי אוטומטי. כל מילה בקטגוריה תזוהה ותוחלף.
          </p>
        )}
        {!isCollapsed && content}
      </div>
    );
  }

  return (
    <div className="category-editor">
      <div className="section-header">
        <h3>קטגוריות לזיהוי (יחידות צבאיות)</h3>
        <p className="section-description">
          הגדר קטגוריות ומילים לזיהוי אוטומטי. כל מילה בקטגוריה תזוהה ותוחלף.
        </p>
      </div>
      {content}
    </div>
  );
}
