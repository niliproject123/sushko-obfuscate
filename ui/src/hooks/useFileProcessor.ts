import { useState, useCallback } from 'react';
import type { FileProcessingResult, UserConfig } from '../types';
import { extractPdf } from '../services/extractApi';

interface UseFileProcessorReturn {
  files: File[];
  results: FileProcessingResult[];
  processing: boolean;
  addFiles: (newFiles: FileList | File[]) => void;
  clearFiles: () => void;
  processAll: (userConfig: UserConfig) => Promise<void>;
}

export function useFileProcessor(): UseFileProcessorReturn {
  const [files, setFiles] = useState<File[]>([]);
  const [results, setResults] = useState<FileProcessingResult[]>([]);
  const [processing, setProcessing] = useState(false);

  const addFiles = useCallback((newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles).filter(
      (f) => f.type === 'application/pdf'
    );
    setFiles((prev) => [...prev, ...fileArray]);
    // Clear previous results when new files are added
    setResults([]);
  }, []);

  const clearFiles = useCallback(() => {
    setFiles([]);
    setResults([]);
  }, []);

  const processAll = useCallback(
    async (userConfig: UserConfig) => {
      if (files.length === 0) return;

      setProcessing(true);

      // Initialize all results as pending
      const initialResults: FileProcessingResult[] = files.map((file) => ({
        file,
        status: 'processing',
      }));
      setResults(initialResults);

      // Process all files in parallel
      const promises = files.map(async (file, index) => {
        try {
          const response = await extractPdf(file, {
            user_replacements: userConfig.replacements,
            disabled_detectors: userConfig.disabled_detectors,
            force_ocr: userConfig.force_ocr,
          });

          setResults((prev) => {
            const updated = [...prev];
            updated[index] = {
              file,
              response,
              status: 'completed',
            };
            return updated;
          });
        } catch (err) {
          setResults((prev) => {
            const updated = [...prev];
            updated[index] = {
              file,
              error: err instanceof Error ? err.message : 'Processing failed',
              status: 'error',
            };
            return updated;
          });
        }
      });

      await Promise.all(promises);
      setProcessing(false);
    },
    [files]
  );

  return {
    files,
    results,
    processing,
    addFiles,
    clearFiles,
    processAll,
  };
}
