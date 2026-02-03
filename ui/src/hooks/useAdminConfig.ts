import { useState, useEffect, useCallback, useMemo } from 'react';
import type { ServerConfig, PIIPatternConfig, ReplacementPoolsConfig } from '../types';
import * as configApi from '../services/configApi';
import { createAsyncAction } from './useAsyncAction';

interface UseAdminConfigReturn {
  config: ServerConfig | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  updatePatterns: (patterns: PIIPatternConfig[]) => Promise<void>;
  addPattern: (pattern: PIIPatternConfig) => Promise<void>;
  updatePattern: (name: string, pattern: PIIPatternConfig) => Promise<void>;
  deletePattern: (name: string) => Promise<void>;
  updatePool: (poolName: keyof ReplacementPoolsConfig, values: string[]) => Promise<void>;
  updatePlaceholders: (placeholders: Record<string, string>) => Promise<void>;
  updateOcr: (ocr: ServerConfig['ocr']) => Promise<void>;
  updateDefaultReplacements: (replacements: Record<string, string>) => Promise<void>;
  // Category management
  createCategory: (name: string, words?: string[]) => Promise<void>;
  updateCategory: (name: string, words: string[]) => Promise<void>;
  deleteCategory: (name: string) => Promise<void>;
  addWordToCategory: (category: string, word: string) => Promise<void>;
  removeWordFromCategory: (category: string, word: string) => Promise<void>;
  toggleCategory: (name: string) => Promise<void>;
}

export function useAdminConfig(): UseAdminConfigReturn {
  const [config, setConfig] = useState<ServerConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await configApi.getConfig();
      setConfig(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load config');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Helper to create actions that update config directly
  const withConfigUpdate = useCallback(
    <T>(apiCall: (arg: T) => Promise<ServerConfig>, errorMsg: string) =>
      createAsyncAction(setError, async (arg: T) => {
        const updated = await apiCall(arg);
        setConfig(updated);
      }, errorMsg),
    []
  );

  // Helper to create actions that refresh after completion
  const withRefresh = useCallback(
    <TArgs extends unknown[]>(
      apiCall: (...args: TArgs) => Promise<unknown>,
      errorMsg: string
    ) =>
      createAsyncAction(setError, async (...args: TArgs) => {
        await apiCall(...args);
        await refresh();
      }, errorMsg),
    [refresh]
  );

  // Memoize all actions to prevent unnecessary re-renders
  const actions = useMemo(() => ({
    updatePatterns: withConfigUpdate(
      (patterns: PIIPatternConfig[]) => configApi.updateConfig({ patterns }),
      'Failed to update patterns'
    ),
    addPattern: withRefresh(
      (pattern: PIIPatternConfig) => configApi.addPattern(pattern),
      'Failed to add pattern'
    ),
    updatePattern: withRefresh(
      (name: string, pattern: PIIPatternConfig) => configApi.updatePattern(name, pattern),
      'Failed to update pattern'
    ),
    deletePattern: withRefresh(
      (name: string) => configApi.deletePattern(name),
      'Failed to delete pattern'
    ),
    updatePool: withRefresh(
      (poolName: keyof ReplacementPoolsConfig, values: string[]) => configApi.updatePool(poolName, values),
      'Failed to update pool'
    ),
    updatePlaceholders: withConfigUpdate(
      (placeholders: Record<string, string>) => configApi.updateConfig({ placeholders }),
      'Failed to update placeholders'
    ),
    updateOcr: withConfigUpdate(
      (ocr: ServerConfig['ocr']) => configApi.updateConfig({ ocr }),
      'Failed to update OCR settings'
    ),
    updateDefaultReplacements: withConfigUpdate(
      (replacements: Record<string, string>) => configApi.updateConfig({ default_replacements: replacements }),
      'Failed to update default replacements'
    ),
    createCategory: withRefresh(
      (name: string, words: string[] = []) => configApi.createCategory(name, words),
      'Failed to create category'
    ),
    updateCategory: withRefresh(
      (name: string, words: string[]) => configApi.updateCategory(name, words),
      'Failed to update category'
    ),
    deleteCategory: withRefresh(
      (name: string) => configApi.deleteCategory(name),
      'Failed to delete category'
    ),
    addWordToCategory: withRefresh(
      (category: string, word: string) => configApi.addWordToCategory(category, word),
      'Failed to add word'
    ),
    removeWordFromCategory: withRefresh(
      (category: string, word: string) => configApi.removeWordFromCategory(category, word),
      'Failed to remove word'
    ),
    toggleCategory: withRefresh(
      (name: string) => configApi.toggleCategory(name),
      'Failed to toggle category'
    ),
  }), [withConfigUpdate, withRefresh]);

  return {
    config,
    loading,
    error,
    refresh,
    ...actions,
  };
}
