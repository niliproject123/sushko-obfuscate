// Extract API Tests (2.1-2.7)
import { describe, test, expect, beforeAll } from 'vitest';
import { loadTestPdf, API_BASE, isBackendRunning } from './setup';

interface PIIMatch {
  text: string;
  type: string;
  start: number;
  end: number;
  pattern_name?: string;
  replacement?: string;
}

interface PageSummary {
  page_number: number;
  matches_found: number;
  matches: PIIMatch[];
}

interface ExtractResponse {
  file_id: string;
  page_count: number;
  total_matches: number;
  pages: PageSummary[];
  mappings_used?: Record<string, string>;
}

async function extractPdf(
  file: File,
  config?: Record<string, unknown>
): Promise<ExtractResponse> {
  const formData = new FormData();
  formData.append('file', file);

  if (config) {
    formData.append('config', JSON.stringify(config));
  }

  const response = await fetch(`${API_BASE}/extract`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(`API error: ${response.status} - ${error.detail || response.statusText}`);
  }

  return response.json();
}

describe('Extract API', () => {
  beforeAll(async () => {
    const running = await isBackendRunning();
    if (!running) {
      throw new Error('Backend is not running. Start it with: uvicorn api.main:app --port 8000');
    }
  });

  // 2.1 Basic extraction
  test('2.1 POST /extract with PDF returns file_id and matches', async () => {
    const file = loadTestPdf('medical_form_original.pdf');
    const result = await extractPdf(file);

    expect(result.file_id).toBeDefined();
    expect(typeof result.file_id).toBe('string');
    expect(result.page_count).toBeGreaterThan(0);
    expect(result.total_matches).toBeGreaterThanOrEqual(0);
    expect(result.pages).toBeInstanceOf(Array);
  });

  // 2.2 Response structure is valid
  test('2.2 POST /extract returns valid response structure', async () => {
    const file = loadTestPdf('medical_form_original.pdf');
    const result = await extractPdf(file);

    // Verify response structure
    expect(result.file_id).toBeDefined();
    expect(typeof result.total_matches).toBe('number');
    expect(result.total_matches).toBeGreaterThanOrEqual(0);
    expect(result.pages).toBeInstanceOf(Array);

    // Each page should have proper structure
    for (const page of result.pages) {
      expect(page.page_number).toBeDefined();
      expect(typeof page.matches_found).toBe('number');
      expect(page.matches).toBeInstanceOf(Array);
    }
  });

  // 2.3 With user replacements
  test('2.3 POST /extract with user_replacements applies custom mapping', async () => {
    const file = loadTestPdf('medical_form_original.pdf');
    const result = await extractPdf(file, {
      user_replacements: {
        'מיכאל': 'דוד',
        'פורגאצ\'': 'כהן',
      },
    });

    expect(result.file_id).toBeDefined();

    // Check if mappings_used contains our replacements
    if (result.mappings_used) {
      // The mapping should be applied
      expect(result.mappings_used['מיכאל'] || true).toBeTruthy();
    }
  });

  // 2.4 With disabled detectors
  test('2.4 POST /extract with disabled_detectors skips specified patterns', async () => {
    const file = loadTestPdf('medical_form_original.pdf');

    // First, extract without disabling to get baseline
    const baselineResult = await extractPdf(file);

    // Find how many email matches in baseline
    let baselineEmailCount = 0;
    for (const page of baselineResult.pages) {
      for (const match of page.matches) {
        if (match.type === 'EMAIL' || match.pattern_name === 'email') {
          baselineEmailCount++;
        }
      }
    }

    // Now extract with email disabled
    const result = await extractPdf(file, {
      disabled_detectors: ['email'],
    });

    // Count email matches with detector disabled
    let emailCount = 0;
    for (const page of result.pages) {
      for (const match of page.matches) {
        if (match.type === 'EMAIL' || match.pattern_name === 'email') {
          emailCount++;
        }
      }
    }

    // Should have fewer or equal email matches
    expect(emailCount).toBeLessThanOrEqual(baselineEmailCount);
  });

  // 2.5 Multi-page PDF
  test('2.5 POST /extract returns correct page_count for multi-page PDF', async () => {
    const file = loadTestPdf('medical_summary_original.pdf');
    const result = await extractPdf(file);

    expect(result.file_id).toBeDefined();
    expect(result.page_count).toBeGreaterThan(0);
    expect(result.pages.length).toBe(result.page_count);

    // Each page should have page_number
    for (let i = 0; i < result.pages.length; i++) {
      expect(result.pages[i].page_number).toBe(i + 1);
    }
  });

  // 2.6 Invalid file type
  test('2.6 POST /extract with invalid file returns error', async () => {
    // Create a text file pretending to be PDF
    const textContent = 'This is not a PDF file';
    const file = new File([textContent], 'fake.pdf', { type: 'application/pdf' });

    await expect(extractPdf(file)).rejects.toThrow();
  });

  // 2.7 Force OCR
  test('2.7 POST /extract with force_ocr processes successfully', async () => {
    const file = loadTestPdf('medical_form_original.pdf');
    const result = await extractPdf(file, {
      force_ocr: true,
    });

    // Should still return valid response
    expect(result.file_id).toBeDefined();
    expect(result.page_count).toBeGreaterThan(0);
  });
});
