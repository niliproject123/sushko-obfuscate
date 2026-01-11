import { useState } from 'react';
import type { ReplacementPoolsConfig } from '../../types';
import './PoolEditor.css';

interface PoolEditorProps {
  pools: ReplacementPoolsConfig;
  onUpdate: (poolName: keyof ReplacementPoolsConfig, values: string[]) => Promise<void>;
}

const POOL_LABELS: Record<keyof ReplacementPoolsConfig, string> = {
  name_hebrew_first: 'Hebrew First Names',
  name_hebrew_last: 'Hebrew Last Names',
  name_english_first: 'English First Names',
  name_english_last: 'English Last Names',
  city: 'Cities',
  street: 'Streets',
};

export function PoolEditor({ pools, onUpdate }: PoolEditorProps) {
  const [editingPool, setEditingPool] = useState<keyof ReplacementPoolsConfig | null>(null);
  const [editValue, setEditValue] = useState('');
  const [saving, setSaving] = useState(false);

  // Handle null/undefined pools safely
  const safePools = pools || {
    name_hebrew_first: [],
    name_hebrew_last: [],
    name_english_first: [],
    name_english_last: [],
    city: [],
    street: [],
  };

  const handleEdit = (poolName: keyof ReplacementPoolsConfig) => {
    setEditingPool(poolName);
    setEditValue(safePools[poolName]?.join('\n') || '');
  };

  const handleCancel = () => {
    setEditingPool(null);
    setEditValue('');
  };

  const handleSave = async () => {
    if (!editingPool) return;

    setSaving(true);
    try {
      const values = editValue
        .split('\n')
        .map((v) => v.trim())
        .filter((v) => v.length > 0);
      await onUpdate(editingPool, values);
      setEditingPool(null);
      setEditValue('');
    } catch (err) {
      // Error handled by parent
    } finally {
      setSaving(false);
    }
  };

  const poolNames = Object.keys(POOL_LABELS) as (keyof ReplacementPoolsConfig)[];

  return (
    <div className="pool-editor">
      <h3>Replacement Pools</h3>
      <p className="description">
        Lists of fake values used to replace detected PII
      </p>

      {editingPool && (
        <div className="pool-form">
          <h4>Edit {POOL_LABELS[editingPool]}</h4>
          <textarea
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            placeholder="One value per line..."
            rows={10}
          />
          <div className="form-actions">
            <button type="button" onClick={handleCancel} className="btn-cancel">
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSave}
              className="btn-save"
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </div>
      )}

      <div className="pool-list">
        {poolNames.map((poolName) => (
          <div key={poolName} className="pool-item">
            <div className="pool-info">
              <span className="pool-name">{POOL_LABELS[poolName]}</span>
              <span className="pool-count">{(safePools[poolName] || []).length} values</span>
            </div>
            <div className="pool-preview">
              {(safePools[poolName] || []).slice(0, 5).join(', ')}
              {(safePools[poolName] || []).length > 5 && '...'}
            </div>
            <button
              type="button"
              onClick={() => handleEdit(poolName)}
              className="btn-edit"
            >
              Edit
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
