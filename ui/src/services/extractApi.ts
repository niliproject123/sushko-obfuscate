// Extraction API endpoints

import { apiPost } from './api';
import type { ExtractResponse, PlainTextResponse } from '../types';

export interface ExtractRequestConfig {
  user_replacements?: Record<string, string>;
  disabled_detectors?: string[];
  force_ocr?: boolean;
}

export async function extractPdf(
  file: File,
  config?: ExtractRequestConfig
): Promise<ExtractResponse> {
  const formData = new FormData();
  formData.append('file', file);

  if (config) {
    formData.append('config', JSON.stringify(config));
  }

  return apiPost<ExtractResponse>('/extract', formData);
}

export async function extractPlainText(
  text: string,
  config?: ExtractRequestConfig
): Promise<PlainTextResponse> {
  return apiPost<PlainTextResponse>('/extract/plain', {
    text,
    config: config || {},
  });
}

export function getDownloadUrl(fileId: string): string {
  return `/api/download/${fileId}`;
}

export async function downloadFile(fileId: string, originalFileName: string): Promise<void> {
  const url = getDownloadUrl(fileId);
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error('Download failed');
  }

  const blob = await response.blob();
  const downloadUrl = URL.createObjectURL(blob);

  // Create filename: originalname_anonim.pdf
  const baseName = originalFileName.replace(/\.pdf$/i, '');
  const downloadFileName = `${baseName}_anonim.pdf`;

  const link = document.createElement('a');
  link.href = downloadUrl;
  link.download = downloadFileName;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  URL.revokeObjectURL(downloadUrl);
}
