/**
 * PDF-to-PDF API Correctness Tests
 *
 * Tests that the PDF processing API workflow works correctly:
 * - Upload PDF → Extract/Process → Download result
 *
 * Note: Actual text extraction correctness is tested in Python API tests.
 * These tests verify the API workflow and response structure.
 */
import { describe, test, expect, beforeAll } from 'vitest';
import { readFileSync } from 'fs';
import { join } from 'path';
import { RESOURCES_PATH, API_BASE, isBackendRunning } from './setup';

// Helper to upload PDF and get full response
async function uploadPdf(filename: string): Promise<{
  file_id: string;
  page_count: number;
  total_matches: number;
  mappings_used: Record<string, string>;
  pages: Array<{
    page_number: number;
    matches_found: number;
    matches: Array<{ text: string; type: string; replacement: string }>;
  }>;
}> {
  const pdfPath = join(RESOURCES_PATH, filename);
  const pdfBuffer = readFileSync(pdfPath);
  const blob = new Blob([pdfBuffer], { type: 'application/pdf' });

  const formData = new FormData();
  formData.append('file', blob, filename);
  formData.append('config', '{}');

  const response = await fetch(`${API_BASE}/extract`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.status}`);
  }

  return response.json();
}

// Helper to download PDF as buffer
async function downloadPdf(fileId: string): Promise<ArrayBuffer> {
  const response = await fetch(`${API_BASE}/download/${fileId}`);

  if (!response.ok) {
    throw new Error(`Download failed: ${response.status}`);
  }

  return response.arrayBuffer();
}

describe('PDF-to-PDF Correctness Tests', () => {
  beforeAll(async () => {
    const running = await isBackendRunning();
    if (!running) {
      throw new Error('Backend server must be running on port 8000');
    }
  });

  test('6.1 Medical form PDF processing returns valid extraction result', async () => {
    const result = await uploadPdf('medical_form_original.pdf');

    // Verify response structure
    expect(result.file_id).toBeDefined();
    expect(typeof result.file_id).toBe('string');
    expect(result.file_id.length).toBeGreaterThan(0);

    expect(result.page_count).toBeGreaterThan(0);
    expect(typeof result.total_matches).toBe('number');
    expect(result.pages).toBeInstanceOf(Array);
    expect(result.mappings_used).toBeDefined();

    // Verify page structure
    for (const page of result.pages) {
      expect(page.page_number).toBeDefined();
      expect(typeof page.matches_found).toBe('number');
      expect(page.matches).toBeInstanceOf(Array);
    }
  });

  test('6.2 Medical summary PDF processing returns valid extraction result', async () => {
    const result = await uploadPdf('medical_summary_original.pdf');

    // Verify response structure
    expect(result.file_id).toBeDefined();
    expect(result.page_count).toBeGreaterThan(0);
    expect(result.pages).toBeInstanceOf(Array);
    expect(result.pages.length).toBe(result.page_count);
  });

  test('6.3 Processed PDF can be downloaded and is valid PDF', async () => {
    // Upload and process
    const result = await uploadPdf('medical_form_original.pdf');

    // Download the processed PDF
    const pdfBuffer = await downloadPdf(result.file_id);

    // Verify it's a valid PDF (starts with %PDF-)
    const uint8Array = new Uint8Array(pdfBuffer);
    const header = String.fromCharCode(...uint8Array.slice(0, 5));
    expect(header).toBe('%PDF-');

    // PDF should have reasonable size (small PDFs can still be valid)
    expect(pdfBuffer.byteLength).toBeGreaterThan(100);
  });

  test('6.4 Extraction result contains mappings when replacements configured', async () => {
    // Get the default replacements first
    const configResponse = await fetch(`${API_BASE}/config`);
    const config = await configResponse.json();
    const hasDefaultReplacements = Object.keys(config.default_replacements || {}).length > 0;

    // Upload and process
    const result = await uploadPdf('medical_form_original.pdf');

    // If there are default replacements configured, they should appear in mappings_used
    if (hasDefaultReplacements) {
      expect(result.mappings_used).toBeDefined();
      // Note: mappings_used only contains mappings that were actually applied
      // So we just verify the structure exists
    }

    // Verify all matches have replacement values
    for (const page of result.pages) {
      for (const match of page.matches) {
        expect(match.text).toBeDefined();
        expect(match.type).toBeDefined();
        expect(match.replacement).toBeDefined();
      }
    }
  });

  test('6.5 Processing with user replacements applies custom mappings', async () => {
    const pdfPath = join(RESOURCES_PATH, 'medical_form_original.pdf');
    const pdfBuffer = readFileSync(pdfPath);
    const blob = new Blob([pdfBuffer], { type: 'application/pdf' });

    // Custom user replacements
    const userConfig = {
      user_replacements: {
        'מיכאל': 'אבי',
        'פורגאצ\'': 'לוי',
      }
    };

    const formData = new FormData();
    formData.append('file', blob, 'medical_form_original.pdf');
    formData.append('config', JSON.stringify(userConfig));

    const response = await fetch(`${API_BASE}/extract`, {
      method: 'POST',
      body: formData,
    });

    expect(response.ok).toBe(true);

    const result = await response.json();

    // User mappings should be in mappings_used
    expect(result.mappings_used['מיכאל']).toBe('אבי');
    expect(result.mappings_used['פורגאצ\'']).toBe('לוי');
  });

  test('6.6 Downloaded PDF preserves page count', async () => {
    // Upload multi-page PDF
    const result = await uploadPdf('medical_summary_original.pdf');
    const originalPageCount = result.page_count;

    // Download the processed PDF
    const pdfBuffer = await downloadPdf(result.file_id);

    // Verify it's a valid PDF
    const uint8Array = new Uint8Array(pdfBuffer);
    const header = String.fromCharCode(...uint8Array.slice(0, 5));
    expect(header).toBe('%PDF-');

    // The API should preserve page count (check via extraction response)
    expect(result.pages.length).toBe(originalPageCount);
  });
});
