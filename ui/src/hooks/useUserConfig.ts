import { useCallback } from 'react';
import { useLocalStorage } from './useLocalStorage';
import type { UserConfig } from '../types';
import { DEFAULT_USER_CONFIG } from '../types';

const STORAGE_KEY = 'pii-extractor-user-config';

export function useUserConfig() {
  const [config, setConfig] = useLocalStorage<UserConfig>(
    STORAGE_KEY,
    DEFAULT_USER_CONFIG
  );

  const setReplacement = useCallback(
    (pattern: string, replacement: string) => {
      setConfig((prev) => ({
        ...prev,
        replacements: {
          ...prev.replacements,
          [pattern]: replacement,
        },
      }));
    },
    [setConfig]
  );

  const removeReplacement = useCallback(
    (pattern: string) => {
      setConfig((prev) => {
        const { [pattern]: _, ...rest } = prev.replacements;
        return {
          ...prev,
          replacements: rest,
        };
      });
    },
    [setConfig]
  );

  const setReplacements = useCallback(
    (replacements: Record<string, string>) => {
      setConfig((prev) => ({
        ...prev,
        replacements,
      }));
    },
    [setConfig]
  );

  const toggleDetector = useCallback(
    (detectorName: string, disabled: boolean) => {
      setConfig((prev) => {
        const disabledSet = new Set(prev.disabled_detectors);
        if (disabled) {
          disabledSet.add(detectorName);
        } else {
          disabledSet.delete(detectorName);
        }
        return {
          ...prev,
          disabled_detectors: Array.from(disabledSet),
        };
      });
    },
    [setConfig]
  );

  const setForceOcr = useCallback(
    (forceOcr: boolean) => {
      setConfig((prev) => ({
        ...prev,
        force_ocr: forceOcr,
      }));
    },
    [setConfig]
  );

  const resetConfig = useCallback(() => {
    setConfig(DEFAULT_USER_CONFIG);
  }, [setConfig]);

  return {
    config,
    setReplacement,
    removeReplacement,
    setReplacements,
    toggleDetector,
    setForceOcr,
    resetConfig,
  };
}
