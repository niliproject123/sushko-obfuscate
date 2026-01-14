import { useState, useCallback } from 'react';
import type { TextProcessingResult, UserConfig } from '../types';
import { extractPlainText } from '../services/extractApi';

interface UseTextProcessorReturn {
  text: string;
  result: TextProcessingResult | null;
  processing: boolean;
  setText: (text: string) => void;
  clearText: () => void;
  processText: (userConfig: UserConfig) => Promise<void>;
}

export function useTextProcessor(): UseTextProcessorReturn {
  const [text, setTextState] = useState('');
  const [result, setResult] = useState<TextProcessingResult | null>(null);
  const [processing, setProcessing] = useState(false);

  const setText = useCallback((newText: string) => {
    setTextState(newText);
    // Clear previous result when text changes
    setResult(null);
  }, []);

  const clearText = useCallback(() => {
    setTextState('');
    setResult(null);
  }, []);

  const processText = useCallback(
    async (userConfig: UserConfig) => {
      if (text.trim().length === 0) return;

      setProcessing(true);

      // Initialize result as processing
      setResult({
        text,
        status: 'processing',
      });

      try {
        const response = await extractPlainText(text, {
          user_replacements: userConfig.replacements,
          disabled_detectors: userConfig.disabled_detectors,
          force_ocr: userConfig.force_ocr,
        });

        setResult({
          text,
          response,
          status: 'completed',
        });
      } catch (err) {
        setResult({
          text,
          error: err instanceof Error ? err.message : 'Processing failed',
          status: 'error',
        });
      } finally {
        setProcessing(false);
      }
    },
    [text]
  );

  return {
    text,
    result,
    processing,
    setText,
    clearText,
    processText,
  };
}
