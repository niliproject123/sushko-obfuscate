import { useState, useEffect, useCallback } from 'react';
import type { ServerConfig, PIIPatternConfig, ReplacementPoolsConfig } from '../types';
import * as configApi from '../services/configApi';

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

  const updatePatterns = useCallback(async (patterns: PIIPatternConfig[]) => {
    setError(null);
    try {
      const updated = await configApi.updateConfig({ patterns });
      setConfig(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update patterns');
      throw err;
    }
  }, []);

  const addPattern = useCallback(async (pattern: PIIPatternConfig) => {
    setError(null);
    try {
      await configApi.addPattern(pattern);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add pattern');
      throw err;
    }
  }, [refresh]);

  const updatePattern = useCallback(async (name: string, pattern: PIIPatternConfig) => {
    setError(null);
    try {
      await configApi.updatePattern(name, pattern);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update pattern');
      throw err;
    }
  }, [refresh]);

  const deletePattern = useCallback(async (name: string) => {
    setError(null);
    try {
      await configApi.deletePattern(name);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete pattern');
      throw err;
    }
  }, [refresh]);

  const updatePool = useCallback(async (poolName: keyof ReplacementPoolsConfig, values: string[]) => {
    setError(null);
    try {
      await configApi.updatePool(poolName, values);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update pool');
      throw err;
    }
  }, [refresh]);

  const updatePlaceholders = useCallback(async (placeholders: Record<string, string>) => {
    setError(null);
    try {
      const updated = await configApi.updateConfig({ placeholders });
      setConfig(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update placeholders');
      throw err;
    }
  }, []);

  const updateOcr = useCallback(async (ocr: ServerConfig['ocr']) => {
    setError(null);
    try {
      const updated = await configApi.updateConfig({ ocr });
      setConfig(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update OCR settings');
      throw err;
    }
  }, []);

  const updateDefaultReplacements = useCallback(async (replacements: Record<string, string>) => {
    setError(null);
    try {
      const updated = await configApi.updateConfig({ default_replacements: replacements });
      setConfig(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update default replacements');
      throw err;
    }
  }, []);

  return {
    config,
    loading,
    error,
    refresh,
    updatePatterns,
    addPattern,
    updatePattern,
    deletePattern,
    updatePool,
    updatePlaceholders,
    updateOcr,
    updateDefaultReplacements,
  };
}
