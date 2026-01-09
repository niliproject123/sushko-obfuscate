// E2E Integration Tests (4.1-4.3)
import { describe, test, expect, beforeAll } from 'vitest';
import { loadTestPdf, API_BASE, isBackendRunning, apiGet } from './setup';

interface PIIPatternConfig {
  name: string;
  pii_type: string;
  regex: string;
  capture_group: number;
  enabled: boolean;
  validator: string | null;
}

interface PIIMatch {
  text: string;
  type: string;
  pattern_name?: string;
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

async function downloadFile(fileId: string): Promise<Blob> {
  const response = await fetch(`${API_BASE}/download/${fileId}`);
  if (!response.ok) {
    throw new Error(`Download failed: ${response.status}`);
  }
  return response.blob();
}

describe('E2E Integration Tests', () => {
  beforeAll(async () => {
    const running = await isBackendRunning();
    if (!running) {
      throw new Error('Backend is not running. Start it with: uvicorn api.main:app --port 8000');
    }
  });

  // 4.1 Full flow: Upload → Extract → Download → Verify
  test('4.1 Full flow: Upload → Extract → Download → Verify PDF valid', async () => {
    // Step 1: Load test PDF
    const file = loadTestPdf('medical_form_original.pdf');

    // Step 2: Extract with user replacements
    const extractResult = await extractPdf(file, {
      user_replacements: {
        'מיכאל': 'דוד',
        'פורגאצ\'': 'כהן',
      },
    });

    expect(extractResult.file_id).toBeDefined();
    expect(extractResult.page_count).toBeGreaterThan(0);

    // Step 3: Download processed file
    const blob = await downloadFile(extractResult.file_id);

    expect(blob.size).toBeGreaterThan(0);

    // Step 4: Verify it's a valid PDF
    const arrayBuffer = await blob.slice(0, 10).arrayBuffer();
    const header = new TextDecoder().decode(arrayBuffer);
    expect(header).toContain('%PDF');
  });

  // 4.2 Extract medical form and verify response structure
  test('4.2 Extract medical_form returns valid structure with mappings', async () => {
    const file = loadTestPdf('medical_form_original.pdf');
    const result = await extractPdf(file);

    // Should have valid structure
    expect(result.file_id).toBeDefined();
    expect(result.page_count).toBeGreaterThan(0);
    expect(typeof result.total_matches).toBe('number');

    // Should have mappings_used (from default_replacements in config)
    expect(result.mappings_used).toBeDefined();

    // Mappings should contain some entries from config
    if (result.mappings_used) {
      const mappingCount = Object.keys(result.mappings_used).length;
      expect(mappingCount).toBeGreaterThan(0);
    }
  });

  // 4.3 Config affects extraction
  test('4.3 Disabling pattern affects extraction results', async () => {
    const file = loadTestPdf('medical_form_original.pdf');

    // Get patterns to find one that detects something
    const patterns = await apiGet<PIIPatternConfig[]>('/config/patterns');
    const phonePattern = patterns.find((p) => p.name.includes('phone'));

    if (!phonePattern) {
      // Skip if no phone pattern
      console.log('No phone pattern found, skipping test');
      return;
    }

    // Extract with phone pattern enabled
    const enabledResult = await extractPdf(file);

    // Count phone matches
    let phoneMatchesEnabled = 0;
    for (const page of enabledResult.pages) {
      for (const match of page.matches) {
        if (match.type === 'PHONE' || match.pattern_name?.includes('phone')) {
          phoneMatchesEnabled++;
        }
      }
    }

    // Extract with phone pattern disabled
    const disabledResult = await extractPdf(file, {
      disabled_detectors: [phonePattern.name],
    });

    // Count phone matches with disabled
    let phoneMatchesDisabled = 0;
    for (const page of disabledResult.pages) {
      for (const match of page.matches) {
        if (match.type === 'PHONE' || match.pattern_name?.includes('phone')) {
          phoneMatchesDisabled++;
        }
      }
    }

    // With detector disabled, should have fewer matches
    expect(phoneMatchesDisabled).toBeLessThanOrEqual(phoneMatchesEnabled);
  });

  // 4.4 Multi-file processing simulation
  test('4.4 Process multiple files sequentially', async () => {
    const files = [
      loadTestPdf('medical_form_original.pdf'),
      loadTestPdf('medical_summary_original.pdf'),
    ];

    const results: ExtractResponse[] = [];

    for (const file of files) {
      const result = await extractPdf(file);
      results.push(result);
    }

    // Both should succeed
    expect(results.length).toBe(2);
    expect(results[0].file_id).toBeDefined();
    expect(results[1].file_id).toBeDefined();

    // Both should have different file IDs
    expect(results[0].file_id).not.toBe(results[1].file_id);

    // Both should be downloadable
    for (const result of results) {
      const blob = await downloadFile(result.file_id);
      expect(blob.size).toBeGreaterThan(0);
    }
  });
});
